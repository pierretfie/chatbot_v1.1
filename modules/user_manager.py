import os
import json
from datetime import datetime, date, time
from typing import Dict, Optional, Tuple
from rich.console import Console

console = Console()

class UserManager:
    """Manages user data, tracking meetings, and reminders."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the user manager with a data directory."""
        # Set up data directory
        if data_dir is None:
            # Default to a directory in the user's home
            home_dir = os.path.expanduser("~")
            self.data_dir = os.path.join(home_dir, "my_AI")
        else:
            self.data_dir = data_dir
            
        # Ensure directory exists
        self._ensure_data_dir()
        
        # Path to files
        self.log_file = os.path.join(self.data_dir, "log.txt")
        self.time_file = os.path.join(self.data_dir, "time.txt")
        self.user_db_file = os.path.join(self.data_dir, "user_data.json")
        
        # Initialize files if needed
        self._init_files()
        
        # Load user data
        self.user_data = self._load_user_data()
        
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                console.print(f"[green]Created data directory: {self.data_dir}[/green]")
            except Exception as e:
                console.print(f"[red]Error creating data directory: {str(e)}[/red]")
                raise
    
    def _init_files(self):
        """Initialize necessary files if they don't exist."""
        # Create log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write(f"{date.today()}\n")
                
        # Create time file if it doesn't exist
        if not os.path.exists(self.time_file):
            with open(self.time_file, "w") as f:
                now = datetime.now().time()
                f.write(f"{now.strftime('%H:%M:%S')}\n")
                
        # Create user database if it doesn't exist
        if not os.path.exists(self.user_db_file):
            default_user = {
                "name": "User",
                "birthday": None,
                "preferences": {},
                "notes": []
            }
            with open(self.user_db_file, "w") as f:
                json.dump(default_user, f, indent=4)
    
    def _load_user_data(self) -> Dict:
        """Load user data from JSON file."""
        try:
            with open(self.user_db_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load user data: {e}[/yellow]")
            # Return default user data
            return {
                "name": "User",
                "birthday": None,
                "preferences": {},
                "notes": []
            }
    
    def save_user_data(self):
        """Save user data to JSON file."""
        try:
            with open(self.user_db_file, "w") as f:
                json.dump(self.user_data, f, indent=4)
        except Exception as e:
            console.print(f"[red]Error saving user data: {e}[/red]")
    
    def update_meeting_time(self):
        """Record the current date and time of the meeting."""
        # Update date log
        with open(self.log_file, "a") as f:
            f.write(f"{date.today()}\n")
            
        # Update time log
        with open(self.time_file, "a") as f:
            now = datetime.now().time()
            f.write(f"{now.strftime('%H:%M:%S')}\n")
    
    def get_time_since_last_meeting(self) -> Tuple[int, int, int, int]:
        """
        Calculate time since the last meeting.
        
        Returns:
            Tuple of (days, hours, minutes, seconds)
        """
        # Get current date and time
        today = date.today()
        now = datetime.now().time()
        
        # Get last recorded date
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_date_str = lines[-1].strip()
                    last_date = date.fromisoformat(last_date_str)
                else:
                    last_date = today
        except Exception:
            last_date = today
        
        # Get last recorded time
        try:
            with open(self.time_file, "r") as f:
                lines = f.readlines()
                if lines:
                    last_time_str = lines[-1].strip()
                    last_time = datetime.strptime(last_time_str, "%H:%M:%S").time()
                else:
                    last_time = now
        except Exception:
            last_time = now
        
        # Calculate days difference
        days_since = (today - last_date).days
        
        # Calculate time difference
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        last_seconds = last_time.hour * 3600 + last_time.minute * 60 + last_time.second
        
        if current_seconds < last_seconds:
            # We've crossed a day boundary
            current_seconds += 24 * 3600
        
        seconds_diff = current_seconds - last_seconds
        
        hours = seconds_diff // 3600
        minutes = (seconds_diff % 3600) // 60
        seconds = seconds_diff % 60
        
        return days_since, hours, minutes, seconds
    
    def get_greeting(self) -> str:
        """Get a greeting message with time since last meeting."""
        days, hours, minutes, seconds = self.get_time_since_last_meeting()
        name = self.user_data.get("name", "User")
        
        if days == 0 and hours == 0 and minutes < 5:
            return f"Hello again, {name}! We just spoke a moment ago."
        
        greeting = f"Hello, {name}! It's been "
        
        if days > 0:
            greeting += f"{days} day{'s' if days != 1 else ''}"
            if hours > 0 or minutes > 0:
                greeting += ", "
        
        if hours > 0:
            greeting += f"{hours} hour{'s' if hours != 1 else ''}"
            if minutes > 0:
                greeting += ", "
        
        if minutes > 0 or (days == 0 and hours == 0):
            greeting += f"{minutes} minute{'s' if minutes != 1 else ''}"
        
        greeting += " since we last spoke. It's great to see you again!"
        
        return greeting
    
    def set_user_birthday(self, birthday_str: str) -> bool:
        """
        Set user's birthday.
        
        Args:
            birthday_str: Birthday in format YYYY-MM-DD
        
        Returns:
            Success status
        """
        try:
            # Validate the date format
            birth_date = date.fromisoformat(birthday_str)
            
            # Store in user data
            self.user_data["birthday"] = birthday_str
            self.save_user_data()
            return True
        except ValueError:
            return False
    
    def get_birthday_reminder(self) -> Optional[str]:
        """
        Check if today is the user's birthday or if it's coming up.
        
        Returns:
            Birthday reminder message or None
        """
        birthday = self.user_data.get("birthday")
        if not birthday:
            return None
            
        try:
            birth_date = date.fromisoformat(birthday)
            today = date.today()
            
            # Create a date for this year's birthday
            this_year_birthday = date(today.year, birth_date.month, birth_date.day)
            
            # If the birthday has already passed this year, check for next year
            if this_year_birthday < today:
                this_year_birthday = date(today.year + 1, birth_date.month, birth_date.day)
            
            days_until = (this_year_birthday - today).days
            
            # Calculate age
            age = today.year - birth_date.year
            if today < date(today.year, birth_date.month, birth_date.day):
                age -= 1
            
            # Format message based on days until birthday
            if days_until == 0:
                return f"Today is your birthday! Happy {age}th birthday! 🎂🎉"
            elif days_until <= 7:
                return f"Your birthday is coming up in {days_until} day{'s' if days_until != 1 else ''}! You'll be turning {age+1}. 🎂"
                
            return None
            
        except Exception:
            return None
    
    def set_user_name(self, name: str):
        """Set the user's name."""
        self.user_data["name"] = name
        self.save_user_data()
    
    def get_user_name(self) -> str:
        """Get the user's name."""
        return self.user_data.get("name", "User")
    
    def add_user_preference(self, key: str, value: str):
        """Add a user preference."""
        self.user_data.setdefault("preferences", {})[key] = value
        self.save_user_data()
    
    def get_user_preference(self, key: str) -> Optional[str]:
        """Get a user preference."""
        return self.user_data.get("preferences", {}).get(key)
    
    def add_note(self, note: str):
        """Add a note about the user."""
        timestamp = datetime.now().isoformat()
        self.user_data.setdefault("notes", []).append({
            "timestamp": timestamp,
            "note": note
        })
        self.save_user_data()
    
    def get_notes(self) -> list:
        """Get all notes about the user."""
        return self.user_data.get("notes", [])
    
    def update_last_interaction(self):
        """Update the timestamp of the last interaction with the user."""
        # Store current timestamp in ISO format in user data
        self.user_data["last_interaction"] = datetime.now().isoformat()
        self.save_user_data()
        
        # Also update the meeting time logs
        self.update_meeting_time()


if __name__ == "__main__":
    # Simple test
    user_manager = UserManager()
    print(user_manager.get_greeting())
    print(user_manager.get_birthday_reminder()) 