
#!/usr/bin/env python3
"""
Enhanced File Organizer GUI - Modern Comprehensive Interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
from datetime import datetime
from pathlib import Path
import json

# Import your organizer classes
try:
    from enhanced_file_organizer import FileOrganizer, OrganizationMode, DuplicateHandling
except ImportError:
    print("❌ Cannot import FileOrganizer. Make sure enhanced_file_organizer.py is in the same directory.")
    sys.exit(1)

class ModernFileOrganizerGUI:
    def __init__(self):
        self.organizer = FileOrganizer()
        self.root = tk.Tk()
        self.setup_main_window()
        
        # Data storage
        self.source_folders = []
        self.operation_queue = queue.Queue()
        self.is_processing = False
        
        # Variables
        self.target_folder = tk.StringVar()
        self.junk_threshold = tk.IntVar(value=10)
        self.organization_mode = tk.StringVar(value="BY_TYPE")
        self.duplicate_handling = tk.StringVar(value="RENAME")
        self.dry_run_mode = tk.BooleanVar(value=True)
        
        # Checklist variables
        self.check_duplicates = tk.BooleanVar(value=True)
        self.check_empty_folders = tk.BooleanVar(value=True)
        self.check_junk_files = tk.BooleanVar(value=True)
        self.create_backups = tk.BooleanVar(value=False)
        self.verify_moves = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.start_queue_checker()
    
    def setup_main_window(self):
        """Setup the main window"""
        self.root.title("🗂️ Enhanced File Organizer Pro")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)
        
        # Configure ttk style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TButton', background='#4CAF50')
        style.configure('Warning.TButton', background='#FF9800')
        style.configure('Danger.TButton', background='#f44336')
    
    def setup_ui(self):
        """Setup the complete user interface"""
        # Main container with scrollable frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🗂️ Enhanced File Organizer Pro", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for organized sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Setup tabs
        self.setup_organize_tab()
        self.setup_checklist_tab()
        self.setup_advanced_tab()
        self.setup_log_tab()
        
        # Status bar
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var, length=200)
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def setup_organize_tab(self):
        """Setup the main organization tab"""
        organize_frame = ttk.Frame(self.notebook)
        self.notebook.add(organize_frame, text="📁 Organize Files")
        
        # Source folders section
        source_group = ttk.LabelFrame(organize_frame, text="📂 Source Folders", padding="10")
        source_group.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Source listbox with scrollbar
        source_container = ttk.Frame(source_group)
        source_container.pack(fill=tk.BOTH, expand=True)
        
        self.source_listbox = tk.Listbox(source_container, height=4, font=('Arial', 9))
        source_scrollbar = ttk.Scrollbar(source_container, orient=tk.VERTICAL, command=self.source_listbox.yview)
        self.source_listbox.configure(yscrollcommand=source_scrollbar.set)
        
        self.source_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        source_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Source buttons
        source_btn_frame = ttk.Frame(source_group)
        source_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(source_btn_frame, text="➕ Add Folder", command=self.add_source_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(source_btn_frame, text="➖ Remove", command=self.remove_source_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(source_btn_frame, text="🗑️ Clear All", command=self.clear_source_folders).pack(side=tk.LEFT, padx=5)
        
        # Target folder section
        target_group = ttk.LabelFrame(organize_frame, text="🎯 Target Folder", padding="10")
        target_group.pack(fill=tk.X, padx=10, pady=5)
        
        target_frame = ttk.Frame(target_group)
        target_frame.pack(fill=tk.X)
        
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_folder, font=('Arial', 9))
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(target_frame, text="📁 Browse", command=self.select_target_folder).pack(side=tk.RIGHT)
        
        # Organization settings section
        settings_group = ttk.LabelFrame(organize_frame, text="⚙️ Organization Settings", padding="10")
        settings_group.pack(fill=tk.X, padx=10, pady=5)
        
        # Organization mode with radio buttons
        mode_frame = ttk.Frame(settings_group)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="📋 Organization Mode:", style='Header.TLabel').pack(anchor=tk.W)
        
        mode_radio_frame = ttk.Frame(mode_frame)
        mode_radio_frame.pack(anchor=tk.W, pady=(5, 0))
        
        modes = [
            ("BY_TYPE", "🗂️ By File Type (Recommended)"),
            ("BY_DATE", "📅 By Date Created"),
            ("BY_SIZE", "📏 By File Size"),
            ("BY_EXTENSION", "📄 By File Extension")
        ]
        
        for value, text in modes:
            ttk.Radiobutton(mode_radio_frame, text=text, variable=self.organization_mode, 
                           value=value).pack(anchor=tk.W, pady=1)
        
        # Duplicate handling with radio buttons
        dup_frame = ttk.Frame(settings_group)
        dup_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dup_frame, text="🔄 Duplicate Handling:", style='Header.TLabel').pack(anchor=tk.W)
        
        dup_radio_frame = ttk.Frame(dup_frame)
        dup_radio_frame.pack(anchor=tk.W, pady=(5, 0))
        
        duplicates = [
            ("RENAME", "✏️ Rename duplicates (Safe)"),
            ("SKIP", "⏭️ Skip duplicates"),
            ("REPLACE", "🔄 Replace existing"),
            ("MERGE_DUPLICATES", "🔗 Merge duplicate folders")
        ]
        
        for value, text in duplicates:
            ttk.Radiobutton(dup_radio_frame, text=text, variable=self.duplicate_handling, 
                           value=value).pack(anchor=tk.W, pady=1)
        
        # Junk threshold
        junk_frame = ttk.Frame(settings_group)
        junk_frame.pack(fill=tk.X)
        
        ttk.Label(junk_frame, text="🗑️ Junk File Threshold (KB):").pack(side=tk.LEFT)
        ttk.Spinbox(junk_frame, from_=0, to=1000, textvariable=self.junk_threshold, 
                   width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Dry run mode
        ttk.Checkbutton(settings_group, text="🔍 Dry Run Mode (Preview Only - Recommended)", 
                       variable=self.dry_run_mode).pack(anchor=tk.W, pady=(10, 0))
        
        # Action buttons
        action_frame = ttk.Frame(organize_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Left side - Preview
        ttk.Button(action_frame, text="🔍 Preview Organization", 
                  command=self.preview_organization, style='Success.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side - Execute
        ttk.Button(action_frame, text="🚀 Start Organization", 
                  command=self.start_organization, style='Warning.TButton').pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(action_frame, text="🛑 Stop", command=self.stop_operation, 
                  style='Danger.TButton').pack(side=tk.RIGHT)
    
    def setup_checklist_tab(self):
        """Setup the checklist tab"""
        checklist_frame = ttk.Frame(self.notebook)
        self.notebook.add(checklist_frame, text="✅ Pre-Flight Checklist")
        
        # Instructions
        instruction_frame = ttk.LabelFrame(checklist_frame, text="📋 Pre-Organization Checklist", padding="15")
        instruction_frame.pack(fill=tk.X, padx=10, pady=10)
        
        instructions = """
✨ Complete this checklist before organizing your files:

🔍 PREPARATION:
• Ensure you have enough disk space in the target folder
• Close any programs that might be using files in source folders
• Consider creating a backup of important files first

⚙️ VERIFICATION:
• Check that source and target folders are correctly selected
• Verify organization mode and duplicate handling settings
• Enable dry run mode for first-time organization

🛡️ SAFETY:
• Review the file types that will be organized
• Check for any protected or system folders in source paths
• Ensure network drives are properly connected (if applicable)
        """
        
        ttk.Label(instruction_frame, text=instructions, font=('Arial', 9)).pack(anchor=tk.W)
        
        # Checklist items
        checklist_group = ttk.LabelFrame(checklist_frame, text="✅ Safety Checks", padding="15")
        checklist_group.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        checks = [
            (self.check_duplicates, "🔍 Check for duplicates during organization"),
            (self.check_empty_folders, "📁 Remove empty folders after organization"),
            (self.check_junk_files, "🗑️ Identify and handle junk files"),
            (self.create_backups, "💾 Create backup before organization (Recommended)"),
            (self.verify_moves, "✅ Verify file integrity after moves")
        ]
        
        for var, text in checks:
            ttk.Checkbutton(checklist_group, text=text, variable=var).pack(anchor=tk.W, pady=3)
        
        # Quick actions
        quick_frame = ttk.LabelFrame(checklist_frame, text="🚀 Quick Actions", padding="15")
        quick_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        quick_btn_frame = ttk.Frame(quick_frame)
        quick_btn_frame.pack(fill=tk.X)
        
        ttk.Button(quick_btn_frame, text="📊 Show File Types", 
                  command=self.show_supported_types).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(quick_btn_frame, text="🔍 Analyze Duplicates", 
                  command=self.analyze_duplicates).pack(side=tk.LEFT, padx=10)
        ttk.Button(quick_btn_frame, text="↩️ Undo Last Operation", 
                  command=self.undo_last_operation).pack(side=tk.LEFT, padx=10)
        ttk.Button(quick_btn_frame, text="🧹 Cleanup Empty Folders", 
                  command=self.cleanup_empty_folders).pack(side=tk.LEFT, padx=10)
    
    def setup_advanced_tab(self):
        """Setup advanced settings tab"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="🔧 Advanced Settings")
        
        # Configuration management
        config_group = ttk.LabelFrame(advanced_frame, text="💾 Configuration Management", padding="15")
        config_group.pack(fill=tk.X, padx=10, pady=10)
        
        config_btn_frame = ttk.Frame(config_group)
        config_btn_frame.pack(fill=tk.X)
        
        ttk.Button(config_btn_frame, text="💾 Save Configuration", 
                  command=self.save_configuration).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(config_btn_frame, text="📁 Load Configuration", 
                  command=self.load_configuration).pack(side=tk.LEFT, padx=10)
        ttk.Button(config_btn_frame, text="🔄 Reset to Defaults", 
                  command=self.reset_to_defaults).pack(side=tk.LEFT, padx=10)
        
        # Statistics
        stats_group = ttk.LabelFrame(advanced_frame, text="📊 Statistics & Info", padding="15")
        stats_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.stats_text = scrolledtext.ScrolledText(stats_group, height=15, font=('Consolas', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Update stats
        self.update_statistics()
    
    def setup_log_tab(self):
        """Setup the logging tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="📝 Activity Log")
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(log_controls, text="🗑️ Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_controls, text="💾 Save Log", command=self.save_log).pack(side=tk.LEFT, padx=10)
        ttk.Button(log_controls, text="🔄 Refresh", command=self.refresh_log).pack(side=tk.LEFT, padx=10)
        
        # Log display
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_container, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial log message
        self.log("🚀 Enhanced File Organizer Pro started")
        self.log("📋 Complete the checklist before organizing files")
    
    def add_source_folder(self):
        """Add a source folder"""
        folder = filedialog.askdirectory(title="Select Source Folder")
        if folder and folder not in self.source_folders:
            self.source_folders.append(folder)
            self.source_listbox.insert(tk.END, folder)
            self.log(f"📁 Added source folder: {folder}")
            self.update_status(f"Added source folder: {os.path.basename(folder)}")
    
    def remove_source_folder(self):
        """Remove selected source folder"""
        selection = self.source_listbox.curselection()
        if selection:
            index = selection[0]
            folder = self.source_folders.pop(index)
            self.source_listbox.delete(index)
            self.log(f"➖ Removed source folder: {folder}")
    
    def clear_source_folders(self):
        """Clear all source folders"""
        if self.source_folders and messagebox.askyesno("Confirm", "Clear all source folders?"):
            self.source_folders.clear()
            self.source_listbox.delete(0, tk.END)
            self.log("🗑️ Cleared all source folders")
    
    def select_target_folder(self):
        """Select target folder"""
        folder = filedialog.askdirectory(title="Select Target Organization Folder")
        if folder:
            self.target_folder.set(folder)
            self.log(f"🎯 Set target folder: {folder}")
    
    def preview_organization(self):
        """Preview the organization"""
        if not self.validate_inputs():
            return
        
        self.start_processing("🔍 Analyzing files for preview...")
        
        def preview_worker():
            try:
                mode = OrganizationMode[self.organization_mode.get()]
                preview = self.organizer.preview_organization(
                    self.source_folders,
                    self.target_folder.get(),
                    self.junk_threshold.get(),
                    mode
                )
                self.operation_queue.put(("preview_complete", preview))
            except Exception as e:
                self.operation_queue.put(("error", str(e)))
        
        threading.Thread(target=preview_worker, daemon=True).start()
    
    def start_organization(self):
        """Start the file organization"""
        if not self.validate_inputs():
            return
        
        # Confirmation dialog
        confirm_msg = f"""
🗂️ ORGANIZATION SUMMARY:

📁 Source folders: {len(self.source_folders)}
🎯 Target folder: {os.path.basename(self.target_folder.get())}
📋 Mode: {self.organization_mode.get().replace('_', ' ').title()}
🔄 Duplicates: {self.duplicate_handling.get().replace('_', ' ').title()}
🔍 Dry Run: {'Yes' if self.dry_run_mode.get() else 'No'}

Continue with organization?
        """
        
        if not messagebox.askyesno("Confirm Organization", confirm_msg):
            return
        
        action = "🔍 Previewing" if self.dry_run_mode.get() else "🚀 Organizing"
        self.start_processing(f"{action} files...")
        
        def organize_worker():
            try:
                mode = OrganizationMode[self.organization_mode.get()]
                dup_handling = DuplicateHandling[self.duplicate_handling.get()]
                
                self.organizer.organize_files(
                    self.source_folders,
                    self.target_folder.get(),
                    self.junk_threshold.get(),
                    mode,
                    dup_handling,
                    dry_run=self.dry_run_mode.get()
                )
                
                self.operation_queue.put(("organize_complete", self.organizer.stats))
            except Exception as e:
                self.operation_queue.put(("error", str(e)))
        
        threading.Thread(target=organize_worker, daemon=True).start()
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.source_folders:
            messagebox.showerror("❌ Error", "Please add at least one source folder.")
            return False
        
        if not self.target_folder.get().strip():
            messagebox.showerror("❌ Error", "Please select a target folder.")
            return False
        
        # Check if target is same as source
        target_path = os.path.abspath(self.target_folder.get())
        for source in self.source_folders:
            if os.path.abspath(source) == target_path:
                messagebox.showerror("❌ Error", "Target folder cannot be the same as source folder.")
                return False
        
        return True
    
    def start_processing(self, message):
        """Start processing mode"""
        self.is_processing = True
        self.update_status(message)
        self.progress_bar.configure(mode='indeterminate')
        self.progress_bar.start()
        self.log(f"🔄 {message}")
    
    def stop_processing(self):
        """Stop processing mode"""
        self.is_processing = False
        self.progress_bar.stop()
        self.progress_bar.configure(mode='determinate')
        self.progress_var.set(0)
        self.update_status("Ready")
    
    def stop_operation(self):
        """Stop current operation"""
        if self.is_processing:
            if messagebox.askyesno("Confirm Stop", "⚠️ Stop the current operation?\nThis may leave files in an inconsistent state."):
                self.stop_processing()
                self.log("🛑 Operation stopped by user")
    
    def show_supported_types(self):
        """Show supported file types"""
        self.organizer.show_supported_types()
        self.log("📊 Displayed supported file types")
    
    def analyze_duplicates(self):
        """Analyze duplicates"""
        if not self.source_folders:
            messagebox.showinfo("ℹ️ Info", "Please add source folders first.")
            return
        
        self.log("🔍 Starting duplicate analysis...")
        # This would call your duplicate analysis method
        
    def undo_last_operation(self):
        """Undo last operation"""
        try:
            self.organizer.undo_last_organization()
            self.log("↩️ Undid last organization")
            messagebox.showinfo("✅ Success", "Last organization has been undone.")
        except Exception as e:
            self.log(f"❌ Error undoing operation: {e}")
            messagebox.showerror("❌ Error", f"Could not undo operation:\n{e}")
    
    def cleanup_empty_folders(self):
        """Cleanup empty folders"""
        if not self.source_folders:
            messagebox.showinfo("ℹ️ Info", "Please add source folders first.")
            return
        
        if messagebox.askyesno("Confirm Cleanup", "🧹 Remove empty folders from source directories?"):
            try:
                removed = self.organizer.remove_empty_directories_recursive(self.source_folders)
                self.log(f"🧹 Removed {removed} empty folders")
                messagebox.showinfo("✅ Success", f"Removed {removed} empty folders.")
            except Exception as e:
                self.log(f"❌ Error during cleanup: {e}")
                messagebox.showerror("❌ Error", f"Cleanup failed:\n{e}")
    
    def save_configuration(self):
        """Save current configuration"""
        file_path = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                config = {
                    'source_folders': self.source_folders,
                    'target_folder': self.target_folder.get(),
                    'junk_threshold': self.junk_threshold.get(),
                    'organization_mode': self.organization_mode.get(),
                    'duplicate_handling': self.duplicate_handling.get(),
                    'dry_run_mode': self.dry_run_mode.get(),
                    'check_duplicates': self.check_duplicates.get(),
                    'check_empty_folders': self.check_empty_folders.get(),
                    'check_junk_files': self.check_junk_files.get(),
                    'create_backups': self.create_backups.get(),
                    'verify_moves': self.verify_moves.get(),
                    'saved_at': datetime.now().isoformat()
                }
                
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.log(f"💾 Configuration saved: {file_path}")
                messagebox.showinfo("✅ Success", "Configuration saved successfully!")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to save configuration:\n{e}")
    
    def load_configuration(self):
        """Load configuration"""
        file_path = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Load settings
                if 'source_folders' in config:
                    self.source_folders = config['source_folders']
                    self.source_listbox.delete(0, tk.END)
                    for folder in self.source_folders:
                        self.source_listbox.insert(tk.END, folder)
                
                if 'target_folder' in config:
                    self.target_folder.set(config['target_folder'])
                
                # Load other settings
                for key, var in [
                    ('junk_threshold', self.junk_threshold),
                    ('organization_mode', self.organization_mode),
                    ('duplicate_handling', self.duplicate_handling),
                    ('dry_run_mode', self.dry_run_mode),
                    ('check_duplicates', self.check_duplicates),
                    ('check_empty_folders', self.check_empty_folders),
                    ('check_junk_files', self.check_junk_files),
                    ('create_backups', self.create_backups),
                    ('verify_moves', self.verify_moves)
                ]:
                    if key in config:
                        var.set(config[key])
                
                self.log(f"📁 Configuration loaded: {file_path}")
                messagebox.showinfo("✅ Success", "Configuration loaded successfully!")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to load configuration:\n{e}")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Confirm Reset", "🔄 Reset all settings to defaults?"):
            self.junk_threshold.set(10)
            self.organization_mode.set("BY_TYPE")
            self.duplicate_handling.set("RENAME")
            self.dry_run_mode.set(True)
            self.check_duplicates.set(True)
            self.check_empty_folders.set(True)
            self.check_junk_files.set(True)
            self.create_backups.set(False)
            self.verify_moves.set(True)
            self.log("🔄 Reset all settings to defaults")
    
    def update_statistics(self):
        """Update statistics display"""
        stats = f"""
📊 SYSTEM INFORMATION:
==========================================

🗂️ File Organizer Status: Ready
📁 Source Folders: {len(self.source_folders)}
🎯 Target Folder: {self.target_folder.get() or 'Not selected'}

⚙️ CURRENT SETTINGS:
==========================================
📋 Organization Mode: {self.organization_mode.get().replace('_', ' ').title()}
🔄 Duplicate Handling: {self.duplicate_handling.get().replace('_', ' ').title()}
🗑️ Junk Threshold: {self.junk_threshold.get()} KB
🔍 Dry Run Mode: {'Enabled' if self.dry_run_mode.get() else 'Disabled'}

✅ SAFETY CHECKS:
==========================================
🔍 Check Duplicates: {'✅' if self.check_duplicates.get() else '❌'}
📁 Remove Empty Folders: {'✅' if self.check_empty_folders.get() else '❌'}
🗑️ Handle Junk Files: {'✅' if self.check_junk_files.get() else '❌'}
💾 Create Backups: {'✅' if self.create_backups.get() else '❌'}
✅ Verify Moves: {'✅' if self.verify_moves.get() else '❌'}

📈 SUPPORTED FILE TYPES:
==========================================
Total Categories: {len(self.organizer.config.FILE_MAP)}
        """
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats)
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
        self.log("🗑️ Log cleared")
    
    def save_log(self):
        """Save log to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"💾 Log saved: {file_path}")
                messagebox.showinfo("✅ Success", "Log saved successfully!")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Failed to save log:\n{e}")
    
    def refresh_log(self):
        """Refresh log display"""
        self.log("🔄 Log refreshed")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update()
    
    def start_queue_checker(self):
        """Start checking for background operation results"""
        self.check_operation_queue()
    
    def check_operation_queue(self):
        """Check for messages from background operations"""
        try:
            while True:
                msg_type, data = self.operation_queue.get_nowait()
                
                if msg_type == "preview_complete":
                    self.stop_processing()
                    self.show_preview_results(data)
                elif msg_type == "organize_complete":
                    self.stop_processing()
                    self.show_organization_results(data)
                elif msg_type == "error":
                    self.stop_processing()
                    self.log(f"❌ Error: {data}")
                    messagebox.showerror("❌ Error", f"Operation failed:\n{data}")
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_operation_queue)
    
    def show_preview_results(self, preview):
        """Show preview results"""
        result_window = tk.Toplevel(self.root)
        result_window.title("🔍 Organization Preview")
        result_window.geometry("600x500")
        result_window.transient(self.root)
        
        # Results display
        results_text = scrolledtext.ScrolledText(result_window, font=('Consolas', 10))
        results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format results
        results = f"""
🔍 ORGANIZATION PREVIEW RESULTS
{'=' * 50}

📊 STATISTICS:
   📁 Total files: {preview.get('total_files', 0):,}
   💾 Total size: {preview.get('total_size_mb', 0):.1f} MB
   🗑️ Junk files: {preview.get('junk_files', 0):,}
   🔒 Protected skipped: {preview.get('protected_skipped', 0):,}

📂 FILE CATEGORIES:
        """
        
        if preview.get('categories'):
            for category, count in sorted(preview['categories'].items(), key=lambda x: x[1], reverse=True):
                results += f"   • {category}: {count:,} files\n"
        
        results_text.insert(tk.END, results)
        results_text.config(state=tk.DISABLED)
        
        ttk.Button(result_window, text="Close", command=result_window.destroy).pack(pady=10)
        
        self.log("🔍 Preview results displayed")
    
    def show_organization_results(self, stats):
        """Show organization results"""
        result_msg = f"""
✅ ORGANIZATION COMPLETED!

📊 RESULTS:
   ✅ Files moved: {stats.get('moved', 0):,}
   ⏭️ Files skipped: {stats.get('skipped', 0):,}
   ❌ Errors: {stats.get('errors', 0):,}
   🔄 Duplicates: {stats.get('duplicates', 0):,}
   💾 Size processed: {stats.get('total_size', 0) / (1024*1024):.1f} MB
        """
        
        messagebox.showinfo("✅ Organization Complete", result_msg)
        self.log("✅ Organization completed successfully!")
        self.update_statistics()
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernFileOrganizerGUI()
    app.run()
