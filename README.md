# 🎵 MP3cator - OGG to MP3 Converter

A fast, parallel OGG to MP3 converter that preserves metadata tags and offers flexible output options.

## 🚀 TLDR - Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic conversion (in-place)
python ogg_to_mp3_converter.py /path/to/music

# Convert with restructured output (camelCase paths in RS folder)
python ogg_to_mp3_converter.py /path/to/music --restructure

# Convert to custom directory
python ogg_to_mp3_converter.py /path/to/music --output-dir /backup/mp3s

# Convert with post-check and cleanup
python ogg_to_mp3_converter.py /path/to/music --post-check --delete
```

**Requirements:** Python 3.7+, ffmpeg, ffprobe

---

## ✨ Features

- 🚄 **Parallel Processing** - Multi-threaded conversion for speed
- 🏷️ **Tag Preservation** - Maintains all metadata (artist, title, album, etc.)
- 📁 **Flexible Output** - In-place, restructured, or custom directory
- 🔍 **Smart Skipping** - Idempotent (skips already converted files)
- ✅ **Post-Check** - Verification and optional cleanup
- 🐛 **Verbose Mode** - Detailed debugging information
- 🖥️ **Terminal-Friendly** - Proper progress bars and cleanup

## 📦 Installation

### Prerequisites

1. **Python 3.7+**
2. **FFmpeg** (with ffprobe)
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS (with Homebrew)
   brew install ffmpeg
   
   # Windows (with Chocolatey)
   choco install ffmpeg
   ```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Basic Syntax

```bash
python ogg_to_mp3_converter.py <folder_path> [options]
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `folder_path` | **Required.** Path to folder containing OGG files |
| `--bitrate` | MP3 bitrate (default: 320k) |
| `--threads` | Number of conversion threads (default: auto) |
| `--restructure` | Output to camelCase structure in RS/ folder |
| `--output-dir` | Custom output directory (overrides --restructure) |
| `--post-check` | Verify conversions after completion |
| `--delete` | Delete original OGG files (requires --post-check) |
| `--verbose` | Show detailed conversion information |
| `--dry-run` | Show what would be converted without converting |

## 📋 Examples

### 1. Basic In-Place Conversion
Converts OGG files to MP3 in the same directory:
```bash
python ogg_to_mp3_converter.py "/music/My Collection"
```
**Result:**
```
Music/My Collection/Artist/Album/Song.ogg → Song.mp3
```

### 2. Restructured Output
Creates camelCase directory structure in RS/ subfolder:
```bash
python ogg_to_mp3_converter.py "/music/My Collection" --restructure
```
**Result:**
```
Music/My Collection/Artist Name/Album Name/01 - Song Title.ogg
→ Music/My Collection/RS/artistName/albumName/01SongTitle.mp3
```

### 3. Custom Output Directory
Preserves original structure in custom location:
```bash
python ogg_to_mp3_converter.py "/music/My Collection" --output-dir "/backup/mp3s"
```
**Result:**
```
Music/My Collection/Artist/Album/Song.ogg
→ /backup/mp3s/Artist/Album/Song.mp3
```

### 4. Full Conversion with Cleanup
Convert, verify, and remove originals:
```bash
python ogg_to_mp3_converter.py "/music/My Collection" \
  --bitrate 256k \
  --post-check \
  --delete \
  --verbose
```

### 5. Performance Tuning
Control threading and quality:
```bash
python ogg_to_mp3_converter.py "/music/My Collection" \
  --threads 8 \
  --bitrate 192k
```

## 🏷️ Tag Preservation

MP3cator automatically preserves metadata tags including:

- **Basic Tags:** Artist, Title, Album, Date/Year, Genre
- **Advanced Tags:** Album Artist, Track Number, Disc Number, Composer
- **Additional:** Performer, Comment, Lyrics, Copyright

**Supported Tag Mappings:**
- `tracknumber` → `track` (formatted as "01", "02", etc.)
- `year` → `date` 
- `picture` → `albumart`
- And many more...

## 🔧 Output Modes

### 1. In-Place Conversion (Default)
- Converts files in their original location
- Preserves exact directory structure
- Files: `Song.ogg` → `Song.mp3`

### 2. Restructured Output (`--restructure`)
- Creates `RS/` subfolder in source directory
- Converts paths to camelCase
- Example: `01 - My Song.ogg` → `RS/artistName/albumName/01MySong.mp3`

### 3. Custom Output (`--output-dir`)
- Outputs to specified directory
- Preserves original directory structure
- Overrides `--restructure` if both specified

## ⚡ Performance

- **Multi-threading:** Utilizes all CPU cores by default
- **Smart Skipping:** Only converts new/changed files
- **Batch Processing:** Handles thousands of files efficiently
- **Progress Tracking:** Real-time progress with file counts

### Typical Performance
- **Small files (3-5 MB):** ~50-100 files/minute
- **Large files (50+ MB):** ~10-20 files/minute
- **Performance scales** with CPU cores and disk speed

## 🔍 Post-Check & Verification

The `--post-check` option provides:
- ✅ Verification that all OGG files have corresponding MP3s
- 📊 Summary of conversion results
- 🗑️ Optional safe deletion of originals (`--delete`)

**Safety Features:**
- Only deletes when ALL files converted successfully
- Clear warnings before any deletion
- Detailed reporting of any unconverted files

## 🐛 Debugging

### Verbose Mode
```bash
python ogg_to_mp3_converter.py "/music" --verbose
```
Shows:
- Tag extraction details
- FFprobe command execution
- File processing steps
- Error diagnostics

### Common Issues

**"No tags found in source file"**
- Enable `--verbose` to see tag extraction process
- Check if OGG files have embedded metadata
- Verify ffprobe can read the files

**"Could not decode file"**
- File may be corrupted
- Install vorbis-tools: `sudo apt install vorbis-tools`
- Check file permissions

**Terminal display issues**
- Fixed automatically with built-in terminal cleanup
- Progress bars restore cursor and input echo

## 📁 Project Structure

```
mp3cator/
├── ogg_to_mp3_converter.py    # Main script
├── core/
│   ├── __init__.py
│   ├── converter.py           # Single file conversion logic
│   ├── finder.py              # File discovery and filtering
│   ├── postcheck.py           # Post-conversion verification
│   ├── utils.py               # Path utilities and helpers
│   └── constants.py           # Application constants
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .gitignore                 # Git ignore patterns
```

## 🔧 Dependencies

### Python Packages
- `pydub` - Audio file manipulation
- `tqdm` - Progress bars
- `audioop-lts` - Audio processing support

### System Dependencies
- `ffmpeg` - Audio conversion engine
- `ffprobe` - Audio metadata extraction

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests (if any)
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Submit a pull request

## 📝 License

This project is open source. Feel free to use, modify, and distribute.

## 🆘 Support

If you encounter issues:
1. Check the **Common Issues** section above
2. Run with `--verbose` for detailed logging
3. Verify ffmpeg/ffprobe installation
4. Check file permissions and disk space

---

**Happy Converting! 🎵→🎶** 
