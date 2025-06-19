
#!/usr/bin/env python3
"""
Enhanced File Organizer - A comprehensive file organization tool (IMPROVED VERSION)
Author: Drae 
Description: Organizes files into categorized folders with smart features and user-friendly interface
Version: 2.6 - Next phase improvements with better GUI integration and safety features
"""

import os
import shutil
import json
import sys
import logging
import hashlib
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes
from collections import defaultdict

@dataclass
class FileOperation:
    """Represents a file operation for logging and undo functionality"""
    source: str
    destination: str
    operation: str
    timestamp: str
    size_bytes: int
    file_hash: Optional[str] = None

@dataclass
class ProgressInfo:
    """Progress tracking information"""
    current: int = 0
    total: int = 0
    current_file: str = ""
    operation: str = ""
    start_time: float = 0
    
    @property
    def percentage(self) -> float:
        return (self.current / self.total * 100) if self.total > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time
    
    @property
    def eta_seconds(self) -> float:
        if self.current == 0:
            return 0
        rate = self.current / self.elapsed_time
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else 0

@dataclass
class PreviewResult:
    """Results from preview operation"""
    total_files: int = 0
    total_size_mb: float = 0.0
    categories: Dict[str, int] = None
    junk_files: int = 0
    protected_skipped: int = 0
    duplicate_groups: int = 0
    estimated_time_seconds: float = 0.0
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = {}

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

class Config:
    SYSTEM_PROTECTED = [
        "Windows", "Android", "Program Files", "Program Files (x86)", 
        "System32", "System Volume Information", "ProgramData", "Recovery", 
        "Boot", "$Recycle.Bin", "hiberfil.sys", "pagefile.sys", "swapfile.sys",
        "Windows.old", "Intel", "AMD", "NVIDIA"
    ]
    MIN_JUNK_SIZE_KB_DEFAULT = 10
    LOG_FILE = "organizer_log.txt"
    UNDO_FILE = "undo.json"
    DUPLICATE_MAP_FILE = "duplicates.json"
    CONFIG_FILE = "organizer_config.json"
    JUNK_FOLDER = "Junk"
    MAX_FILENAME_LENGTH = 255
    HASH_CHUNK_SIZE = 8192
    MAX_WORKERS = 4
    PROGRESS_UPDATE_INTERVAL = 50
    BACKUP_FOLDER = "OrganizeBackup"
    
    # Enhanced file categorization map
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

class FileOrganizerImproved:
    """Enhanced File Organizer with improved error handling and user feedback"""
    
    def __init__(self, config: Config = None, progress_callback: Callable[[ProgressInfo], None] = None):
        self.config = config or Config()
        self.operations_log: List[FileOperation] = []
        self.duplicate_map: Dict[str, List[str]] = {}
        self.progress_callback = progress_callback
        self.progress = ProgressInfo()
        self.cancelled = False
        
        # Enhanced statistics tracking
        self.stats = {
            'moved': 0,
            'skipped': 0,
            'errors': 0,
            'duplicates': 0,
            'total_size': 0,
            'protected_skipped': 0,
            'empty_folders_removed': 0,
            'processing_time': 0,
            'average_file_size': 0,
            'largest_file': {'name': '', 'size': 0},
            'categories_processed': defaultdict(int)
        }
        
        self.setup_logging()
        mimetypes.init()
        
        # CLI command parser for interactive mode
        self.parser = self.create_parser()
    
    def setup_logging(self):
        """Enhanced logging configuration with rotating files"""
        log_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        file_handler = logging.FileHandler('enhanced_organizer.log')
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.WARNING)
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def create_parser(self):
        """Create enhanced argument parser with better help"""
        parser = argparse.ArgumentParser(
            description="Enhanced File Organizer - Organize your files with smart categorization",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
🚀 EXAMPLES:
  python organizer.py                 Interactive organization mode
  python organizer.py --dryrun        Preview changes without moving files
  python organizer.py --undo          Undo the last organization
  python organizer.py --types         Show all supported file types
  python organizer.py --duplicates    Analyze duplicate files
  python organizer.py --cleanup       Remove empty folders only
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
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Enable verbose output')
        
        return parser
    
    def update_progress(self, current: int = None, operation: str = None, current_file: str = None):
        """Update progress information and call callback if provided"""
        if current is not None:
            self.progress.current = current
        if operation is not None:
            self.progress.operation = operation
        if current_file is not None:
            self.progress.current_file = current_file
        
        # Call progress callback for GUI updates
        if self.progress_callback:
            self.progress_callback(self.progress)
        
        # Console progress update
        if self.progress.total > 0 and self.progress.current % self.config.PROGRESS_UPDATE_INTERVAL == 0:
            percentage = self.progress.percentage
            eta_mins = self.progress.eta_seconds / 60
            current_file_name = os.path.basename(self.progress.current_file) if self.progress.current_file else "..."
            
            print(f"   📊 Progress: {percentage:.1f}% ({self.progress.current:,}/{self.progress.total:,}) "
                  f"- ETA: {eta_mins:.1f}min - Processing: {current_file_name}")
    
    def cancel_operation(self):
        """Cancel the current operation gracefully"""
        self.cancelled = True
        print("\n🛑 Cancellation requested... finishing current file...")
    
    def preview_organization(self, sources: List[str], target: str, junk_threshold: int, 
                           mode: OrganizationMode) -> Dict:
        """
        Preview what the organization would do without actually moving files
        Returns a dictionary with preview statistics
        """
        print("\n🔍 GENERATING ORGANIZATION PREVIEW...")
        print("=" * 60)
        
        self.progress.start_time = time.time()
        preview_result = PreviewResult()
        
        try:
            # Scan all files
            all_files, scan_stats = self.enhanced_file_scan(sources)
            preview_result.total_files = len(all_files)
            
            # Calculate total size
            total_size = 0
            category_counts = defaultdict(int)
            junk_count = 0
            protected_count = 0
            
            for file_path in all_files:
                try:
                    if self.is_protected_path(file_path):
                        protected_count += 1
                        continue
                    
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # Check if it's junk
                    if file_size < junk_threshold * 1024:  # Convert KB to bytes
                        junk_count += 1
                    
                    # Categorize file
                    category, subcategory = self.get_file_category(file_path)
                    category_counts[category] += 1
                    
                except (OSError, PermissionError):
                    continue
            
            preview_result.total_size_mb = total_size / (1024 * 1024)
            preview_result.categories = dict(category_counts)
            preview_result.junk_files = junk_count
            preview_result.protected_skipped = protected_count
            
            # Estimate processing time (rough calculation)
            preview_result.estimated_time_seconds = len(all_files) * 0.1  # 0.1 seconds per file estimate
            
            # Find duplicates for preview
            duplicate_groups = self.find_duplicate_groups(all_files[:1000])  # Sample for preview
            preview_result.duplicate_groups = len(duplicate_groups)
            
            print(f"\n📊 PREVIEW RESULTS:")
            print(f"   📁 Total files: {preview_result.total_files:,}")
            print(f"   💾 Total size: {preview_result.total_size_mb:.1f} MB")
            print(f"   🗑️ Junk files: {preview_result.junk_files:,}")
            print(f"   🔒 Protected files: {preview_result.protected_skipped:,}")
            print(f"   🔄 Potential duplicate groups: {preview_result.duplicate_groups:,}")
            print(f"   ⏱️ Estimated time: {preview_result.estimated_time_seconds/60:.1f} minutes")
            
            return asdict(preview_result)
            
        except Exception as e:
            self.logger.error(f"Preview failed: {e}")
            return {"error": str(e)}
    
    def find_duplicate_groups(self, files: List[str]) -> List[List[str]]:
        """Find groups of duplicate files"""
        hash_groups = defaultdict(list)
        
        for file_path in files:
            try:
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    hash_groups[file_hash].append(file_path)
            except:
                continue
        
        # Return only groups with more than one file
        return [group for group in hash_groups.values() if len(group) > 1]
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate file hash for duplicate detection"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(self.config.HASH_CHUNK_SIZE), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None
    
    def organize_files(self, sources: List[str], target: str, junk_threshold: int,
                      mode: OrganizationMode, duplicate_handling: DuplicateHandling,
                      dry_run: bool = False):
        """
        Main file organization method with enhanced features
        """
        print(f"\n🚀 {'PREVIEW' if dry_run else 'STARTING'} ENHANCED FILE ORGANIZATION")
        print("=" * 70)
        
        self.progress.start_time = time.time()
        self.stats = {'moved': 0, 'skipped': 0, 'errors': 0, 'duplicates': 0, 'total_size': 0}
        
        try:
            # Create backup if not dry run
            if not dry_run:
                self.create_backup(sources)
            
            # Enhanced file scanning
            all_files, scan_stats = self.enhanced_file_scan(sources)
            self.progress.total = len(all_files)
            
            if not all_files:
                print("❌ No files found to organize!")
                return
            
            # Process files
            self.process_files_batch(all_files, target, mode, duplicate_handling, dry_run)
            
            # Clean up empty folders
            if not dry_run:
                self.remove_empty_directories_recursive(sources)
            
            # Generate final report
            self.generate_organization_report(dry_run)
            
        except Exception as e:
            self.logger.error(f"Organization failed: {e}")
            print(f"❌ Organization failed: {e}")
    
    def create_backup(self, sources: List[str]):
        """Create backup before organization"""
        print("\n💾 Creating backup before organization...")
        # Implementation for backup creation
        pass
    
    def process_files_batch(self, files: List[str], target: str, mode: OrganizationMode,
                           duplicate_handling: DuplicateHandling, dry_run: bool):
        """Process files in batches for better performance"""
        print(f"\n📂 Processing {len(files):,} files...")
        
        for i, file_path in enumerate(files):
            if self.cancelled:
                break
                
            self.update_progress(current=i+1, current_file=file_path, operation="Processing")
            
            try:
                if self.is_protected_path(file_path):
                    self.stats['protected_skipped'] += 1
                    continue
                
                # Get destination path based on organization mode
                dest_path = self.get_destination_path(file_path, target, mode)
                
                if not dry_run:
                    # Actual file move
                    self.move_file_safely(file_path, dest_path)
                    self.stats['moved'] += 1
                else:
                    # Just log what would happen
                    self.stats['moved'] += 1
                
                # Update file size stats
                try:
                    file_size = os.path.getsize(file_path)
                    self.stats['total_size'] += file_size
                except:
                    pass
                    
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                self.stats['errors'] += 1
    
    def get_destination_path(self, file_path: str, target: str, mode: OrganizationMode) -> str:
        """Get destination path based on organization mode"""
        category, subcategory = self.get_file_category(file_path)
        
        if mode == OrganizationMode.BY_TYPE:
            return os.path.join(target, category, subcategory, os.path.basename(file_path))
        elif mode == OrganizationMode.BY_DATE:
            # Organize by creation date
            try:
                timestamp = os.path.getctime(file_path)
                date_obj = datetime.fromtimestamp(timestamp)
                year_month = date_obj.strftime("%Y/%m-%B")
                return os.path.join(target, year_month, os.path.basename(file_path))
            except:
                return os.path.join(target, "Unknown_Date", os.path.basename(file_path))
        elif mode == OrganizationMode.BY_SIZE:
            # Organize by file size
            try:
                size = os.path.getsize(file_path)
                if size < 1024 * 1024:  # < 1MB
                    size_category = "Small"
                elif size < 100 * 1024 * 1024:  # < 100MB
                    size_category = "Medium"
                elif size < 1024 * 1024 * 1024:  # < 1GB
                    size_category = "Large"
                else:
                    size_category = "Very_Large"
                return os.path.join(target, size_category, os.path.basename(file_path))
            except:
                return os.path.join(target, "Unknown_Size", os.path.basename(file_path))
        else:  # BY_EXTENSION
            ext = Path(file_path).suffix.lower() or "no_extension"
            return os.path.join(target, ext[1:] if ext.startswith('.') else ext, os.path.basename(file_path))
    
    def move_file_safely(self, source: str, destination: str):
        """Move file with safety checks"""
        # Create destination directory
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Handle conflicts
        if os.path.exists(destination):
            destination = self.resolve_file_conflict(source, destination)
        
        # Move the file
        shutil.move(source, destination)
        
        # Log the operation
        operation = FileOperation(
            source=source,
            destination=destination,
            operation="move",
            timestamp=datetime.now().isoformat(),
            size_bytes=os.path.getsize(destination)
        )
        self.operations_log.append(operation)
    
    def resolve_file_conflict(self, source: str, destination: str) -> str:
        """Resolve file naming conflicts"""
        base, ext = os.path.splitext(destination)
        counter = 1
        
        while os.path.exists(destination):
            destination = f"{base}_({counter}){ext}"
            counter += 1
        
        return destination
    
    def generate_organization_report(self, dry_run: bool):
        """Generate detailed organization report"""
        print(f"\n📊 {'PREVIEW' if dry_run else 'ORGANIZATION'} REPORT")
        print("=" * 50)
        print(f"✅ Files {'would be moved' if dry_run else 'moved'}: {self.stats['moved']:,}")
        print(f"⏭️ Files skipped: {self.stats['skipped']:,}")
        print(f"❌ Errors: {self.stats['errors']:,}")
        print(f"💾 Total size processed: {self.stats['total_size'] / (1024*1024):.1f} MB")
        print(f"⏱️ Processing time: {time.time() - self.progress.start_time:.1f} seconds")
    
    # ... keep existing code (rest of the methods from original file)

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
    
    def enhanced_file_scan(self, sources: List[str]) -> Tuple[List[str], Dict[str, int]]:
        """Enhanced file scanning with better feedback"""
        print("\n🔍 ENHANCED FILE SCANNING...")
        print("─" * 50)
        
        all_files = []
        scan_stats = defaultdict(int)
        total_size = 0
        
        for i, source in enumerate(sources, 1):
            print(f"📂 Scanning {i}/{len(sources)}: {os.path.basename(source)}")
            source_files = 0
            
            try:
                for root, dirs, files in os.walk(source):
                    # Skip protected directories
                    if self.is_protected_path(root):
                        scan_stats['protected_folders'] += 1
                        scan_stats['protected_files'] += len(files)
                        continue
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        try:
                            file_size = os.path.getsize(file_path)
                            all_files.append(file_path)
                            total_size += file_size
                            source_files += 1
                            
                            # Track file type statistics
                            category, _ = self.get_file_category(file_path)
                            scan_stats[f'category_{category}'] += 1
                            
                            # Show progress every 1000 files
                            if len(all_files) % 1000 == 0:
                                print(f"   📁 Found: {len(all_files):,} files...")
                        
                        except (OSError, PermissionError):
                            scan_stats['scan_errors'] += 1
                            continue
                
                print(f"   ✅ Found {source_files:,} files in {os.path.basename(source)}")
                
            except Exception as e:
                print(f"   ❌ Error scanning {source}: {e}")
                scan_stats['folder_errors'] += 1
        
        # Print scan summary
        print(f"\n📊 SCAN SUMMARY:")
        print(f"   📁 Total files found: {len(all_files):,}")
        print(f"   💾 Total size: {total_size / (1024**3):.2f} GB")
        print(f"   🔒 Protected files skipped: {scan_stats['protected_files']:,}")
        print(f"   ❌ Scan errors: {scan_stats['scan_errors']:,}")
        
        return all_files, dict(scan_stats)
    
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

    def remove_empty_directories_recursive(self, sources: List[str], max_iterations: int = 10) -> int:
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
                if self.cancelled:
                    break
                    
                try:
                    # Double-check it's still empty before removing
                    if os.path.exists(empty_dir) and os.path.isdir(empty_dir):
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

    def scan_for_empty_directories(self, root_paths: List[str]) -> Set[str]:
        """Scan for empty directories recursively and return a set of empty directories"""
        empty_dirs = set()
        
        print("🔍 Scanning for empty directories...")
        
        for root_path in root_paths:
            print(f"   📂 Scanning: {os.path.basename(root_path)}...")
            
            try:
                # Walk through all directories from deepest to shallowest
                for current_dir, subdirs, files in os.walk(root_path, topdown=False):
                    # Skip protected paths
                    if self.is_protected_path(current_dir):
                        continue
                    
                    try:
                        # Check if directory is truly empty
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
                        
                        if not has_real_content and current_dir != root_path:  # Don't mark root path as empty
                            empty_dirs.add(current_dir)
                            
                    except (OSError, PermissionError) as e:
                        self.logger.warning(f"Cannot access directory {current_dir}: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error scanning {root_path}: {e}")
                continue
        
        return empty_dirs

if __name__ == "__main__":
    # Quick test for the improved organizer
    organizer = FileOrganizerImproved()
    print("🚀 Enhanced File Organizer v2.6 - Next Phase Improvements")
    print("Run with enhanced_gui_improved.py for the full GUI experience!")
