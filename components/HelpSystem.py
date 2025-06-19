
"""
Help System Component for Enhanced File Organizer
Provides user guidance and instructions
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser
from typing import Dict, List

class HelpSystem:
    """Comprehensive help system for the file organizer"""
    
    def __init__(self, parent):
        self.parent = parent
        self.help_window = None
        
    def show_help(self):
        """Show main help window"""
        if self.help_window and self.help_window.winfo_exists():
            self.help_window.lift()
            return
            
        self.help_window = tk.Toplevel(self.parent)
        self.help_window.title("📖 Help & Instructions")
        self.help_window.geometry("800x600")
        self.help_window.transient(self.parent)
        
        # Create notebook for different help sections
        notebook = ttk.Notebook(self.help_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Getting Started tab
        self.create_getting_started_tab(notebook)
        
        # How to Use tab
        self.create_how_to_use_tab(notebook)
        
        # Organization Modes tab
        self.create_organization_modes_tab(notebook)
        
        # Troubleshooting tab
        self.create_troubleshooting_tab(notebook)
        
        # About tab
        self.create_about_tab(notebook)
        
        # Close button
        close_btn = ttk.Button(self.help_window, text="Close", command=self.help_window.destroy)
        close_btn.pack(pady=10)
    
    def create_getting_started_tab(self, notebook):
        """Create getting started guide"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🚀 Getting Started")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """🚀 GETTING STARTED WITH FILE ORGANIZER

Welcome to Enhanced File Organizer Pro! This guide will help you organize your files quickly and safely.

📋 STEP-BY-STEP GUIDE:

1️⃣ ADD SOURCE FOLDERS
   • Click "➕ Add Folder" to select folders you want to organize
   • Or drag and drop folders directly into the interface
   • You can add multiple folders at once

2️⃣ SELECT TARGET FOLDER
   • Choose where you want your organized files to go
   • This folder will contain all your organized files in neat categories

3️⃣ CHOOSE ORGANIZATION MODE
   • BY_TYPE: Groups files by type (Documents, Images, Videos, etc.)
   • BY_DATE: Organizes by creation date (Year/Month folders)
   • BY_SIZE: Groups by file size (Small, Medium, Large)
   • BY_EXTENSION: Organizes by file extension (.pdf, .jpg, etc.)

4️⃣ CONFIGURE SETTINGS
   • Set junk file threshold (files smaller than this will be moved to Junk folder)
   • Choose how to handle duplicate files
   • Enable "Dry Run Mode" to preview changes first

5️⃣ PREVIEW OR ORGANIZE
   • Click "🔍 Preview Organization" to see what will happen
   • Click "🚀 Start Organization" to begin organizing

🛡️ SAFETY FEATURES:
   ✅ Dry Run Mode - Preview changes before applying
   ✅ Auto Backup - Automatic backup of important files
   ✅ File Verification - Ensures files are moved correctly
   ✅ Operation History - Track all changes made

💡 PRO TIPS:
   • Always use Preview first to check the organization plan
   • Keep backups enabled for safety
   • Start with a small test folder to familiarize yourself
   • Check the Progress Monitor tab for real-time updates
"""
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
    
    def create_how_to_use_tab(self, notebook):
        """Create detailed usage instructions"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📖 How to Use")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """📖 DETAILED USAGE INSTRUCTIONS

🗂️ MAIN INTERFACE FEATURES:

📁 SOURCE FOLDERS SECTION:
   • Add folders containing files you want to organize
   • Use drag-and-drop or click "Add Folder" button
   • Remove unwanted folders with "Remove" button
   • Clear all folders with "Clear All" button

🎯 TARGET FOLDER SECTION:
   • Select destination folder for organized files
   • Browse button opens folder selection dialog
   • Recent button shows previously used folders

⚙️ ORGANIZATION SETTINGS:
   • Organization Mode: How files will be categorized
   • Duplicate Handling: What to do with duplicate files
   • Junk Threshold: Size limit for junk files (in KB)
   • Dry Run Mode: Preview changes without applying them

🚀 ACTION BUTTONS:
   • Preview Organization: Shows what will happen without changes
   • Start Organization: Begins the actual file organization

📊 PROGRESS MONITORING:
   • Real-time statistics during organization
   • Progress bar showing completion percentage
   • Detailed logs of all operations

📜 OPERATION HISTORY:
   • View all past operations with timestamps
   • Export history to text file
   • Clear history when needed

⚙️ ADVANCED FEATURES:
   • Smart Categorization: AI-powered file classification
   • Batch Operations: Analyze duplicates, clean empty folders
   • Configuration Management: Save/load your settings

🔧 KEYBOARD SHORTCUTS:
   • Ctrl+O: Add source folder
   • Ctrl+S: Save configuration
   • Ctrl+L: Load configuration
   • F5: Refresh history
   • Escape: Cancel current operation
   • Ctrl+1-5: Switch between tabs
"""
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
    
    def create_organization_modes_tab(self, notebook):
        """Create organization modes explanation"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📋 Organization Modes")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """📋 ORGANIZATION MODES EXPLAINED

🗂️ BY_TYPE (Recommended for most users)
   Creates folders based on file types:
   • 📄 Documents: .pdf, .doc, .docx, .txt, .rtf, etc.
   • 🖼️ Images: .jpg, .png, .gif, .bmp, .tiff, etc.
   • 🎥 Videos: .mp4, .avi, .mov, .mkv, .wmv, etc.
   • 🎵 Audio: .mp3, .wav, .flac, .aac, .wma, etc.
   • 📦 Archives: .zip, .rar, .7z, .tar, .gz, etc.
   • 💾 Programs: .exe, .msi, .dmg, .deb, .rpm, etc.
   • 🗑️ Junk: Files smaller than threshold

📅 BY_DATE
   Organizes files by creation date:
   • 📁 2024/
     • 📁 01-January/
     • 📁 02-February/
     • 📁 03-March/
   • 📁 2023/
   • 📁 2022/

📏 BY_SIZE
   Groups files by file size:
   • 📁 Small (0-1 MB)
   • 📁 Medium (1-10 MB)
   • 📁 Large (10-100 MB)
   • 📁 Very Large (100+ MB)

🏷️ BY_EXTENSION
   Creates folders for each file extension:
   • 📁 pdf/
   • 📁 jpg/
   • 📁 mp4/
   • 📁 docx/
   • 📁 txt/

🔄 DUPLICATE HANDLING OPTIONS:

   • RENAME: Adds number to duplicate files (file_1.jpg, file_2.jpg)
   • SKIP: Leaves duplicates in original location
   • REPLACE: Overwrites existing files (use with caution!)
   • MERGE_TO_DUPLICATES: Creates special duplicates folder

💡 CHOOSING THE RIGHT MODE:
   • BY_TYPE: Best for general organization and daily use
   • BY_DATE: Great for photos and time-sensitive documents
   • BY_SIZE: Useful for managing storage space
   • BY_EXTENSION: Perfect for developers and technical users
"""
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
    
    def create_troubleshooting_tab(self, notebook):
        """Create troubleshooting guide"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔧 Troubleshooting")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """🔧 TROUBLESHOOTING GUIDE

❌ COMMON ISSUES AND SOLUTIONS:

🚫 "Permission Denied" Errors:
   • Run the program as administrator
   • Check folder permissions
   • Ensure folders are not in use by other programs
   • Avoid system folders (Windows, Program Files)

📁 "Target folder doesn't exist":
   • The program will offer to create the folder
   • Choose a location where you have write permissions
   • Avoid special system directories

🔄 "Operation cancelled" or hangs:
   • Large operations may take time - be patient
   • Check if antivirus is scanning files
   • Ensure sufficient disk space
   • Close other programs that might lock files

💾 "Not enough disk space":
   • Check available space in target folder
   • Clean up unnecessary files first
   • Consider organizing in smaller batches

🗂️ Files not organizing as expected:
   • Check the organization mode setting
   • Verify junk threshold setting
   • Use Preview mode to check before organizing
   • Check operation history for details

📊 Progress bar stuck or not updating:
   • Large folders take time to process
   • Check the details section for current activity
   • Network drives are slower than local drives

🔍 Preview shows no results:
   • Check if source folders contain files
   • Verify folder permissions
   • Ensure files aren't already organized

💡 PERFORMANCE TIPS:
   • Close other programs during large operations
   • Use local drives instead of network drives when possible
   • Organize in smaller batches for better performance
   • Keep antivirus real-time scanning disabled during operations

🛡️ SAFETY RECOMMENDATIONS:
   • Always backup important files before organizing
   • Test with a small folder first
   • Use Dry Run mode for unfamiliar operations
   • Keep operation history for reference

📞 NEED MORE HELP?
   • Check the operation history for detailed logs
   • Export logs for technical support
   • Use Preview mode to understand what will happen
   • Start with small test folders to learn the system
"""
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)
    
    def create_about_tab(self, notebook):
        """Create about information"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="ℹ️ About")
        
        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Segoe UI', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        content = """ℹ️ ABOUT ENHANCED FILE ORGANIZER PRO

🗂️ Enhanced File Organizer Pro v2.6
   Next Phase Improvements - Professional Edition

🎯 PURPOSE:
   This application helps you organize messy folders by automatically
   categorizing and moving files into neat, organized structures.

✨ KEY FEATURES:
   • Multiple organization modes (Type, Date, Size, Extension)
   • Drag & drop interface
   • Real-time progress tracking
   • Automatic backup system
   • Smart duplicate handling
   • Preview mode for safety
   • Operation history tracking
   • Batch operations
   • Recent folders memory
   • Comprehensive help system

🛡️ SAFETY FEATURES:
   • Dry run mode for previewing changes
   • Automatic backups before operations
   • File integrity verification
   • Atomic operations (all-or-nothing)
   • Comprehensive logging
   • Operation cancellation
   • Permission checking

🎨 USER EXPERIENCE:
   • Modern, intuitive interface
   • Keyboard shortcuts
   • Real-time feedback
   • Detailed progress information
   • Comprehensive help system
   • Error recovery options

🔧 TECHNICAL DETAILS:
   • Built with Python and Tkinter
   • Multi-threaded for performance
   • Memory optimized for large folders
   • Cross-platform compatibility
   • Extensive error handling
   • Modular architecture

📜 VERSION HISTORY:
   • v2.6: Next Phase Improvements
     - Modern GUI with enhanced UX
     - Advanced help system
     - Improved performance
     - Better error handling
     - Smart categorization
   
   • v2.5: Enhanced Features
     - Drag & drop support
     - Recent folders
     - Progress monitoring
   
   • v2.0: Major Redesign
     - Complete GUI overhaul
     - Safety improvements
     - Performance optimization

🙏 CREDITS:
   Developed with focus on user experience, safety, and efficiency.
   Thank you for using Enhanced File Organizer Pro!

💡 TIPS FOR BEST RESULTS:
   • Read the Getting Started guide
   • Always use Preview mode first
   • Keep backups enabled
   • Start with small test folders
   • Check the troubleshooting guide if needed
"""
        
        text.insert(tk.END, content)
        text.config(state=tk.DISABLED)

class WelcomeDialog:
    """Welcome dialog for first-time users"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.result = False
        
    def show(self):
        """Show welcome dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("🎉 Welcome to Enhanced File Organizer Pro!")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry(f"+{self.parent.winfo_rootx() + 100}+{self.parent.winfo_rooty() + 50}")
        
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="🎉 Welcome to Enhanced File Organizer Pro!", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Your intelligent file organization assistant", 
                                  font=('Segoe UI', 10))
        subtitle_label.pack()
        
        # Content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Features list
        features_text = """✨ WHAT THIS APP DOES FOR YOU:

🗂️ Automatically organizes messy folders
📁 Groups files by type, date, size, or extension
🛡️ Keeps your files safe with backups and previews
⚡ Handles thousands of files quickly and efficiently
🔍 Shows you exactly what will happen before doing it
📊 Tracks all operations with detailed history

🚀 GETTING STARTED IS EASY:

1️⃣ Add folders you want to organize
2️⃣ Choose where to put organized files
3️⃣ Pick how you want files organized
4️⃣ Click Preview to see what will happen
5️⃣ Click Start to organize your files!

💡 PRO TIP: Always use Preview mode first to see what will happen!"""
        
        features_label = ttk.Label(content_frame, text=features_text, 
                                  font=('Segoe UI', 9), justify=tk.LEFT)
        features_label.pack(anchor=tk.W)
        
        # Checkbox for not showing again
        self.show_again_var = tk.BooleanVar(value=True)
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(checkbox_frame, text="Show this welcome message next time", 
                       variable=self.show_again_var).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="📖 Show Help Guide", 
                  command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🚀 Get Started!", 
                  command=self.close_dialog).pack(side=tk.RIGHT)
        
        # Make dialog modal
        self.dialog.focus_set()
        self.parent.wait_window(self.dialog)
        
        return self.show_again_var.get()
    
    def show_help(self):
        """Show help from welcome dialog"""
        self.close_dialog()
        # The parent will handle showing help
        self.result = "help"
    
    def close_dialog(self):
        """Close the welcome dialog"""
        if self.dialog:
            self.dialog.destroy()
