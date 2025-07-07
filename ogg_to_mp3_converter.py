import argparse
import sys
import concurrent.futures
import os
from tqdm import tqdm
import shutil
import logging
from typing import Optional, Tuple, List, Dict, Any, Generator
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
import re
import time
import json
import atexit
import signal

from core.finder import FileFinder
from core.converter import OggToMp3Converter
from core.postcheck import PostCheck
from core.constants import DEFAULT_BITRATE, DEFAULT_THREADS, SUPPORTED_AUDIO_FORMATS, RESTRUCTURE_FOLDER_NAME, SUPPORTED_EXTENSIONS, CAMEL_CASE_PATTERN

# Configure logging with different levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_terminal():
    """
    Cleanup function to restore terminal state.
    This ensures the cursor is visible and input echo is enabled.
    """
    try:
        # Force tqdm to cleanup any remaining progress bars
        if hasattr(tqdm, '_instances'):
            tqdm._instances.clear()
        
        # Close any open tqdm instances
        try:
            for instance in tqdm._instances.copy():
                instance.close()
        except Exception:
            pass
        
        # Restore cursor visibility and input echo
        sys.stdout.write('\033[?25h')  # Show cursor
        sys.stdout.write('\033[0m')    # Reset all attributes
        sys.stdout.write('\n')         # Add newline for clean prompt
        sys.stdout.flush()
        
        # Enable input echo (stty echo) - only on Unix-like systems
        if hasattr(os, 'system') and os.name != 'nt':
            os.system('stty echo 2>/dev/null')
    except Exception:
        # Ignore any errors during cleanup
        pass

def setup_terminal_cleanup():
    """Register terminal cleanup function to run on exit."""
    atexit.register(cleanup_terminal)
    
    # Also register signal handlers for graceful cleanup
    def signal_handler(signum, frame):
        cleanup_terminal()
        sys.exit(128 + signum)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

@dataclass
class ConversionConfig:
    bitrate: str = "320k"
    threads: Optional[int] = None
    quiet: bool = False
    restructure: bool = False
    post_check: bool = False
    delete_originals: bool = False

class ProgressTracker:
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.start_time = time.time()
    
    def update(self, success: bool):
        self.processed += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
    
    def get_stats(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'elapsed_time': elapsed,
            'files_per_second': self.processed / elapsed if elapsed > 0 else 0
        }

def main():
    """Main function to run the script."""
    # Setup terminal cleanup to ensure proper restoration on exit
    setup_terminal_cleanup()
    
    parser = argparse.ArgumentParser(
        description="Recursively finds and converts OGG files to MP3, preserving tags."
    )
    parser.add_argument("folder_path", type=str, help="The absolute path to the folder to scan.")
    parser.add_argument(
        "--bitrate",
        type=str,
        default="320k",
        help="The bitrate for the output MP3 file (e.g., '192k', '256k', '320k'). Default: 320k"
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Number of threads for conversion. Defaults to the system's optimal number."
    )
    parser.add_argument(
        """--post-check""",
        action="store_true",
        help="After conversion, check for any .ogg files that were not converted."
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="After a successful post-check, delete the original .ogg files. Requires --post-check."
    )
    parser.add_argument(
        "--restructure",
        action="store_true",
        help="Restructures output into a 'RS' subfolder with camelCase paths."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without actually converting"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Specify custom output directory. Preserves the original directory structure from source. Overrides --restructure if both are specified."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    args = parser.parse_args()

    # Ensure --delete is only used with --post-check for safety
    if args.delete and not args.post_check:
        parser.error("--delete can only be used when --post-check is also specified.")
    
    # Validate and prepare output directory if specified
    if args.output_dir:
        # Make output directory path absolute
        args.output_dir = os.path.abspath(args.output_dir)
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(args.output_dir, exist_ok=True)
        except OSError as e:
            parser.error(f"Cannot create output directory '{args.output_dir}': {e}")
        
        # Check if output directory is writable
        if not os.access(args.output_dir, os.W_OK):
            parser.error(f"Output directory '{args.output_dir}' is not writable.")
        
        print(f"Using custom output directory: {args.output_dir}")
        
        # If output_dir is specified, it overrides restructure
        if args.restructure:
            print("Note: --output-dir overrides --restructure flag.")

    # --- Pre-flight check for dependencies ---
    # This is done early to fail fast before any processing begins.
    # This also prevents worker threads from calling sys.exit(), which can
    # corrupt the terminal state by not allowing tqdm to clean up.
    missing_dependencies = check_dependencies()
    if missing_dependencies:
        print(f"Error: Required dependencies not found in your system's PATH: {', '.join(missing_dependencies)}", file=sys.stderr)
        print("Please install these dependencies to proceed.", file=sys.stderr)
        sys.exit(1)

    try:
        # Use the new, more generic FileFinder
        print(f"Scanning '{args.folder_path}' for .ogg files...")
        finder = FileFinder(args.folder_path)
        ogg_files_to_convert, total_ogg_count, skipped_count = finder.identify_files_for_conversion("ogg", "mp3", restructure=args.restructure, output_dir=args.output_dir)

        if total_ogg_count == 0:
            print(f"No .ogg files found in '{args.folder_path}' or its subdirectories.")
            return

        if skipped_count > 0:
            print(f"Found {total_ogg_count} total .ogg file(s). Skipping {skipped_count} because a corresponding .mp3 already exists.")

        if not ogg_files_to_convert:
            print("No new .ogg files to convert.")
            # Still run post-check if requested, as it might be for cleanup.
            if args.post_check:
                print("Proceeding to post-check as requested...")
                PostCheck.perform_post_check(args.folder_path, delete_originals=args.delete, restructure=args.restructure, output_dir=args.output_dir)
            return

        # Determine the number of threads to report to the user for clarity.
        if args.threads:
            thread_count_msg = f"up to {args.threads} threads"
        else:
            # os.cpu_count() can be None, so we provide a fallback of 1.
            cores = os.cpu_count() or 1
            thread_count_msg = f"the default number of threads (optimized for {cores} cores)"

        print(f"\nReady to convert {len(ogg_files_to_convert)} file(s). Starting parallel conversion using {thread_count_msg}...\n")

        def convert_file(ogg_path: str) -> bool:
            """
            A small helper function to be called by each thread.
            It instantiates and runs the converter for a single file.
            """
            # Note: We suppress the individual print statements from the converter
            # to avoid cluttering the console with progress bar.
            converter = OggToMp3Converter(
                ogg_path,
                root_path=args.folder_path,
                bitrate=args.bitrate,
                quiet=True,
                restructure=args.restructure,
                verbose=args.verbose,
                output_dir=args.output_dir
            )
            return converter.convert()

        # --- Refactored conversion loop for robust interruption handling ---
        # This pattern ensures that tqdm's context manager cleans up the terminal
        # state correctly, even when the user interrupts with Ctrl+C.
        results = []
        with tqdm(total=len(ogg_files_to_convert), desc="Converting", unit="file", 
                 leave=True, ncols=80, ascii=True) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                # Create a future for each file conversion
                future_to_ogg = {executor.submit(convert_file, ogg): ogg for ogg in ogg_files_to_convert}

                for future in concurrent.futures.as_completed(future_to_ogg):
                    try:
                        # Get the result of the conversion (True/False)
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        # In case a conversion task itself raises an unexpected error
                        ogg_path = future_to_ogg[future]
                        pbar.write(f"Error processing {os.path.basename(ogg_path)}: {exc}", file=sys.stderr)
                    finally:
                        # Update the progress bar for every completed file
                        pbar.update(1)

        converted_count = sum(results)

        print(f"\nConversion complete. {converted_count}/{len(ogg_files_to_convert)} files converted successfully.")

        # Perform the post-conversion check if the flag was passed
        if args.post_check:
            PostCheck.perform_post_check(args.folder_path, delete_originals=args.delete, restructure=args.restructure, output_dir=args.output_dir)

    except (ValueError, FileNotFoundError) as e:
        cleanup_terminal()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        # Ensure immediate cleanup before any output
        cleanup_terminal()
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)  # Standard exit code for Ctrl+C
    except PermissionError as e:
        cleanup_terminal()
        print(f"Permission denied: {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        cleanup_terminal()
        print(f"System error: {e}", file=sys.stderr)
        sys.exit(1)

def validate_bitrate(bitrate: str) -> bool:
    """Validate bitrate format"""
    return bool(re.match(r'^\d+k$', bitrate))

def validate_folder_path(path: str) -> bool:
    """Validate folder path exists and is readable"""
    return os.path.exists(path) and os.access(path, os.R_OK)

def find_files_generator(self, extension: str) -> Generator[str, None, None]:
    """Generator version for memory efficiency with large directories"""
    normalized_ext = f".{extension.lower().lstrip('.')}"
    for dirpath, _, filenames in os.walk(self.root_path):
        for filename in filenames:
            if filename.lower().endswith(normalized_ext):
                yield os.path.join(dirpath, filename)

def to_camel_case(text: str) -> str:
    """
    Converts a string to lower camelCase, removing special characters.
    
    Args:
        text: The input string to convert
        
    Returns:
        The camelCase version of the input string
        
    Examples:
        >>> to_camel_case("01 - My Awesome Song")
        "01MyAwesomeSong"
        >>> to_camel_case("hello world")
        "helloWorld"
    """

# Add test utilities
class TestableConverter(OggToMp3Converter):
    """Version of converter that can be mocked for testing"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dry_run = kwargs.get('dry_run', False)
    
    def convert(self) -> bool:
        if self.dry_run:
            return True  # Simulate successful conversion
        return super().convert()

def check_dependencies() -> List[str]:
    """Check for required dependencies and return missing ones"""
    missing = []
    dependencies = ["ffmpeg", "ffprobe"]
    
    for dep in dependencies:
        if not shutil.which(dep):
            missing.append(dep)
    
    return missing

# Support for configuration files
def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from file if available"""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    main()
