"""
Constants used throughout the mp3cator application.
"""

# Default conversion settings
DEFAULT_BITRATE = "320k"
DEFAULT_THREADS = None

# File formats
SUPPORTED_AUDIO_FORMATS = ["ogg", "mp3"]
SUPPORTED_EXTENSIONS = [".ogg", ".mp3"]
SOURCE_EXTENSION = "ogg"
TARGET_EXTENSION = "mp3"

# Restructuring settings
RESTRUCTURE_FOLDER_NAME = "RS"

# Regex patterns
CAMEL_CASE_PATTERN = r'[^a-zA-Z0-9]+'

# FFmpeg parameters
FFMPEG_CBR_PARAMS = ["-minrate", "-maxrate"]

# Error messages
ERROR_FFMPEG_NOT_FOUND = "Error: Required dependency 'ffmpeg' not found in your system's PATH."
ERROR_FFMPEG_INSTALL = "Please install ffmpeg to proceed."
ERROR_INVALID_DIRECTORY = "Provided path '{path}' is not a valid directory."
ERROR_COULD_NOT_DECODE = "Could not decode '{filename}'. The file may be corrupt or you may be missing 'vorbis-tools'."
ERROR_CONVERSION_FAILED = "Error converting '{filename}': {error}"
ERROR_METADATA_READ = "Warning: Could not read metadata for {filename}. Reason: {error}"
ERROR_DELETE_REQUIRES_POSTCHECK = "--delete can only be used when --post-check is also specified."

# Success messages
SUCCESS_CONVERSION = "Successfully saved to '{filename}'"
SUCCESS_ALL_CONVERTED = "Success! All .ogg files appear to have a corresponding .mp3 file."
SUCCESS_DELETED_FILES = "Successfully deleted {count}/{total} .ogg files."

# Progress messages
MSG_SCANNING = "Scanning '{path}' for .ogg files..."
MSG_CONVERTING = "Converting '{filename}'..."
MSG_READY_TO_CONVERT = "Ready to convert {count} file(s). Starting parallel conversion using {threads}..."
MSG_CONVERSION_COMPLETE = "Conversion complete. {successful}/{total} files converted successfully."
MSG_POST_CHECK_HEADER = "--- Post-Conversion Check ---"
MSG_POST_CHECK_FOOTER = "--- End of Check ---"
MSG_OPERATION_CANCELLED = "Operation cancelled by user."

# File count messages
MSG_NO_OGG_FILES = "No .ogg files found in '{path}' or its subdirectories."
MSG_NO_NEW_FILES = "No new .ogg files to convert."
MSG_FILES_FOUND = "Found {total} total .ogg file(s). Skipping {skipped} because a corresponding .mp3 already exists."
MSG_FILES_STATUS = "Found {ogg_count} total .ogg file(s) and {mp3_count} total .mp3 file(s)."

# Warning messages
WARNING_UNCONVERTED_FILES = "Warning: Found {count} .ogg file(s) without a corresponding .mp3:"
WARNING_SKIPPING_DELETION = "Skipping deletion because some files were not converted."
