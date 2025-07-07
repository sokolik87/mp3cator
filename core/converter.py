import os
import sys
import subprocess
import json
from pydub import AudioSegment, exceptions
from pydub.utils import mediainfo_json

from .utils import get_mp3_path

class OggToMp3Converter:
    """
    Converts a single .ogg file to .mp3 format, preserving metadata tags.
    """
    def __init__(self, ogg_path: str, root_path: str, bitrate: str = "320k", quiet: bool = False, restructure: bool = False, verbose: bool = False, output_dir: str = None):
        """
        Initializes the converter with the path to an .ogg file.

        Args:
            ogg_path (str): The absolute path to the .ogg file.
            root_path (str): The root path of the scan, used for restructuring.
            bitrate (str): The target bitrate for the MP3 file (e.g., "192k", "320k").
            quiet (bool): If True, suppresses print statements for cleaner parallel output.
            restructure (bool): If True, the output path will be restructured.
            verbose (bool): If True, shows detailed tag information during conversion.
            output_dir (str, optional): Custom output directory. Overrides restructure logic.
        """
        self.ogg_path = ogg_path
        self.quiet = quiet
        self.bitrate = bitrate
        self.restructure = restructure
        self.verbose = verbose
        self.output_dir = output_dir
        self.mp3_path = get_mp3_path(ogg_path, root_path, restructure, output_dir)

    def _normalize_tags(self, raw_tags: dict) -> dict:
        """
        Normalize and map OGG tags to MP3-compatible tag format.
        
        Args:
            raw_tags (dict): Raw tags from mediainfo_json
            
        Returns:
            dict: Normalized tags suitable for MP3 export
        """
        if not raw_tags:
            return {}
            
        # OGG to MP3 tag mapping (case-insensitive)
        tag_mapping = {
            'title': 'title',
            'artist': 'artist',
            'album': 'album',
            'albumartist': 'albumartist',
            'date': 'date',
            'year': 'date',  # Map year to date
            'genre': 'genre',
            'track': 'track',
            'tracknumber': 'track',  # Common OGG variant
            'tracktotal': 'tracktotal',
            'disc': 'disc',
            'discnumber': 'disc',  # Common OGG variant
            'disctotal': 'disctotal',
            'composer': 'composer',
            'performer': 'performer',
            'comment': 'comment',
            'lyrics': 'lyrics',
            'copyright': 'copyright',
            'encoder': 'encoder',
            'encoded_by': 'encoded_by',
            'organization': 'organization',
            'albumart': 'albumart',
            'picture': 'albumart',  # Alternative for album art
        }
        
        normalized_tags = {}
        
        for key, value in raw_tags.items():
            # Convert to lowercase for mapping
            key_lower = key.lower()
            
            # Map the key if we have a mapping for it
            if key_lower in tag_mapping:
                mp3_key = tag_mapping[key_lower]
                
                # Special handling for certain tag types
                if mp3_key in ['track', 'disc']:
                    # Ensure track/disc numbers are properly formatted
                    normalized_tags[mp3_key] = self._format_track_number(str(value).strip())
                elif mp3_key == 'date':
                    # Ensure date is properly formatted
                    normalized_tags[mp3_key] = self._format_date(str(value).strip())
                else:
                    normalized_tags[mp3_key] = str(value).strip()
            else:
                # For unknown tags, keep them as-is but ensure they're strings
                normalized_tags[key.lower()] = str(value).strip()
        
        # Remove empty tags
        normalized_tags = {k: v for k, v in normalized_tags.items() if v}
        
        return normalized_tags
    
    def _format_track_number(self, track_str: str) -> str:
        """Format track number to ensure it's in the correct format."""
        if not track_str:
            return ""
        
        # Handle formats like "1/12" or "01/12" - keep as is
        if '/' in track_str:
            return track_str
        
        # Handle simple numbers - pad with zero if single digit
        try:
            track_num = int(track_str)
            return f"{track_num:02d}"
        except ValueError:
            # If it's not a number, return as-is
            return track_str
    
    def _format_date(self, date_str: str) -> str:
        """Format date to ensure it's in the correct format."""
        if not date_str:
            return ""
        
        # Keep full dates as-is, but extract year from full dates if needed
        if len(date_str) == 4 and date_str.isdigit():
            return date_str
        elif len(date_str) >= 4:
            # Extract year from full date format
            return date_str[:4]
        else:
            return date_str
    
    def _get_tags_with_ffprobe(self, file_path: str) -> dict:
        """
        Direct ffprobe call to extract tags as a fallback method.
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            dict: Raw tags from ffprobe
        """
        try:
            # Call ffprobe directly to get JSON output
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                '-show_format', '-show_streams', file_path
            ]
            
            if self.verbose:
                print(f"  -> Debug: Running ffprobe command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                if self.verbose:
                    print(f"  -> Debug: ffprobe failed with return code {result.returncode}")
                    print(f"  -> Debug: ffprobe stderr: {result.stderr}")
                return {}
            
            # Parse JSON output
            info = json.loads(result.stdout)
            
            if self.verbose:
                print(f"  -> Debug: ffprobe returned: {info}")
            
            # Extract tags from the format section
            raw_tags = {}
            
            # Method 1: Look in format.tags (standard ffprobe location)
            if 'format' in info and 'tags' in info['format']:
                raw_tags.update(info['format']['tags'])
                if self.verbose:
                    print(f"  -> Debug: Found tags in format.tags: {info['format']['tags']}")
            
            # Method 2: Look in streams[0].tags (alternative location)
            if 'streams' in info and len(info['streams']) > 0 and 'tags' in info['streams'][0]:
                raw_tags.update(info['streams'][0]['tags'])
                if self.verbose:
                    print(f"  -> Debug: Found tags in streams[0].tags: {info['streams'][0]['tags']}")
            
            return raw_tags
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            if self.verbose:
                print(f"  -> Debug: Direct ffprobe call failed: {e}")
            return {}

    def convert(self) -> bool:
        """
        Performs the conversion from .ogg to .mp3.

        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        try:
            # Ensure the destination directory exists for restructuring or custom output
            if self.restructure or self.output_dir:
                os.makedirs(os.path.dirname(self.mp3_path), exist_ok=True)

            if not self.quiet:
                print(f"Converting '{os.path.basename(self.ogg_path)}'...")

            # Explicitly read metadata using ffprobe, which is more reliable.
            # This bypasses potential issues with AudioSegment's automatic tag loading.
            raw_tags = {}
            export_tags = None
            
            # Try Method 1: Use pydub's mediainfo_json
            try:
                if self.verbose:
                    print(f"  -> Debug: Trying pydub's mediainfo_json...")
                
                info = mediainfo_json(self.ogg_path)
                
                # Debug: Show what mediainfo_json returns
                if self.verbose:
                    print(f"  -> Debug: mediainfo_json returned: {info}")
                
                # Try multiple locations for tags in the JSON structure
                raw_tags = {}
                
                # Method 1: Look in format.tags (standard ffprobe location)
                if 'format' in info and 'tags' in info['format']:
                    raw_tags.update(info['format']['tags'])
                    if self.verbose:
                        print(f"  -> Debug: Found tags in format.tags: {info['format']['tags']}")
                
                # Method 2: Look in streams[0].tags (alternative location)
                if 'streams' in info and len(info['streams']) > 0 and 'tags' in info['streams'][0]:
                    raw_tags.update(info['streams'][0]['tags'])
                    if self.verbose:
                        print(f"  -> Debug: Found tags in streams[0].tags: {info['streams'][0]['tags']}")
                
                # Method 3: Look for tags directly in the root (some formats)
                if 'tags' in info:
                    raw_tags.update(info['tags'])
                    if self.verbose:
                        print(f"  -> Debug: Found tags in root: {info['tags']}")
                
                if self.verbose:
                    print(f"  -> Debug: Combined raw_tags from mediainfo_json: {raw_tags}")
                
            except Exception as e:
                if self.verbose:
                    print(f"  -> Debug: mediainfo_json failed: {e}")
                raw_tags = {}
            
            # Try Method 2: Direct ffprobe call if mediainfo_json didn't work or found no tags
            if not raw_tags:
                if self.verbose:
                    print(f"  -> Debug: No tags found with mediainfo_json, trying direct ffprobe...")
                
                raw_tags = self._get_tags_with_ffprobe(self.ogg_path)
                
                if self.verbose:
                    print(f"  -> Debug: Combined raw_tags from direct ffprobe: {raw_tags}")
            
            # Process the tags if we found any
            if raw_tags:
                # Map OGG tag keys to MP3 tag keys and ensure proper formatting
                export_tags = self._normalize_tags(raw_tags)
                
                if export_tags:
                    # Show tag information (respect quiet mode except for verbose)
                    if not self.quiet or self.verbose:
                        print(f"  -> Found {len(export_tags)} tag(s) to preserve")
                        # Show tag details in verbose mode
                        if self.verbose:
                            for key, value in export_tags.items():
                                print(f"     {key}: {value}")
                else:
                    if self.verbose:
                        print(f"  -> No tags found in source file after processing")
            else:
                if self.verbose:
                    print(f"  -> No tags found in source file with any method")
                export_tags = None

            # pydub will raise an exception if ffmpeg/avconv is not found
            audio = AudioSegment.from_ogg(self.ogg_path)

            # Export using Constant Bit Rate (CBR) and the tags we just read.
            # Use different approaches based on whether we have tags to preserve
            if export_tags:
                try:
                    # First try with normalized tags
                    audio.export(
                        self.mp3_path, format="mp3", bitrate=self.bitrate,
                        parameters=["-minrate", self.bitrate, "-maxrate", self.bitrate],
                        tags=export_tags)
                except Exception as tag_error:
                    if not self.quiet or self.verbose:
                        print(f"  -> Warning: Failed to export with tags ({tag_error}), trying without tags", file=sys.stderr)
                    # Fallback: export without tags
                    audio.export(
                        self.mp3_path, format="mp3", bitrate=self.bitrate,
                        parameters=["-minrate", self.bitrate, "-maxrate", self.bitrate])
            else:
                # No tags to preserve, export normally
                audio.export(
                    self.mp3_path, format="mp3", bitrate=self.bitrate,
                    parameters=["-minrate", self.bitrate, "-maxrate", self.bitrate])
            if not self.quiet:
                print(f"  -> Successfully saved to '{os.path.basename(self.mp3_path)}'")
            return True
        except exceptions.CouldntDecodeError:
            print(f"  -> ERROR: Could not decode '{os.path.basename(self.ogg_path)}'. The file may be corrupt or you may be missing 'vorbis-tools'.", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  -> Error converting '{os.path.basename(self.ogg_path)}': {e}", file=sys.stderr)
            return False
    