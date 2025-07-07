import os
import re

def to_camel_case(text: str) -> str:
    """
    Converts a string to lower camelCase, removing special characters.
    Example: "01 - My Awesome Song" -> "01MyAwesomeSong"
    """
    # Replace non-alphanumeric characters with a space, then split.
    s = re.sub(r'[^a-zA-Z0-9]+', ' ', text).strip()
    if not s:
        return ""
    words = s.split(' ')
    # Make the first word/part lowercase and all subsequent parts capitalized.
    return words[0].lower() + ''.join(x.capitalize() for x in words[1:])

def get_mp3_path(ogg_path: str, root_path: str, restructure: bool, output_dir: str = None) -> str:
    """
    Calculates the target MP3 path for a given OGG path.

    Args:
        ogg_path (str): The absolute path to the .ogg file.
        root_path (str): The root path of the scan.
        restructure (bool): If True, builds a camelCased path structure.
        output_dir (str, optional): Custom output directory. If provided, 
                                   overrides restructure logic.

    Returns:
        str: The target MP3 file path.
    """
    # Priority 1: Custom output directory (overrides everything)
    if output_dir:
        return _get_custom_output_path(ogg_path, root_path, output_dir)
    
    # Priority 2: In-place conversion (no restructuring)
    if not restructure:
        return os.path.splitext(ogg_path)[0] + '.mp3'

    # Priority 3: Restructuring Logic
    return _get_restructured_path(ogg_path, root_path)

def _get_custom_output_path(ogg_path: str, root_path: str, output_dir: str) -> str:
    """
    Generates a path for custom output directory.
    Preserves the relative directory structure from the source.
    """
    # Get relative path from root to maintain directory structure
    relative_path = os.path.relpath(ogg_path, root_path)
    
    # Split into directory components and filename
    path_components = relative_path.split(os.sep)
    
    # Keep directory structure but change extension to .mp3
    original_basename = os.path.splitext(path_components[-1])[0]
    new_filename = f"{original_basename}.mp3"
    
    # Build the new path under the custom output directory
    final_path = os.path.join(output_dir, *path_components[:-1], new_filename)
    return final_path

def _get_restructured_path(ogg_path: str, root_path: str) -> str:
    """
    Generates a restructured path with camelCase components.
    """
    relative_path = os.path.relpath(ogg_path, root_path)
    path_components = relative_path.split(os.sep)

    # CamelCase directory parts
    camel_cased_dirs = [to_camel_case(part) for part in path_components[:-1]]

    # Handle filename
    original_basename = os.path.splitext(path_components[-1])[0]
    camel_cased_basename = to_camel_case(original_basename)
    new_filename = f"{camel_cased_basename}.mp3"

    # Join everything together under the 'RS' subfolder
    new_base = os.path.join(root_path, "RS")
    final_path = os.path.join(new_base, *camel_cased_dirs, new_filename)
    return final_path
