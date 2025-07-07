import os
from .finder import FileFinder
from .utils import get_mp3_path


class PostCheck:
    """
    A utility class to perform post-conversion checks and cleanup.
    """
    @staticmethod
    def perform_post_check(root_path: str, delete_originals: bool = False, restructure: bool = False, output_dir: str = None):
        """
        Scans the directory for .ogg and .mp3 files and reports any .ogg files
        that do not have a corresponding .mp3 file.

        Optionally deletes original .ogg files if all have been converted.

        Args:
            root_path (str): The root directory to check.
            delete_originals (bool): If True and all files were converted,
                                     deletes the original .ogg files.
            restructure (bool): If True, checks for restructured output paths.
            output_dir (str, optional): Custom output directory. Overrides restructure logic.
        """
        print("\n--- Post-Conversion Check ---")
        # Note: We create a new finder to get a fresh look at the directory state.
        finder = FileFinder(root_path)

        # Find all ogg and mp3 files again
        ogg_files = finder.find_files("ogg")
        mp3_files = finder.find_files("mp3")

        print(f"Found {len(ogg_files)} total .ogg file(s) and {len(mp3_files)} total .mp3 file(s).")

        # Create a set of mp3 basenames (filename without extension) for efficient lookup
        if not restructure and not output_dir:
            mp3_basenames = {os.path.splitext(os.path.basename(f))[0] for f in mp3_files}

        unconverted_files = []
        for ogg_file in ogg_files:
            if restructure or output_dir:
                expected_mp3_path = get_mp3_path(ogg_file, root_path, restructure, output_dir)
                if not os.path.exists(expected_mp3_path):
                    unconverted_files.append(ogg_file)
            else:
                ogg_basename = os.path.splitext(os.path.basename(ogg_file))[0]
                if ogg_basename not in mp3_basenames:
                    unconverted_files.append(ogg_file)

        if not unconverted_files:
            print("\nSuccess! All .ogg files appear to have a corresponding .mp3 file.")
            if delete_originals and ogg_files:
                print(f"Deleting {len(ogg_files)} original .ogg file(s)...")
                deleted_count = 0
                for ogg_file in ogg_files:
                    try:
                        os.remove(ogg_file)
                        deleted_count += 1
                    except OSError as e:
                        print(f"  -> Error deleting {os.path.basename(ogg_file)}: {e}")
                print(f"Successfully deleted {deleted_count}/{len(ogg_files)} .ogg files.")
            elif delete_originals:
                print("No .ogg files found to delete.")
        else:
            print(f"\nWarning: Found {len(unconverted_files)} .ogg file(s) without a corresponding .mp3:")
            for f in unconverted_files:
                print(f"  - {os.path.relpath(f, root_path)}")
            if delete_originals:
                print("\nSkipping deletion because some files were not converted.")
        print("--- End of Check ---")
