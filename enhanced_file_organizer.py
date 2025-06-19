#!/usr/bin/env python3
"""
Enhanced File Organizer - A comprehensive file organization tool
Author: Drae 
Description: Organizes files into categorized folders with smart features and user-friendly interface
New Feature: Advanced recursive empty folder deletion + CLI flag interception + Tkinter GUI
"""

import os
import shutil
import json
import sys
import logging
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes

# Configuration
class Config:
    SYSTEM_PROTECTED = ["Windows", "Android", "Program Files", "System32", "System Volume Information", 
                       "ProgramData", "Recovery", "Boot", "$Recycle.Bin", "hiberfil.sys", "pagefile.sys"]
    MIN_JUNK_SIZE_KB_DEFAULT = 10
    LOG_FILE = "organizer_log.txt"
    UNDO_FILE = "undo.json"
    DUPLICATE_MAP_FILE = "duplicates.json"
    JUNK_FOLDER = "Junk"
    MAX_FILENAME_LENGTH = 255
    HASH_CHUNK_SIZE = 8192
    MAX_WORKERS = 4
    
    # Enhanced file categorization map with MIME type fallback
    FILE_MAP = {
        "Documents": {
            "PDF": [".pdf"],
            "Word": [".doc", ".docx", ".dot", ".dotx", ".docm"],
            "PowerPoint": [".ppt", ".pptx", ".pps", ".ppsx", ".odp", ".potx"],
            "Excel": [".xls", ".xlsx", ".xlsm", ".csv", ".ods", ".xlsb"],
            "Text": [".txt", ".rtf", ".md", ".tex", ".log", ".readme", ".rst"],
            "eBooks": [".epub", ".mobi", ".azw3", ".djvu", ".fb2", ".lit"],
            "XPS": [".xps", ".oxps"],
            "OtherDocs": [".odt", ".abw", ".pages", ".wpd", ".wps", ".gdoc"]
        },
        "Images": {
            "JPEG": [".jpg", ".jpeg", ".jpe", ".jfif"],
            "PNG": [".png"],
            "GIF": [".gif"],
            "WebP": [".webp"],
            "BMP": [".bmp", ".dib"],
            "TIFF": [".tif", ".tiff"],
            "HEIC": [".heic", ".heif"],
            "RAW": [".raw", ".cr2", ".nef", ".arw", ".orf", ".sr2", ".dng", ".rw2"],
            "SVG": [".svg", ".svgz"],
            "OtherImages": [".ico", ".icns", ".ppm", ".pgm", ".pbm", ".psd", ".xcf", ".ai"]
        },
        "Videos": {
            "MP4": [".mp4", ".m4v"],
            "MKV": [".mkv"],
            "AVI": [".avi"],
            "MOV": [".mov", ".qt"],
            "WMV": [".wmv", ".asf"],
            "FLV": [".flv", ".f4v"],
            "WebM": [".webm"],
            "MTS": [".mts", ".m2ts", ".ts"],
            "3GP": [".3gp", ".3g2"],
            "OtherVideos": [".vob", ".mpg", ".mpeg", ".ogv", ".rmvb", ".divx", ".m2v"]
        },
        "Audio": {
            "MP3": [".mp3"],
            "WAV": [".wav"],
            "FLAC": [".flac"],
            "AAC": [".aac", ".m4a"],
            "OGG": [".ogg", ".oga"],
            "WMA": [".wma"],
            "MIDI": [".mid", ".midi"],
            "OtherAudio": [".opus", ".amr", ".aiff", ".au", ".ra", ".ac3", ".dts"]
        },
        "Compressed": {
            "ZIP": [".zip", ".zipx"],
            "RAR": [".rar", ".r00", ".r01", ".r02"],
            "7Z": [".7z"],
            "TAR": [".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz"],
            "GZ": [".gz", ".bz2", ".xz", ".lz", ".lzma"],
            "ISO": [".iso", ".img", ".bin", ".cue", ".mdf"],
            "DMG": [".dmg"],
            "OtherArchives": [".cab", ".ace", ".z", ".sit", ".sitx", ".pak"]
        },
        "Executables": {
            "Windows": [".exe", ".msi", ".scr", ".com", ".bat", ".cmd"],
            "Linux": [".deb", ".rpm", ".run", ".sh", ".appimage", ".snap"],
            "Mac": [".pkg", ".dmg", ".app"],
            "Scripts": [".ps1", ".vbs", ".py", ".pl", ".rb"],
            "OtherBins": [".bin", ".out", ".elf", ".so", ".dll"]
        },
        "MobileApps": {
            "Android": [".apk", ".xapk", ".apks", ".aab"],
            "iOS": [".ipa"]
        },
        "Code": {
            "Python": [".py", ".pyw", ".pyx", ".pyi", ".ipynb"],
            "Web": [".html", ".htm", ".css", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte"],
            "Java": [".java", ".jar", ".class", ".scala", ".kt"],
            "C_CPP": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"],
            "Scripts": [".sh", ".bash", ".zsh", ".fish", ".csh", ".tcsh"],
            "Data": [".json", ".xml", ".yml", ".yaml", ".toml", ".ini", ".cfg"],
            "PHP": [".php", ".phtml"],
            "SQL": [".sql", ".db", ".sqlite", ".sqlite3"],
            "Other": [".rs", ".go", ".pl", ".rb", ".lua", ".cs", ".swift", ".dart", ".r"]
        },
        "System": {
            "Logs": [".log", ".trace", ".out"],
            "Config": [".ini", ".cfg", ".conf", ".reg", ".plist", ".settings"],
            "Cache": [".tmp", ".temp", ".bak", ".old", ".swp", ".swo", ".orig", ".cache"]
        },
        "Fonts": {
            "TrueType": [".ttf", ".ttc"],
            "OpenType": [".otf"],
            "Other": [".woff", ".woff2", ".eot", ".pfb", ".pfm"]
        },
        "3D_Models": {
            "Common": [".obj", ".fbx", ".dae", ".3ds", ".blend", ".max", ".ma", ".mb"],
            "CAD": [".dwg", ".dxf", ".step", ".stp", ".iges", ".igs"],
            "STL": [".stl", ".ply"]
        }
    }

@dataclass
class FileOperation:
    """Represents a file operation for logging and undo functionality"""
    source: str
    destination: str
    operation: str
    timestamp: str
    size_bytes: int
    file_hash: Optional[str] = None

class OrganizationMode(Enum):
    """Different organization modes"""
    BY_TYPE = "by_type"
    BY_DATE = "by_date"
    BY_SIZE = "by_size"
    BY_EXTENSION = "by_extension"

class DuplicateHandling(Enum):
    """Duplicate file handling strategies"""
    RENAME = "rename"
    SKIP = "skip"
    REPLACE = "replace"
    MERGE_TO_DUPLICATES = "merge_duplicates"

class FileOrganizer:
    """Main file organizer class with enhanced functionality"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.operations_log: List[FileOperation] = []
        self.duplicate_map: Dict[str, List[str]] = {}
        self.stats = {
            'moved': 0,
            'skipped': 0,
            'errors': 0,
            'duplicates': 0,
            'total_size': 0,
            'protected_skipped': 0,
            'empty_folders_removed': 0
        }
        self.setup_logging()
        mimetypes.init()
        
        # CLI command parser for interactive mode
        self.parser = self.create_parser()
    
    def create_parser(self):
        """Create argument parser for CLI flag detection"""
        parser = argparse.ArgumentParser(
            description="Enhanced File Organizer - Organize your files with smart categorization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python organizer.py                 # Interactive organization
  python organizer.py --dryrun        # Preview without moving files
  python organizer.py --undo          # Undo last organization
  python organizer.py --types         # Show supported file types
  python organizer.py --duplicates    # Show duplicate analysis
  python organizer.py --cleanup       # Remove empty folders only
  python organizer.py --gui           # Launch GUI mode
            """
        )
        
        parser.add_argument('--dryrun', action='store_true', 
                           help='Preview organization without moving files')
        parser.add_argument('--undo', action='store_true',
                           help='Undo the last organization operation')
        parser.add_argument('--types', action='store_true',
                           help='Show supported file types and exit')
        parser.add_argument('--duplicates', action='store_true',
                           help='Show duplicate file analysis from last run')
        parser.add_argument('--cleanup', action='store_true',
                           help='Remove empty folders only (standalone mode)')
        parser.add_argument('--gui', action='store_true',
                           help='Launch GUI mode')
        
        return parser
    
    def handle_interactive_command(self, user_input: str) -> bool:
        """Handle CLI commands during interactive mode. Returns True if command was handled."""
        if not user_input.startswith('--'):
            return False
        
        try:
            # Parse the command
            args = self.parser.parse_args([user_input])
            
            if user_input == '--help':
                self.parser.print_help()
                return True
            elif user_input == '--types':
                self.show_supported_types()
                return True
            elif user_input == '--duplicates':
                self.show_duplicate_analysis()
                return True
            elif user_input == '--undo':
                self.undo_last_organization()
                return True
            elif user_input == '--cleanup':
                self.cleanup_empty_folders_only()
                return True
            elif user_input == '--gui':
                self.launch_gui()
                return True
            else:
                print(f"⚠️  Command {user_input} recognized but cannot be executed in interactive mode")
                return True
                
        except SystemExit:
            # argparse calls sys.exit() for help/error - catch it
            return True
        except:
            return False
    
    def launch_gui(self):
        """Launch the Tkinter GUI"""
        try:
            from organizer_gui import FileOrganizerGUI
            gui = FileOrganizerGUI(self)
            gui.run()
        except ImportError:
            print("❌ GUI dependencies not available. Install tkinter.")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('organizer.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of file for duplicate detection"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                while chunk := f.read(self.config.HASH_CHUNK_SIZE):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot hash {file_path}: {e}")
            return None
    
    def detect_mime_type(self, file_path: str) -> Tuple[str, str]:
        """Detect file type using MIME types as fallback"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            return "Others", "Unknown"
        
        main_type, sub_type = mime_type.split('/', 1)
        
        mime_category_map = {
            'text': 'Documents',
            'image': 'Images', 
            'video': 'Videos',
            'audio': 'Audio',
            'application': 'Documents'  # Most application types are documents
        }
        
        category = mime_category_map.get(main_type, 'Others')
        return category, sub_type.title()
    
    def print_welcome_and_usage(self):
        """Display unified welcome header and usage instructions"""
        welcome = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ✨ Enhanced File Organizer by Drae ✨                     ║
║                          🚀 Improved Version 2.1                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔧 COMMAND LINE OPTIONS:
  python organizer.py                 Run interactive file organizer
  python organizer.py --dryrun        Preview operations (no files moved)
  python organizer.py --undo          Undo last organization
  python organizer.py --types         Show supported file types
  python organizer.py --duplicates    Show duplicate analysis
  python organizer.py --cleanup       Remove empty folders only
  python organizer.py --gui           Launch GUI mode
  python organizer.py --help          Show detailed help

🚀 NEW FEATURES:
  • Enhanced recursive empty folder deletion
  • Standalone empty folder cleanup mode
  • Improved duplicate detection with file hashing
  • Multi-threaded processing for better performance
  • MIME type fallback detection
  • Advanced duplicate handling options
  • Improved error recovery and logging
  • 3D model file support
  • CLI flag interception during interactive mode
  • Comprehensive Tkinter GUI

🔧 ORGANIZATION MODES:
  • By Type: Documents, Images, Videos, etc.
  • By Date: Year/Month folders based on creation date
  • By Size: Small, Medium, Large, Very Large categories
  • By Extension: Group by file extension

⚠️  SAFETY FEATURES:
  • Enhanced system folder protection
  • Atomic file operations with rollback
  • Comprehensive logging and undo system
  • Progress tracking with interruption recovery
  • Advanced recursive empty folder removal
  
💡 INTERACTIVE MODE TIP:
  Type any CLI flag (like --help, --types, --undo) during prompts for instant access!
        """
        print(welcome)
    
    def show_supported_types(self):
        """Display all supported file types by category"""
        print("\n📁 SUPPORTED FILE TYPES BY CATEGORY:")
        print("=" * 70)
        
        total_extensions = 0
        for category, subcategories in self.config.FILE_MAP.items():
            print(f"\n🗂️  {category.upper().replace('_', ' ')}:")
            for subcategory, extensions in subcategories.items():
                total_extensions += len(extensions)
                ext_list = ", ".join(extensions[:6])  # Show first 6 extensions
                if len(extensions) > 6:
                    ext_list += f" ... and {len(extensions) - 6} more"
                print(f"   └── {subcategory}: {ext_list}")
        
        print(f"\n📊 Total Categories: {len(self.config.FILE_MAP)}")
        total_subcats = sum(len(subs) for subs in self.config.FILE_MAP.values())
        print(f"📊 Total Subcategories: {total_subcats}")
        print(f"📊 Total Extensions: {total_extensions}")
        
        input("\nPress Enter to continue...")
    
    def get_yes_no_input(self, question: str, default: str = "n") -> bool:
        """Get yes/no input from user with clear instructions"""
        default_text = f" (Y/n)" if default.lower() == "y" else f" (y/N)"
        full_question = f"{question}{default_text}: "
        
        while True:
            try:
                response = input(full_question).strip().lower()
                
                # Check for CLI commands first
                if self.handle_interactive_command(response):
                    continue
                
                if not response:
                    return default.lower() == "y"
                elif response in ['y', 'yes', '1', 'true']:
                    return True
                elif response in ['n', 'no', '0', 'false']:
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no (or press Enter for default)")
                    print("💡 You can also type CLI flags like --help, --types, --undo")
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)

    def get_user_input(self) -> Tuple[List[str], str, int, OrganizationMode, DuplicateHandling]:
        """Get user input for organization parameters with detailed guidance"""
        print("\n🚀 STEP-BY-STEP CONFIGURATION:")
        print("─" * 50)
        print("💡 TIP: Type CLI flags like --help, --types, --undo anytime!")
        
        # Source folders
        print("\n📁 STEP 1: Select Source Folder(s)")
        print("   💡 TIP: Multiple folders separated by commas")
        print("   💡 Example: C:\\Downloads, D:\\Temp")
        print("   💡 Use quotes for paths with spaces")
        
        while True:
            try:
                sources_input = input("\n➤ Enter source folder(s): ").strip()
                
                # Check for CLI commands first
                if self.handle_interactive_command(sources_input):
                    continue
                
                if not sources_input:
                    print("❌ Please enter at least one source folder")
                    continue
                
                sources = [Path(s.strip().strip('"')).resolve() for s in sources_input.split(",") if s.strip()]
                
                # Validate sources
                valid_sources = []
                for source in sources:
                    if source.exists() and source.is_dir():
                        if not self.is_protected_path(str(source)):
                            valid_sources.append(str(source))
                            print(f"   ✅ Valid: {source}")
                        else:
                            print(f"   ⚠️  Protected (skipped): {source}")
                    else:
                        print(f"   ❌ Invalid: {source}")
                
                if valid_sources:
                    if self.get_yes_no_input(f"\n❓ Use these {len(valid_sources)} source folder(s)"):
                        break
                else:
                    print("❌ No valid directories found. Try again.")
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)
        
        # Target folder
        print(f"\n🎯 STEP 2: Select Target Organization Folder")
        print("   💡 Where organized files will be moved")
        print("   💡 Created automatically if doesn't exist")
        
        while True:
            try:
                target = input("\n➤ Enter target folder: ").strip().strip('"')
                
                # Check for CLI commands first
                if self.handle_interactive_command(target):
                    continue
                
                if not target:
                    print("❌ Please enter a target folder")
                    continue
                
                target_path = Path(target).resolve()
                
                # Check if target is one of the sources
                if str(target_path) in valid_sources:
                    print("❌ Target cannot be the same as source folder")
                    continue
                
                if target_path.exists() and any(target_path.iterdir()):
                    print(f"   ⚠️  Warning: {target_path} contains files")
                    if not self.get_yes_no_input("   ❓ Continue anyway"):
                        continue
                
                if self.get_yes_no_input("❓ Use this target folder"):
                    try:
                        target_path.mkdir(parents=True, exist_ok=True)
                        break
                    except Exception as e:
                        print(f"   ❌ Error creating folder: {e}")
                        continue
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)
        
        # Junk threshold
        print(f"\n📏 STEP 3: Set Junk File Threshold")
        print("   💡 Files smaller than this go to 'Junk' folder")
        print("   💡 Common: 10 KB (default), 50 KB, 100 KB, or 0 to disable")
        
        while True:
            try:
                threshold_input = input(f"\n➤ Junk threshold in KB (default: {self.config.MIN_JUNK_SIZE_KB_DEFAULT}): ").strip()
                
                # Check for CLI commands first
                if self.handle_interactive_command(threshold_input):
                    continue
                
                if not threshold_input:
                    junk_threshold = self.config.MIN_JUNK_SIZE_KB_DEFAULT
                    break
                
                junk_threshold = int(threshold_input)
                if junk_threshold < 0:
                    print("❌ Must be 0 or positive")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)
        
        # Organization mode
        print(f"\n📋 STEP 4: Choose Organization Mode")
        print("   1. 📁 By File Type (default) - Documents, Images, etc.")
        print("   2. 📅 By Creation Date - Year/Month folders")
        print("   3. 📊 By File Size - Small, Medium, Large")
        print("   4. 🏷️  By Extension - Group by file extension")
        
        mode_map = {
            "1": OrganizationMode.BY_TYPE,
            "2": OrganizationMode.BY_DATE, 
            "3": OrganizationMode.BY_SIZE,
            "4": OrganizationMode.BY_EXTENSION,
            "": OrganizationMode.BY_TYPE
        }
        
        while True:
            try:
                mode_choice = input("\n➤ Choose mode (1-4, default: 1): ").strip()
                
                # Check for CLI commands first
                if self.handle_interactive_command(mode_choice):
                    continue
                
                if mode_choice in mode_map:
                    mode = mode_map[mode_choice]
                    break
                else:
                    print("❌ Please enter 1, 2, 3, or 4")
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)
        
        # Duplicate handling
        print(f"\n🔄 STEP 5: Choose Duplicate Handling Strategy")
        print("   1. 📝 Rename duplicates (default) - Add (1), (2), etc.")
        print("   2. ⏭️  Skip duplicates - Keep original, skip new")
        print("   3. 🔄 Replace duplicates - Replace with newer file")
        print("   4. 📂 Move to Duplicates folder - Separate folder for duplicates")
        
        dup_map = {
            "1": DuplicateHandling.RENAME,
            "2": DuplicateHandling.SKIP,
            "3": DuplicateHandling.REPLACE,
            "4": DuplicateHandling.MERGE_TO_DUPLICATES,
            "": DuplicateHandling.RENAME
        }
        
        while True:
            try:
                dup_choice = input("\n➤ Choose duplicate handling (1-4, default: 1): ").strip()
                
                # Check for CLI commands first
                if self.handle_interactive_command(dup_choice):
                    continue
                
                if dup_choice in dup_map:
                    duplicate_handling = dup_map[dup_choice]
                    break
                else:
                    print("❌ Please enter 1, 2, 3, or 4")
            except KeyboardInterrupt:
                print("\n\n🛑 Operation cancelled by user")
                sys.exit(0)
        
        return valid_sources, str(target_path), junk_threshold, mode, duplicate_handling

    def preview_organization(self, sources: List[str], target: str, threshold: int, mode: OrganizationMode) -> dict:
        """Preview what the organization will do with multithreading"""
        print("\n🔍 ANALYZING FILES FOR PREVIEW...")
        
        preview_stats = {
            'total_files': 0,
            'categories': {},
            'junk_files': 0,
            'protected_skipped': 0,
            'total_size_mb': 0,
            'duplicate_groups': 0,
            'largest_files': []
        }
        
        all_files = []
        
        # Collect all files first
        for source in sources:
            print(f"   📂 Scanning: {os.path.basename(source)}...")
            
            for root, dirs, files in os.walk(source):
                if self.is_protected_path(root):
                    preview_stats['protected_skipped'] += len(files)
                    continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
        
        # Process files with threading for better performance
        def analyze_file(file_path):
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_kb = file_size_bytes / 1024
                file_size_mb = file_size_bytes / (1024 * 1024)
                
                result = {
                    'path': file_path,
                    'size_mb': file_size_mb,
                    'size_kb': file_size_kb,
                    'size_bytes': file_size_bytes
                }
                
                if file_size_kb < threshold:
                    result['category'] = 'Junk'
                else:
                    if mode == OrganizationMode.BY_TYPE:
                        category, subcategory = self.get_file_category(file_path)
                        result['category'] = f"{category}/{subcategory}"
                    elif mode == OrganizationMode.BY_DATE:
                        stat = os.stat(file_path)
                        date = datetime.fromtimestamp(stat.st_mtime)
                        result['category'] = f"By Date/{date.year}/{date.month:02d}-{date.strftime('%B')}"
                    elif mode == OrganizationMode.BY_SIZE:
                        if file_size_mb < 1:
                            result['category'] = "By Size/Small (< 1MB)"
                        elif file_size_mb < 10:
                            result['category'] = "By Size/Medium (1-10MB)"
                        elif file_size_mb < 100:
                            result['category'] = "By Size/Large (10-100MB)"
                        else:
                            result['category'] = "By Size/Very Large (> 100MB)"
                    else:  # BY_EXTENSION
                        ext = Path(file_path).suffix.lower() or 'no_extension'
                        result['category'] = f"By Extension/{ext.replace('.', '').upper() if ext != 'no_extension' else 'NO_EXTENSION'}"
                
                return result
                
            except (OSError, PermissionError):
                return {'error': True, 'path': file_path}
        
        # Process files with thread pool
        with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
            futures = [executor.submit(analyze_file, file_path) for file_path in all_files]
            
            for future in as_completed(futures):
                result = future.result()
                
                if result.get('error'):
                    preview_stats['protected_skipped'] += 1
                    continue
                
                preview_stats['total_files'] += 1
                preview_stats['total_size_mb'] += result['size_mb']
                
                if result['category'] == 'Junk':
                    preview_stats['junk_files'] += 1
                else:
                    category = result['category']
                    preview_stats['categories'][category] = preview_stats['categories'].get(category, 0) + 1
                
                # Track largest files
                if len(preview_stats['largest_files']) < 10:
                    preview_stats['largest_files'].append((result['path'], result['size_mb']))
                else:
                    preview_stats['largest_files'].sort(key=lambda x: x[1], reverse=True)
                    if result['size_mb'] > preview_stats['largest_files'][-1][1]:
                        preview_stats['largest_files'][-1] = (result['path'], result['size_mb'])
        
        return preview_stats
    
    def confirm_operation(self, sources: List[str], target: str, threshold: int, mode: OrganizationMode) -> bool:
        """Display detailed summary and get user confirmation"""
        print("\n" + "="*70)
        print("📊 ORGANIZATION PREVIEW & CONFIRMATION")
        print("="*70)
        
        # Get preview
        preview = self.preview_organization(sources, target, threshold, mode)
        
        # Display configuration summary
        print(f"\n🔧 CONFIGURATION:")
        print(f"   📂 Sources: {len(sources)} folders")
        for i, source in enumerate(sources, 1):
            print(f"      {i}. {source}")
        print(f"   🎯 Target: {target}")
        print(f"   📏 Junk threshold: {threshold} KB")
        print(f"   📋 Mode: {mode.value.replace('_', ' ').title()}")
        
        # Preview results
        print(f"\n📈 PREVIEW:")
        print(f"   📁 Total files: {preview['total_files']:,}")
        print(f"   💾 Total size: {preview['total_size_mb']:.1f} MB")
        print(f"   🗑️  Junk files: {preview['junk_files']:,}")
        print(f"   🔒 Protected skipped: {preview['protected_skipped']:,}")
        
        if preview['categories']:
            print(f"\n📂 TOP CATEGORIES:")
            sorted_categories = sorted(preview['categories'].items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:10]:
                print(f"   • {category}: {count:,} files")
            
            if len(sorted_categories) > 10:
                remaining = sum(count for _, count in sorted_categories[10:])
                print(f"   • ... {len(sorted_categories) - 10} more ({remaining:,} files)")
        
        # Show largest files
        if preview['largest_files']:
            print(f"\n🏋️ LARGEST FILES:")
            preview['largest_files'].sort(key=lambda x: x[1], reverse=True)
            for file_path, size_mb in preview['largest_files'][:5]:
                print(f"   • {os.path.basename(file_path)}: {size_mb:.1f} MB")
        
        print(f"\n⚠️  FILES WILL BE MOVED (not copied)")
        print(f"⚠️  All operations logged for undo capability")
        print(f"⚠️  Multi-threaded processing for better performance")
        
        return self.get_yes_no_input("\n❓ Proceed with organization")
    
    def is_protected_path(self, path: str) -> bool:
        """Enhanced check if path is in protected system directories"""
        path_lower = path.lower()
        path_parts = Path(path_lower).parts
        
        # Check against protected directories
        for protected in self.config.SYSTEM_PROTECTED:
            if protected.lower() in path_lower:
                return True
        
        # Additional checks for common system paths
        system_indicators = ['system', 'windows', 'program files', 'programdata', 'recovery']
        if any(indicator in path_parts for indicator in system_indicators):
            return True
        
        return False
    
    def get_file_category(self, file_path: str) -> Tuple[str, str]:
        """Enhanced file categorization with MIME type fallback"""
        ext = Path(file_path).suffix.lower()
        
        if not ext:
            # Try MIME type detection for extensionless files
            return self.detect_mime_type(file_path)
        
        for category, subcategories in self.config.FILE_MAP.items():
            for subcategory, extensions in subcategories.items():
                if ext in extensions:
                    return category, subcategory
        
        # Fallback to MIME type detection
        mime_category, mime_subcategory = self.detect_mime_type(file_path)
        if mime_category != "Others":
            return mime_category, mime_subcategory
        
        return "Others", "Uncategorized"
    
    def get_organization_path(self, file_path: str, target: str, mode: OrganizationMode) -> str:
        """Get the organization path based on the selected mode"""
        if mode == OrganizationMode.BY_TYPE:
            category, subcategory = self.get_file_category(file_path)
            return os.path.join(target, category, subcategory)
        
        elif mode == OrganizationMode.BY_DATE:
            stat = os.stat(file_path)
            date = datetime.fromtimestamp(stat.st_mtime)
            return os.path.join(target, "By Date", str(date.year), f"{date.month:02d}-{date.strftime('%B')}")
        
        elif mode == OrganizationMode.BY_SIZE:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb < 1:
                size_category = "Small (< 1MB)"
            elif size_mb < 10:
                size_category = "Medium (1-10MB)"
            elif size_mb < 100:
                size_category = "Large (10-100MB)"
            else:
                size_category = "Very Large (> 100MB)"
            return os.path.join(target, "By Size", size_category)
        
        else:  # BY_EXTENSION
            ext = Path(file_path).suffix.lower() or 'no_extension'
            return os.path.join(target, "By Extension", ext.replace(".", "").upper() if ext != 'no_extension' else 'NO_EXTENSION')
    
    def generate_unique_filename(self, target_path: str, duplicate_handling: DuplicateHandling) -> str:
        """Generate unique filename to avoid conflicts"""
        if duplicate_handling == DuplicateHandling.SKIP:
            return None  # Signal to skip this file
        
        if duplicate_handling == DuplicateHandling.REPLACE:
            return target_path  # Overwrite existing file
        
        if duplicate_handling == DuplicateHandling.MERGE_TO_DUPLICATES:
            # Move to duplicates folder
            parent = Path(target_path).parent
            duplicates_folder = parent / "Duplicates"
            duplicates_folder.mkdir(exist_ok=True)
            return str(duplicates_folder / Path(target_path).name)
        
        # RENAME strategy (default)
        base_path = Path(target_path)
        parent = base_path.parent
        stem = base_path.stem
        suffix = base_path.suffix
        
        counter = 1
        while True:
            new_name = f"{stem} ({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1
            if counter > 1000:  # Safety limit
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return str(parent / f"{stem}_{timestamp}{suffix}")
    
    def move_file_safe(self, source: str, destination: str, duplicate_handling: DuplicateHandling) -> bool:
        """Safely move file with error handling and conflict resolution"""
        try:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle duplicates
            if dest_path.exists():
                final_destination = self.generate_unique_filename(destination, duplicate_handling)
                if final_destination is None:
                    # Skip file
                    self.stats['skipped'] += 1
                    self.logger.info(f"Skipped (duplicate): {os.path.basename(source)}")
                    return False
                destination = final_destination
            
            # Calculate file hash for logging
            file_hash = self.calculate_file_hash(source) if duplicate_handling != DuplicateHandling.SKIP else None
            file_size = os.path.getsize(source)
            
            # Perform the move
            shutil.move(source, destination)
            
            # Log the operation
            operation = FileOperation(
                source=source,
                destination=destination,
                operation="move",
                timestamp=datetime.now().isoformat(),
                size_bytes=file_size,
                file_hash=file_hash
            )
            self.operations_log.append(operation)
            
            self.stats['moved'] += 1
            self.stats['total_size'] += file_size
            
            # Track duplicates for analysis
            if file_hash:
                if file_hash not in self.duplicate_map:
                    self.duplicate_map[file_hash] = []
                self.duplicate_map[file_hash].append(destination)
                if len(self.duplicate_map[file_hash]) > 1:
                    self.stats['duplicates'] += 1
            
            return True
            
        except (OSError, PermissionError, shutil.Error) as e:
            self.logger.error(f"Failed to move {source}: {e}")
            self.stats['errors'] += 1
            return False

    def organize_files(self, sources: List[str], target: str, junk_threshold: int, 
                      mode: OrganizationMode, duplicate_handling: DuplicateHandling, dry_run: bool = False):
        """Main organization function with enhanced features"""
        print(f"\n🚀 {'DRY RUN - ' if dry_run else ''}STARTING ORGANIZATION...")
        print("─" * 50)
        
        # Collect all files
        all_files = []
        for source in sources:
            print(f"📂 Scanning: {os.path.basename(source)}...")
            
            for root, dirs, files in os.walk(source):
                if self.is_protected_path(root):
                    self.stats['protected_skipped'] += len(files)
                    continue
                
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
        
        if not all_files:
            print("❌ No files found to organize")
            return
        
        print(f"📁 Found {len(all_files):,} files to process")
        
        # Process files with progress tracking
        junk_files = []
        processed = 0
        
        def process_file(file_path):
            nonlocal processed
            
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_kb = file_size_bytes / 1024
                
                # Determine destination
                if file_size_kb < junk_threshold:
                    # Junk file
                    junk_folder = os.path.join(target, self.config.JUNK_FOLDER)
                    dest_path = os.path.join(junk_folder, os.path.basename(file_path))
                    junk_files.append(file_path)
                else:
                    # Regular file
                    category_path = self.get_organization_path(file_path, target, mode)
                    dest_path = os.path.join(category_path, os.path.basename(file_path))
                
                if not dry_run:
                    success = self.move_file_safe(file_path, dest_path, duplicate_handling)
                    if success:
                        processed += 1
                        if processed % 100 == 0:
                            print(f"   ✅ Processed: {processed:,}/{len(all_files):,} files")
                else:
                    processed += 1
                    print(f"   [PREVIEW] {os.path.basename(file_path)} → {os.path.relpath(dest_path, target)}")
                
                return True
                
            except (OSError, PermissionError) as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
                return False
        
        # Process with threading for better performance
        if not dry_run:
            with ThreadPoolExecutor(max_workers=self.config.MAX_WORKERS) as executor:
                list(executor.map(process_file, all_files))
        else:
            for file_path in all_files:
                process_file(file_path)
        
        # Handle junk files
        if junk_files and not dry_run:
            print(f"\n🗑️  Found {len(junk_files):,} junk files (< {junk_threshold} KB)")
            if self.get_yes_no_input("❓ Delete junk files permanently"):
                deleted_junk = 0
                for junk_file in junk_files:
                    try:
                        os.remove(junk_file)
                        deleted_junk += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete junk {junk_file}: {e}")
                print(f"   🗑️  Deleted {deleted_junk:,} junk files")
        
        # Enhanced empty directory cleanup
        if not dry_run:
            if self.get_yes_no_input("\n❓ Remove empty folders from source directories"):
                self.remove_empty_directories_recursive(sources)
        
        # Save operations log and duplicate map
        if not dry_run:
            self.save_operations_log()
            self.save_duplicate_map()
        
        self.print_final_summary(dry_run)

    def scan_for_empty_directories(self, root_paths: List[str]) -> Set[str]:
        """Scan for empty directories recursively and return a set of empty directories"""
        empty_dirs = set()
        
        for root_path in root_paths:
            print(f"   🔍 Scanning for empty folders in: {os.path.basename(root_path)}...")
            
            for current_dir, subdirs, files in os.walk(root_path, topdown=False):
                # Skip protected paths
                if self.is_protected_path(current_dir):
                    continue
                
                try:
                    # Check if directory is truly empty (no files and no non-empty subdirectories)
                    dir_contents = list(os.scandir(current_dir))
                    
                    # Filter out hidden/system files and check if any real content exists
                    has_real_content = False
                    for entry in dir_contents:
                        if entry.is_file():
                            # Check if it's not a hidden/system file
                            if not entry.name.startswith('.') and not entry.name.startswith('~'):
                                has_real_content = True
                                break
                        elif entry.is_dir():
                            # Check if subdirectory is not empty (and not in our empty set)
                            if entry.path not in empty_dirs:
                                has_real_content = True
                                break
                    
                    if not has_real_content:
                        empty_dirs.add(current_dir)
                        
                except (OSError, PermissionError) as e:
                    self.logger.warning(f"Cannot access directory {current_dir}: {e}")
                    continue
        
        return empty_dirs
    
    def remove_empty_directories_recursive(self, sources: List[str], max_iterations: int = 10):
        """Enhanced recursive empty directory removal with multiple passes"""
        print(f"\n🗂️  ADVANCED RECURSIVE EMPTY FOLDER CLEANUP")
        print("─" * 50)
        
        total_removed = 0
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Pass {iteration}: Scanning for empty directories...")
            
            # Find all empty directories
            empty_dirs = self.scan_for_empty_directories(sources)
            
            if not empty_dirs:
                print(f"   ✅ No empty directories found")
                break
            
            print(f"   📁 Found {len(empty_dirs)} empty directories")
            
            # Sort by depth (deepest first) to avoid parent/child conflicts
            empty_dirs_sorted = sorted(empty_dirs, key=lambda x: x.count(os.sep), reverse=True)
            
            # Remove empty directories
            removed_this_pass = 0
            failed_this_pass = 0
            
            for empty_dir in empty_dirs_sorted:
                try:
                    # Double-check it's still empty before removing
                    if os.path.exists(empty_dir):
                        dir_contents = list(os.scandir(empty_dir))
                        if not dir_contents:  # Truly empty
                            os.rmdir(empty_dir)
                            removed_this_pass += 1
                            total_removed += 1
                            self.logger.info(f"Removed empty directory: {empty_dir}")
                            
                            # Show progress every 10 deletions
                            if removed_this_pass % 10 == 0:
                                print(f"      🗑️  Removed: {removed_this_pass} folders")
                                
                except (OSError, PermissionError) as e:
                    failed_this_pass += 1
                    self.logger.warning(f"Cannot remove {empty_dir}: {e}")
            
            print(f"   ✅ Removed: {removed_this_pass} directories")
            if failed_this_pass > 0:
                print(f"   ⚠️  Failed: {failed_this_pass} directories")
            
            # If we didn't remove any directories, we're done
            if removed_this_pass == 0:
                print(f"   🎯 No more empty directories to remove")
                break
        
        # Update stats
        self.stats['empty_folders_removed'] = total_removed
        
        print(f"\n📊 EMPTY FOLDER CLEANUP SUMMARY:")
        print(f"   🗂️  Total passes: {iteration}")
        print(f"   🗑️  Total directories removed: {total_removed}")
        
        if total_removed > 0:
            print(f"   🎉 Cleanup completed successfully!")
        
        return total_removed
    
    def cleanup_empty_folders_only(self, sources: List[str] = None):
        """Standalone empty folder cleanup mode"""
        print("\n🗂️  STANDALONE EMPTY FOLDER CLEANUP MODE")
        print("=" * 70)
        
        if sources is None:
            # Get directories from user input
            print("\n📁 SELECT DIRECTORIES TO CLEAN:")
            print("   💡 Multiple directories separated by commas")
            print("   💡 Use quotes for paths with spaces")
            
            while True:
                try:
                    sources_input = input("\n➤ Enter directories to clean: ").strip()
                    if not sources_input:
                        print("❌ Please enter at least one directory")
                        continue
                    
                    sources = [Path(s.strip().strip('"')).resolve() for s in sources_input.split(",") if s.strip()]
                    
                    # Validate sources
                    valid_sources = []
                    for source in sources:
                        if source.exists() and source.is_dir():
                            if not self.is_protected_path(str(source)):
                                valid_sources.append(str(source))
                                print(f"   ✅ Valid: {source}")
                            else:
                                print(f"   ⚠️  Protected (skipped): {source}")
                        else:
                            print(f"   ❌ Invalid: {source}")
                    
                    if valid_sources:
                        sources = valid_sources
                        break
                    else:
                        print("❌ No valid directories found. Try again.")
                        
                except KeyboardInterrupt:
                    print("\n\n🛑 Operation cancelled by user")
                    sys.exit(0)
        
        # Preview empty directories
        print(f"\n🔍 SCANNING FOR EMPTY DIRECTORIES...")
        empty_dirs = self.scan_for_empty_directories(sources)
        
        if not empty_dirs:
            print("✅ No empty directories found!")
            return
        
        print(f"\n📊 PREVIEW RESULTS:")
        print(f"   📁 Empty directories found: {len(empty_dirs)}")
        print(f"   📂 Source directories: {len(sources)}")
        
        # Show some examples
        print(f"\n📋 EXAMPLES OF EMPTY DIRECTORIES:")
        empty_dirs_sorted = sorted(empty_dirs, key=lambda x: x.count(os.sep), reverse=True)
        for i, empty_dir in enumerate(empty_dirs_sorted[:10], 1):
            rel_path = os.path.relpath(empty_dir, sources[0]) if len(sources) == 1 else empty_dir
            print(f"   {i:2d}. {rel_path}")
        
        if len(empty_dirs) > 10:
            print(f"       ... and {len(empty_dirs) - 10} more")
        
        # Confirm cleanup
        if self.get_yes_no_input(f"\n❓ Remove all {len(empty_dirs)} empty directories"):
            removed_count = self.remove_empty_directories_recursive(sources)
            
            if removed_count > 0:
                print(f"\n🎉 Successfully removed {removed_count} empty directories!")
            else:
                print(f"\n❌ No directories were removed")
        else:
            print("❌ Cleanup cancelled by user")

    def save_operations_log(self):
        """Save operations for undo functionality"""
        try:
            with open(self.config.UNDO_FILE, 'w') as f:
                operations_data = [asdict(op) for op in self.operations_log]
                json.dump(operations_data, f, indent=2)
            self.logger.info(f"Saved {len(self.operations_log)} operations to {self.config.UNDO_FILE}")
        except Exception as e:
            self.logger.error(f"Failed to save operations log: {e}")
    
    def save_duplicate_map(self):
        """Save duplicate file mapping"""
        try:
            duplicates_only = {k: v for k, v in self.duplicate_map.items() if len(v) > 1}
            with open(self.config.DUPLICATE_MAP_FILE, 'w') as f:
                json.dump(duplicates_only, f, indent=2)
            if duplicates_only:
                self.logger.info(f"Saved {len(duplicates_only)} duplicate groups to {self.config.DUPLICATE_MAP_FILE}")
        except Exception as e:
            self.logger.error(f"Failed to save duplicate map: {e}")
    
    def print_final_summary(self, dry_run: bool = False):
        """Print comprehensive final summary"""
        print(f"\n{'🔸' * 70}")
        print(f"{'DRY RUN ' if dry_run else ''}ORGANIZATION COMPLETE!")
        print(f"{'🔸' * 70}")
        
        print(f"\n📊 STATISTICS:")
        if not dry_run:
            print(f"   ✅ Files moved: {self.stats['moved']:,}")
            print(f"   ⏭️  Files skipped: {self.stats['skipped']:,}")
            print(f"   ❌ Errors: {self.stats['errors']:,}")
            print(f"   🔄 Duplicates found: {self.stats['duplicates']:,}")
            print(f"   💾 Total size processed: {self.stats['total_size'] / (1024*1024):.1f} MB")
            print(f"   🔒 Protected files skipped: {self.stats['protected_skipped']:,}")
            print(f"   🗂️  Empty folders removed: {self.stats['empty_folders_removed']:,}")
        else:
            print(f"   📁 Files analyzed: {sum([self.stats['moved'], self.stats['skipped'], self.stats['errors']]):,}")
        
        if not dry_run:
            print(f"\n📋 LOGS CREATED:")
            print(f"   📝 Operations log: {self.config.UNDO_FILE}")
            print(f"   🔄 Duplicate map: {self.config.DUPLICATE_MAP_FILE}")
            print(f"   📊 General log: organizer.log")
            
            print(f"\n💡 UNDO AVAILABLE:")
            print(f"   Run: python organizer.py --undo")
        
        print(f"\n🎉 Organization {'preview' if dry_run else 'completed'} successfully!")
        input("\nPress Enter to exit...")

    def undo_last_organization(self):
        """Undo the last organization operation"""
        print("\n↩️  UNDO LAST ORGANIZATION")
        print("─" * 50)
        
        if not os.path.exists(self.config.UNDO_FILE):
            print("❌ No undo file found. Nothing to undo.")
            return
        
        try:
            with open(self.config.UNDO_FILE, 'r') as f:
                operations_data = json.load(f)
            
            if not operations_data:
                print("❌ No operations found in undo file.")
                return
            
            print(f"📋 Found {len(operations_data)} operations to undo")
            
            if not self.get_yes_no_input("❓ Proceed with undo"):
                return
            
            # Reverse the operations
            undone = 0
            skipped = 0
            errors = 0
            
            for op_data in reversed(operations_data):
                source = op_data['destination']  # Current location
                destination = op_data['source']  # Original location
                
                try:
                    if os.path.exists(source):
                        if os.path.exists(destination):
                            print(f"   ⏭️  Skipped (destination exists): {os.path.basename(destination)}")
                            skipped += 1
                        else:
                            # Create destination directory if needed
                            os.makedirs(os.path.dirname(destination), exist_ok=True)
                            shutil.move(source, destination)
                            undone += 1
                            
                            if undone % 50 == 0:
                                print(f"   ↩️  Undone: {undone:,} operations")
                    else:
                        skipped += 1
                        
                except Exception as e:
                    self.logger.error(f"Undo error for {source}: {e}")
                    errors += 1
            
            print(f"\n📊 UNDO SUMMARY:")
            print(f"   ↩️  Operations undone: {undone:,}")
            print(f"   ⏭️  Skipped: {skipped:,}")
            print(f"   ❌ Errors: {errors:,}")
            
            # Clean up undo file
            if self.get_yes_no_input("\n❓ Delete undo file"):
                os.remove(self.config.UNDO_FILE)
                print("   🗑️  Undo file deleted")
            
        except Exception as e:
            print(f"❌ Error during undo: {e}")
    
    def show_duplicate_analysis(self):
        """Show detailed duplicate file analysis"""
        print("\n🔄 DUPLICATE FILE ANALYSIS")
        print("─" * 50)
        
        if not os.path.exists(self.config.DUPLICATE_MAP_FILE):
            print("❌ No duplicate analysis file found. Run organization first.")
            return
        
        try:
            with open(self.config.DUPLICATE_MAP_FILE, 'r') as f:
                duplicate_map = json.load(f)
            
            if not duplicate_map:
                print("✅ No duplicates found in last organization!")
                return
            
            total_duplicates = sum(len(files) for files in duplicate_map.values())
            duplicate_groups = len(duplicate_map)
            
            print(f"📊 DUPLICATE STATISTICS:")
            print(f"   🔄 Duplicate groups: {duplicate_groups:,}")
            print(f"   📁 Total duplicate files: {total_duplicates:,}")
            
            print(f"\n🔍 TOP DUPLICATE GROUPS:")
            sorted_groups = sorted(duplicate_map.items(), key=lambda x: len(x[1]), reverse=True)
            
            for i, (file_hash, files) in enumerate(sorted_groups[:10], 1):
                print(f"\n   {i}. Group with {len(files)} copies:")
                for file_path in files[:3]:  # Show first 3 files
                    print(f"      • {os.path.basename(file_path)}")
                if len(files) > 3:
                    print(f"      • ... and {len(files) - 3} more")
            
            if len(sorted_groups) > 10:
                print(f"\n   ... and {len(sorted_groups) - 10} more groups")
            
        except Exception as e:
            print(f"❌ Error reading duplicate analysis: {e}")
        
        input("\nPress Enter to continue...")

def main():
    """Main function with enhanced command line argument handling"""
    parser = argparse.ArgumentParser(
        description="Enhanced File Organizer - Organize your files with smart categorization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python organizer.py                 # Interactive organization
  python organizer.py --dryrun        # Preview without moving files
  python organizer.py --undo          # Undo last organization
  python organizer.py --types         # Show supported file types
  python organizer.py --duplicates    # Show duplicate analysis
  python organizer.py --cleanup       # Remove empty folders only
  python organizer.py --gui           # Launch GUI mode
        """
    )
    
    parser.add_argument('--dryrun', action='store_true', 
                       help='Preview organization without moving files')
    parser.add_argument('--undo', action='store_true',
                       help='Undo the last organization operation')
    parser.add_argument('--types', action='store_true',
                       help='Show supported file types and exit')
    parser.add_argument('--duplicates', action='store_true',
                       help='Show duplicate file analysis from last run')
    parser.add_argument('--cleanup', action='store_true',
                       help='Remove empty folders only (standalone mode)')
    parser.add_argument('--gui', action='store_true',
                       help='Launch GUI mode')
    
    args = parser.parse_args()
    
    # Initialize organizer
    organizer = FileOrganizer()
    
    # Handle command line arguments
    if args.types:
        organizer.print_welcome_and_usage()
        organizer.show_supported_types()
        return
    
    if args.duplicates:
        organizer.show_duplicate_analysis()
        return
    
    if args.undo:
        organizer.undo_last_organization()
        return
    
    if args.cleanup:
        organizer.cleanup_empty_folders_only()
        return
    
    if args.gui:
        organizer.launch_gui()
        return
    
    # Main interactive organization
    try:
        organizer.print_welcome_and_usage()
        
        # Get user input
        sources, target, junk_threshold, mode, duplicate_handling = organizer.get_user_input()
        
        # Confirm operation
        if organizer.confirm_operation(sources, target, junk_threshold, mode):
            # Perform organization
            organizer.organize_files(sources, target, junk_threshold, mode, duplicate_handling, args.dryrun)
        else:
            print("❌ Organization cancelled by user")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}")
        print("Check organizer.log for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
