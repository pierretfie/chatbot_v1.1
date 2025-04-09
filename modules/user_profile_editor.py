import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from datetime import datetime, date
import re
from typing import Dict, Any, List

console = Console()

class UserProfileEditor:
    """Interactive editor for user profile data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the user profile editor."""
        # Set up data directory
        if data_dir is None:
            # Default to a directory in the user's home
            home_dir = os.path.expanduser("~")
            self.data_dir = os.path.join(home_dir, "my_AI")
        else:
            self.data_dir = data_dir
            
        # User DB file path
        self.user_db_file = os.path.join(self.data_dir, "user_data.json")
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                console.print(f"[green]Created data directory: {self.data_dir}[/green]")
            except Exception as e:
                console.print(f"[red]Error creating data directory: {str(e)}[/red]")
                raise
                
        # Create user database if it doesn't exist
        if not os.path.exists(self.user_db_file):
            default_user = {
                "name": "User",
                "birthday": None,
                "personal_info": {
                    "occupation": None,
                    "location": None,
                    "hobbies": [],
                    "family": {},
                    "favorite_things": {}
                },
                "preferences": {},
                "conversation_style": {
                    "formality": "casual",
                    "detail_level": "balanced",
                    "humor": "moderate"
                },
                "notes": [],
                "interaction_history": {
                    "first_interaction": datetime.now().isoformat(),
                    "session_count": 1,
                    "topics_discussed": []
                }
            }
            with open(self.user_db_file, "w") as f:
                json.dump(default_user, f, indent=4)
                
    def load_user_data(self) -> Dict[str, Any]:
        """Load user data from JSON file."""
        try:
            with open(self.user_db_file, "r") as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load user data: {e}[/yellow]")
            return {
                "name": "User",
                "birthday": None,
                "personal_info": {
                    "occupation": None,
                    "location": None,
                    "hobbies": [],
                    "family": {},
                    "favorite_things": {}
                },
                "preferences": {},
                "conversation_style": {
                    "formality": "casual",
                    "detail_level": "balanced",
                    "humor": "moderate"
                },
                "notes": [],
                "interaction_history": {
                    "first_interaction": datetime.now().isoformat(),
                    "session_count": 1,
                    "topics_discussed": []
                }
            }
            
    def save_user_data(self, user_data: Dict[str, Any]) -> bool:
        """Save user data to JSON file."""
        try:
            with open(self.user_db_file, "w") as f:
                json.dump(user_data, f, indent=4)
            return True
        except Exception as e:
            console.print(f"[red]Error saving user data: {e}[/red]")
            return False
    
    def display_user_data(self, user_data: Dict[str, Any]):
        """Display user data in a formatted way."""
        # Basic info panel
        basic_info = Table.grid(padding=1)
        basic_info.add_column(style="cyan", justify="right")
        basic_info.add_column(style="green")
        basic_info.add_row("Name:", user_data.get("name", "Not set"))
        
        # Format birthday if present
        birthday = user_data.get("birthday")
        if birthday:
            try:
                birth_date = date.fromisoformat(birthday)
                # Calculate age
                today = date.today()
                age = today.year - birth_date.year
                if today < date(today.year, birth_date.month, birth_date.day):
                    age -= 1
                birthday_display = f"{birth_date.strftime('%B %d, %Y')} (Age: {age})"
            except:
                birthday_display = birthday
        else:
            birthday_display = "Not set"
            
        basic_info.add_row("Birthday:", birthday_display)
        
        # Add personal info
        personal_info = user_data.get("personal_info", {})
        if personal_info.get("occupation"):
            basic_info.add_row("Occupation:", personal_info["occupation"])
        if personal_info.get("location"):
            basic_info.add_row("Location:", personal_info["location"])
            
        console.print(Panel(basic_info, title="Basic Information", box=box.ROUNDED))
        
        # Display hobbies
        hobbies = personal_info.get("hobbies", [])
        if hobbies:
            hobby_table = Table.grid(padding=1)
            hobby_table.add_column(style="cyan", justify="right")
            hobby_table.add_column(style="green")
            hobby_table.add_row("Hobbies:", ", ".join(hobbies))
            console.print(Panel(hobby_table, title="Hobbies & Interests", box=box.ROUNDED))
        
        # Display favorite things
        favorites = personal_info.get("favorite_things", {})
        if favorites:
            fav_table = Table(title="Favorite Things", box=box.SIMPLE)
            fav_table.add_column("Category", style="cyan")
            fav_table.add_column("Value", style="green")
            
            for key, value in favorites.items():
                fav_table.add_row(key.capitalize(), value)
                
            console.print(fav_table)
        
        # Display family members
        family = personal_info.get("family", {})
        if family:
            family_table = Table(title="Family Members", box=box.SIMPLE)
            family_table.add_column("Relation", style="cyan")
            family_table.add_column("Name", style="green")
            
            for relation, name in family.items():
                family_table.add_row(relation.capitalize(), name)
                
            console.print(family_table)
        
        # Preferences table
        preferences = user_data.get("preferences", {})
        if preferences:
            pref_table = Table(title="Preferences", box=box.SIMPLE)
            pref_table.add_column("Category", style="cyan")
            pref_table.add_column("Value", style="green")
            
            for key, value in preferences.items():
                pref_table.add_row(key.capitalize(), value)
                
            console.print(pref_table)
        else:
            console.print("[dim]No preferences set.[/dim]")
        
        # Conversation style
        style = user_data.get("conversation_style", {})
        if style:
            style_table = Table.grid(padding=1)
            style_table.add_column(style="cyan", justify="right")
            style_table.add_column(style="green")
            
            for key, value in style.items():
                style_table.add_row(f"{key.replace('_', ' ').capitalize()}:", value.capitalize())
                
            console.print(Panel(style_table, title="Conversation Style", box=box.ROUNDED))
            
        # Interaction history
        history = user_data.get("interaction_history", {})
        if history:
            history_table = Table.grid(padding=1)
            history_table.add_column(style="cyan", justify="right")
            history_table.add_column(style="green")
            
            # Format first interaction date
            first = history.get("first_interaction")
            if first:
                try:
                    first_date = datetime.fromisoformat(first)
                    first_str = first_date.strftime("%B %d, %Y")
                    history_table.add_row("First interaction:", first_str)
                except:
                    pass
            
            session_count = history.get("session_count", 0)
            history_table.add_row("Session count:", str(session_count))
            
            topics = history.get("topics_discussed", [])
            if topics:
                history_table.add_row("Topics discussed:", ", ".join(topics[:5]) + ("..." if len(topics) > 5 else ""))
                
            console.print(Panel(history_table, title="Interaction History", box=box.ROUNDED))
            
        # Notes section
        notes = user_data.get("notes", [])
        if notes:
            note_table = Table(title="Notes", box=box.SIMPLE)
            note_table.add_column("Date", style="cyan")
            note_table.add_column("Note", style="green")
            
            # Show only the most recent 5 notes
            for note in notes[-5:]:
                try:
                    timestamp = datetime.fromisoformat(note.get("timestamp", ""))
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = "Unknown"
                    
                note_table.add_row(date_str, note.get("note", "")[:50] + ("..." if len(note.get("note", "")) > 50 else ""))
                
            console.print(note_table)
            if len(notes) > 5:
                console.print(f"[dim]+ {len(notes) - 5} more notes...[/dim]")
        else:
            console.print("[dim]No notes available.[/dim]")
    
    def edit_basic_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit basic user information."""
        console.print("\n[bold]Edit Basic Information[/bold]")
        
        # Edit name
        current_name = user_data.get("name", "User")
        new_name = Prompt.ask("Name", default=current_name)
        user_data["name"] = new_name
        
        # Edit birthday
        current_birthday = user_data.get("birthday", "")
        while True:
            new_birthday = Prompt.ask(
                "Birthday (YYYY-MM-DD)", 
                default=current_birthday if current_birthday else "Skip"
            )
            
            if new_birthday.lower() == "skip":
                break
                
            if re.match(r'^\d{4}-\d{2}-\d{2}$', new_birthday):
                try:
                    # Validate date
                    birth_date = date.fromisoformat(new_birthday)
                    user_data["birthday"] = new_birthday
                    break
                except ValueError:
                    console.print("[red]Invalid date. Please use format YYYY-MM-DD.[/red]")
            else:
                console.print("[red]Invalid format. Please use YYYY-MM-DD.[/red]")
        
        return user_data
    
    def edit_preferences(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit user preferences."""
        preferences = user_data.get("preferences", {})
        
        console.print("\n[bold]Edit Preferences[/bold]")
        console.print("Current preferences:")
        
        if preferences:
            for i, (key, value) in enumerate(preferences.items(), 1):
                console.print(f"{i}. {key}: {value}")
        else:
            console.print("[dim]No preferences set.[/dim]")
        
        # Menu options
        console.print("\nOptions:")
        console.print("1. Add new preference")
        console.print("2. Edit existing preference")
        console.print("3. Delete preference")
        console.print("4. Return to main menu")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            # Add new preference
            key = Prompt.ask("Enter preference category (e.g., 'food', 'color')")
            value = Prompt.ask("Enter preference value")
            preferences[key.lower()] = value
            console.print(f"[green]Added preference: {key} = {value}[/green]")
            
        elif choice == "2" and preferences:
            # Edit existing preference
            keys = list(preferences.keys())
            for i, key in enumerate(keys, 1):
                console.print(f"{i}. {key}: {preferences[key]}")
            
            idx = Prompt.ask(
                "Select preference to edit", 
                choices=[str(i) for i in range(1, len(keys) + 1)],
                default="1"
            )
            key = keys[int(idx) - 1]
            value = Prompt.ask(f"New value for '{key}'", default=preferences[key])
            preferences[key] = value
            console.print(f"[green]Updated preference: {key} = {value}[/green]")
            
        elif choice == "3" and preferences:
            # Delete preference
            keys = list(preferences.keys())
            for i, key in enumerate(keys, 1):
                console.print(f"{i}. {key}: {preferences[key]}")
            
            idx = Prompt.ask(
                "Select preference to delete", 
                choices=[str(i) for i in range(1, len(keys) + 1)],
                default="1"
            )
            key = keys[int(idx) - 1]
            del preferences[key]
            console.print(f"[green]Deleted preference: {key}[/green]")
        
        user_data["preferences"] = preferences
        return user_data
    
    def manage_notes(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user notes."""
        notes = user_data.get("notes", [])
        
        console.print("\n[bold]Manage Notes[/bold]")
        
        if notes:
            for i, note_entry in enumerate(notes, 1):
                try:
                    timestamp = datetime.fromisoformat(note_entry.get("timestamp", ""))
                    date_str = timestamp.strftime("%Y-%m-%d %H:%M")
                except:
                    date_str = "Unknown"
                    
                console.print(f"{i}. [{date_str}] {note_entry.get('note', '')[:50]}...")
        else:
            console.print("[dim]No notes available.[/dim]")
        
        # Menu options
        console.print("\nOptions:")
        console.print("1. Add new note")
        console.print("2. View full note")
        console.print("3. Edit note")
        console.print("4. Delete note")
        console.print("5. Return to main menu")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "1":
            # Add new note
            note_text = Prompt.ask("Enter note")
            notes.append({
                "timestamp": datetime.now().isoformat(),
                "note": note_text
            })
            console.print(f"[green]Added new note[/green]")
            
        elif choice == "2" and notes:
            # View full note
            idx = Prompt.ask(
                "Select note to view",
                choices=[str(i) for i in range(1, len(notes) + 1)],
                default="1"
            )
            note_entry = notes[int(idx) - 1]
            try:
                timestamp = datetime.fromisoformat(note_entry.get("timestamp", ""))
                date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = "Unknown"
                
            console.print(Panel(note_entry.get("note", ""), title=f"Note from {date_str}"))
            
        elif choice == "3" and notes:
            # Edit note
            idx = Prompt.ask(
                "Select note to edit",
                choices=[str(i) for i in range(1, len(notes) + 1)],
                default="1"
            )
            note_idx = int(idx) - 1
            current_note = notes[note_idx].get("note", "")
            new_note = Prompt.ask("Edit note", default=current_note)
            notes[note_idx]["note"] = new_note
            console.print(f"[green]Updated note[/green]")
            
        elif choice == "4" and notes:
            # Delete note
            idx = Prompt.ask(
                "Select note to delete",
                choices=[str(i) for i in range(1, len(notes) + 1)],
                default="1"
            )
            del notes[int(idx) - 1]
            console.print(f"[green]Deleted note[/green]")
        
        user_data["notes"] = notes
        return user_data
    
    def edit_personal_info(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit detailed personal information."""
        personal_info = user_data.get("personal_info", {})
        
        console.print("\n[bold]Edit Personal Information[/bold]")
        console.print("\nOptions:")
        console.print("1. Edit hobbies")
        console.print("2. Edit family members")
        console.print("3. Edit favorite things")
        console.print("4. Return to main menu")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            # Edit hobbies
            hobbies = personal_info.get("hobbies", [])
            console.print("\n[bold]Current Hobbies:[/bold]")
            
            if hobbies:
                for i, hobby in enumerate(hobbies, 1):
                    console.print(f"{i}. {hobby}")
            else:
                console.print("[dim]No hobbies set.[/dim]")
                
            console.print("\nOptions:")
            console.print("1. Add hobby")
            console.print("2. Remove hobby")
            console.print("3. Return")
            
            subchoice = Prompt.ask("Select an option", choices=["1", "2", "3"], default="3")
            
            if subchoice == "1":
                # Add hobby
                new_hobby = Prompt.ask("Enter new hobby")
                if new_hobby and new_hobby not in hobbies:
                    hobbies.append(new_hobby)
                    console.print(f"[green]Added hobby: {new_hobby}[/green]")
                    
            elif subchoice == "2" and hobbies:
                # Remove hobby
                idx = Prompt.ask(
                    "Select hobby to remove",
                    choices=[str(i) for i in range(1, len(hobbies) + 1)],
                    default="1"
                )
                removed = hobbies.pop(int(idx) - 1)
                console.print(f"[green]Removed hobby: {removed}[/green]")
                
            personal_info["hobbies"] = hobbies
                
        elif choice == "2":
            # Edit family members
            family = personal_info.get("family", {})
            console.print("\n[bold]Current Family Members:[/bold]")
            
            if family:
                for i, (relation, name) in enumerate(family.items(), 1):
                    console.print(f"{i}. {relation}: {name}")
            else:
                console.print("[dim]No family members set.[/dim]")
                
            console.print("\nOptions:")
            console.print("1. Add family member")
            console.print("2. Remove family member")
            console.print("3. Return")
            
            subchoice = Prompt.ask("Select an option", choices=["1", "2", "3"], default="3")
            
            if subchoice == "1":
                # Add family member
                relation = Prompt.ask("Enter relation (e.g., 'spouse', 'daughter')")
                name = Prompt.ask("Enter name")
                if relation and name:
                    family[relation.lower()] = name
                    console.print(f"[green]Added family member: {relation} - {name}[/green]")
                    
            elif subchoice == "2" and family:
                # Remove family member
                relations = list(family.keys())
                for i, relation in enumerate(relations, 1):
                    console.print(f"{i}. {relation}: {family[relation]}")
                
                idx = Prompt.ask(
                    "Select family member to remove",
                    choices=[str(i) for i in range(1, len(relations) + 1)],
                    default="1"
                )
                relation = relations[int(idx) - 1]
                removed = family.pop(relation)
                console.print(f"[green]Removed family member: {relation} - {removed}[/green]")
                
            personal_info["family"] = family
            
        elif choice == "3":
            # Edit favorite things
            favorites = personal_info.get("favorite_things", {})
            console.print("\n[bold]Current Favorite Things:[/bold]")
            
            if favorites:
                for i, (category, item) in enumerate(favorites.items(), 1):
                    console.print(f"{i}. {category}: {item}")
            else:
                console.print("[dim]No favorite things set.[/dim]")
                
            console.print("\nOptions:")
            console.print("1. Add favorite thing")
            console.print("2. Remove favorite thing")
            console.print("3. Return")
            
            subchoice = Prompt.ask("Select an option", choices=["1", "2", "3"], default="3")
            
            if subchoice == "1":
                # Add favorite thing
                category = Prompt.ask("Enter category (e.g., 'movie', 'food')")
                item = Prompt.ask("Enter favorite item")
                if category and item:
                    favorites[category.lower()] = item
                    console.print(f"[green]Added favorite: {category} - {item}[/green]")
                    
            elif subchoice == "2" and favorites:
                # Remove favorite thing
                categories = list(favorites.keys())
                for i, category in enumerate(categories, 1):
                    console.print(f"{i}. {category}: {favorites[category]}")
                
                idx = Prompt.ask(
                    "Select favorite to remove",
                    choices=[str(i) for i in range(1, len(categories) + 1)],
                    default="1"
                )
                category = categories[int(idx) - 1]
                removed = favorites.pop(category)
                console.print(f"[green]Removed favorite: {category} - {removed}[/green]")
                
            personal_info["favorite_things"] = favorites
        
        user_data["personal_info"] = personal_info
        return user_data
        
    def edit_conversation_style(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit conversation style preferences."""
        style = user_data.get("conversation_style", {
            "formality": "casual",
            "detail_level": "balanced",
            "humor": "moderate"
        })
        
        console.print("\n[bold]Edit Conversation Style[/bold]")
        
        # Edit formality
        formality_options = ["formal", "casual", "friendly", "professional"]
        current_formality = style.get("formality", "casual")
        console.print("\nFormality level:")
        for i, option in enumerate(formality_options, 1):
            marker = "→" if option == current_formality else " "
            console.print(f"{marker} {i}. {option.capitalize()}")
            
        formality_idx = Prompt.ask(
            "Select formality level",
            choices=[str(i) for i in range(1, len(formality_options) + 1)],
            default=str(formality_options.index(current_formality) + 1)
        )
        style["formality"] = formality_options[int(formality_idx) - 1]
        
        # Edit detail level
        detail_options = ["minimal", "balanced", "detailed", "comprehensive"]
        current_detail = style.get("detail_level", "balanced")
        console.print("\nDetail level:")
        for i, option in enumerate(detail_options, 1):
            marker = "→" if option == current_detail else " "
            console.print(f"{marker} {i}. {option.capitalize()}")
            
        detail_idx = Prompt.ask(
            "Select detail level",
            choices=[str(i) for i in range(1, len(detail_options) + 1)],
            default=str(detail_options.index(current_detail) + 1)
        )
        style["detail_level"] = detail_options[int(detail_idx) - 1]
        
        # Edit humor level
        humor_options = ["none", "subtle", "moderate", "high"]
        current_humor = style.get("humor", "moderate")
        console.print("\nHumor level:")
        for i, option in enumerate(humor_options, 1):
            marker = "→" if option == current_humor else " "
            console.print(f"{marker} {i}. {option.capitalize()}")
            
        humor_idx = Prompt.ask(
            "Select humor level",
            choices=[str(i) for i in range(1, len(humor_options) + 1)],
            default=str(humor_options.index(current_humor) + 1)
        )
        style["humor"] = humor_options[int(humor_idx) - 1]
        
        user_data["conversation_style"] = style
        console.print("[green]Conversation style updated![/green]")
        return user_data
        
    def edit_interaction_history(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit conversation history and topics."""
        history = user_data.get("interaction_history", {
            "first_interaction": datetime.now().isoformat(),
            "session_count": 1,
            "topics_discussed": []
        })
        
        console.print("\n[bold]Edit Interaction History[/bold]")
        
        # Show current topics
        topics = history.get("topics_discussed", [])
        console.print("\n[bold]Topics Discussed:[/bold]")
        
        if topics:
            for i, topic in enumerate(topics, 1):
                console.print(f"{i}. {topic}")
        else:
            console.print("[dim]No topics recorded.[/dim]")
            
        console.print("\nOptions:")
        console.print("1. Add topic")
        console.print("2. Remove topic")
        console.print("3. Reset session count")
        console.print("4. Return to main menu")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            # Add topic
            new_topic = Prompt.ask("Enter new topic discussed")
            if new_topic and new_topic not in topics:
                topics.append(new_topic)
                console.print(f"[green]Added topic: {new_topic}[/green]")
                
        elif choice == "2" and topics:
            # Remove topic
            idx = Prompt.ask(
                "Select topic to remove",
                choices=[str(i) for i in range(1, len(topics) + 1)],
                default="1"
            )
            removed = topics.pop(int(idx) - 1)
            console.print(f"[green]Removed topic: {removed}[/green]")
            
        elif choice == "3":
            # Reset session count
            if Confirm.ask("Are you sure you want to reset the session count?"):
                history["session_count"] = 1
                console.print("[green]Session count reset to 1.[/green]")
        
        history["topics_discussed"] = topics
        user_data["interaction_history"] = history
        return user_data
    
    def run(self):
        """Run the interactive profile editor."""
        console.print(Panel.fit(
            "[bold blue]User Profile Editor[/bold blue]\n\n"
            "This tool allows you to view and edit your AI assistant's knowledge about you.",
            title="Welcome"
        ))
        
        user_data = self.load_user_data()
        
        while True:
            self.display_user_data(user_data)
            
            # Main menu
            console.print("\n[bold]Main Menu[/bold]")
            console.print("1. Edit basic information")
            console.print("2. Edit personal information")
            console.print("3. Edit preferences")
            console.print("4. Edit conversation style")
            console.print("5. Edit interaction history")
            console.print("6. Manage notes")
            console.print("7. Save and exit")
            console.print("8. Exit without saving")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8"], default="7")
            
            if choice == "1":
                user_data = self.edit_basic_info(user_data)
            elif choice == "2":
                user_data = self.edit_personal_info(user_data)
            elif choice == "3":
                user_data = self.edit_preferences(user_data)
            elif choice == "4":
                user_data = self.edit_conversation_style(user_data)
            elif choice == "5":
                user_data = self.edit_interaction_history(user_data)
            elif choice == "6":
                user_data = self.manage_notes(user_data)
            elif choice == "7":
                if self.save_user_data(user_data):
                    console.print("[green]User data saved successfully![/green]")
                else:
                    console.print("[red]Failed to save user data![/red]")
                break
            elif choice == "8":
                if Confirm.ask("Are you sure you want to exit without saving?"):
                    console.print("[yellow]Exiting without saving changes.[/yellow]")
                    break
        
        console.print("Thank you for using the User Profile Editor.")

if __name__ == "__main__":
    editor = UserProfileEditor()
    editor.run()