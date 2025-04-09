#!/usr/bin/env python3
"""
User Profile Management Tool

This script provides a command-line interface for managing your AI assistant's 
user profile data. It allows you to view, edit, and manage personal information,
preferences, and conversation notes.
"""

import os
import sys
import argparse
from rich.console import Console

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from modules.user_profile_editor import UserProfileEditor
except ImportError:
    print("Error: Could not import UserProfileEditor module.")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)

console = Console()

def main():
    """Main entry point for the user profile tool."""
    parser = argparse.ArgumentParser(
        description="Manage your AI assistant's user profile data"
    )
    parser.add_argument(
        "--data-dir", 
        help="Specify a custom data directory (default: ~/my_AI)"
    )
    parser.add_argument(
        "--backup", 
        action="store_true", 
        help="Create a backup of your user data"
    )
    parser.add_argument(
        "--restore",
        help="Restore user data from a backup file"
    )
    
    args = parser.parse_args()
    
    # Initialize the profile editor
    editor = UserProfileEditor(data_dir=args.data_dir)
    
    if args.backup:
        backup_profile(editor)
    elif args.restore:
        restore_profile(editor, args.restore)
    else:
        # Run the interactive editor
        editor.run()

def backup_profile(editor):
    """Create a backup of the user profile data."""
    import json
    import datetime
    
    user_data = editor.load_user_data()
    
    # Create a backup file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"user_data_backup_{timestamp}.json"
    
    try:
        with open(backup_file, "w") as f:
            json.dump(user_data, f, indent=4)
        console.print(f"[green]Backup created successfully: {backup_file}[/green]")
    except Exception as e:
        console.print(f"[red]Error creating backup: {e}[/red]")

def restore_profile(editor, backup_file):
    """Restore user profile data from a backup file."""
    import json
    
    if not os.path.exists(backup_file):
        console.print(f"[red]Error: Backup file not found: {backup_file}[/red]")
        return
    
    try:
        with open(backup_file, "r") as f:
            user_data = json.load(f)
        
        # Validate the user data structure
        required_keys = ["name", "preferences"]
        if not all(key in user_data for key in required_keys):
            console.print(f"[red]Error: Invalid backup file format. Missing required keys.[/red]")
            return
        
        # Save the restored data
        if editor.save_user_data(user_data):
            console.print(f"[green]User profile restored successfully from {backup_file}[/green]")
        else:
            console.print(f"[red]Failed to save restored user data.[/red]")
            
    except json.JSONDecodeError:
        console.print(f"[red]Error: Invalid JSON format in backup file.[/red]")
    except Exception as e:
        console.print(f"[red]Error restoring backup: {e}[/red]")

if __name__ == "__main__":
    main() 