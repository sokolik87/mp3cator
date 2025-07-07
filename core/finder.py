import os
from .utils import get_mp3_path

class FileFinder:
    """
    Finds files within a directory and its subdirectories.
    """
    def __init__(self, root_path: str):
        """
        Initializes the finder with a root path.

        Args:
            root_path (str): The absolute path to the root directory to search.

        Raises:
            ValueError: If the provided path is not a valid directory.
        """
        if not os.path.isdir(root_path):
            raise ValueError(f"Provided path '{root_path}' is not a valid directory.")
        self.root_path = root_path

    def find_files(self, extension: str) -> list[str]:
        """
        Finds files with the specified extension.

        Args:
            extension (str): The file extension to search for (e.g., "ogg", "mp3").

        Returns:
            list[str]: A list of absolute paths to the found files.
        """
        found_files = []
        normalized_ext = f".{extension.lower().lstrip('.')}"
        # The print statement was removed to avoid duplicate messages, as the
        # main script and post-check now handle their own user-facing messages.
        for dirpath, _, filenames in os.walk(self.root_path):
            for filename in filenames:
                if filename.lower().endswith(normalized_ext):
                    full_path = os.path.join(dirpath, filename)
                    found_files.append(full_path)
        return found_files

    def identify_files_for_conversion(self, source_ext: str, target_ext: str, restructure: bool = False, output_dir: str = None) -> tuple[list[str], int, int]:
        """
        Identifies source files that need conversion by checking for target files.

        This makes the script idempotent by skipping files that have already
        been converted.

        Args:
            source_ext (str): The source file extension (e.g., "ogg").
            target_ext (str): The target file extension (e.g., "mp3").
            restructure (bool): If True, checks for restructured output paths.
            output_dir (str, optional): Custom output directory. Overrides restructure logic.

        Returns:
            tuple[list[str], int, int]: A tuple containing:
                - A list of source file paths that need conversion.
                - The total number of source files found.
                - The number of source files that were skipped.
        """
        source_files = self.find_files(source_ext)

        if not restructure and not output_dir:
            # Original logic for in-place conversion
            target_files = self.find_files(target_ext)
            target_basenames = {os.path.splitext(os.path.basename(f))[0] for f in target_files}
            files_to_convert = [
                f for f in source_files if os.path.splitext(os.path.basename(f))[0] not in target_basenames
            ]
        else:
            # New logic for restructured output or custom output directory
            files_to_convert = []
            for ogg_file in source_files:
                expected_mp3_path = get_mp3_path(ogg_file, self.root_path, restructure, output_dir)
                if not os.path.exists(expected_mp3_path):
                    files_to_convert.append(ogg_file)


        total_source_count = len(source_files)
        skipped_count = total_source_count - len(files_to_convert)

        return files_to_convert, total_source_count, skipped_count
