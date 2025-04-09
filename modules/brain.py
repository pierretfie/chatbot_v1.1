from llama_cpp import Llama
import time
from typing import List, Dict, Optional
from rich.console import Console
import os
import sys
import contextlib
import warnings
import random
import json
import re
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.prompt_template import PromptTemplate
from modules.user_manager import UserManager
try:
    from modules.user_profile_editor import UserProfileEditor
    PROFILE_EDITOR_AVAILABLE = True
except ImportError:
    PROFILE_EDITOR_AVAILABLE = False
from config import Config

console = Console()

class Brain:
    """Handles the chatbot's reasoning and response generation."""
    
    @staticmethod
    @contextlib.contextmanager
    def suppress_stderr():
        """Context manager to suppress stderr output"""
        with open(os.devnull, 'w') as devnull:
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stderr = old_stderr

    def __init__(self, model_path: str = Config.TINYLLAMA_PATH, 
                 context_size: int = Config.CONTEXT_SIZE):
        self.model_path = model_path
        self.context_size = context_size
        self.llm = None
        self.prompt_template = PromptTemplate()
        self.conversation_history: List[Dict[str, str]] = []
        self.chatty_expressions = self._load_chatty_expressions()
        self.user_manager = UserManager()
        self._initialize_model()    
    
    def _load_chatty_expressions(self) -> Dict[str, List[str]]:
        """Load chatty expressions from JSON file."""
        try:
            expressions_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'chatty_expressions.json'
            )
            with open(expressions_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load chatty expressions: {e}[/yellow]")
            # Fallback expressions if file can't be loaded
            return {
                "interjections": ["Well, ", "Hmm, ", "Oh! "],
                "thinking": ["Let me think... "],
                "enthusiasm": ["I'm excited to tell you that "]
            }
    
    def _initialize_model(self):
        """Initialize the TinyLlama model."""
        try:
            os.environ['LLAMA_CPP_LOG_LEVEL'] = '-1'
            console.print("[blue]Initializing TinyLlama model...[/blue]")
            
            # Suppress warnings during model initialization
            with self.suppress_stderr():
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    self.llm = Llama(
                        model_path=self.model_path,
                        n_ctx=self.context_size,
                        n_threads=Config.N_THREADS,
                        n_gpu_layers=-1
                    )
            
            console.print("[green]Model initialized successfully![/green]")
        except Exception as e:
            error_msg = Config.ERROR_MESSAGES['initialization_error'].format(error=str(e))
            console.print(f"[red]{error_msg}[/red]")
            raise
    
    def _check_for_user_commands(self, user_input: str) -> Optional[str]:
        """Check for special user commands related to user management."""
        user_input_lower = user_input.lower()
        
        # Command to edit profile
        if "edit my profile" in user_input_lower or "edit profile" in user_input_lower or "manage my profile" in user_input_lower:
            if PROFILE_EDITOR_AVAILABLE:
                console.print("[yellow]Launching profile editor...[/yellow]")
                editor = UserProfileEditor()
                editor.run()
                
                # Reload user data after editing
                self.user_manager.user_data = self.user_manager._load_user_data()
                
                return "I've closed the profile editor. Your changes have been saved!"
            else:
                return "I'm sorry, the profile editor is not available. Please make sure the user_profile_editor.py module is installed."
        
        # Detect birth date information in various formats
        if any(phrase in user_input_lower for phrase in ["born in", "born on", "birthday is", "date of birth", "my birthday", "birth date"]):
            # Try multiple date extraction patterns
            
            # Pattern 1: YYYY-MM-DD format
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', user_input)
            
            # Pattern 2: Day Month Year (26th December 2007)
            if not date_match:
                day_month_year = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', user_input, re.IGNORECASE)
                if day_month_year:
                    day = int(day_month_year.group(1))
                    month_name = day_month_year.group(2).lower()
                    year = int(day_month_year.group(3))
                    
                    # Convert month name to number
                    month_map = {
                        'january': 1, 'jan': 1,
                        'february': 2, 'feb': 2,
                        'march': 3, 'mar': 3,
                        'april': 4, 'apr': 4,
                        'may': 5, 'may': 5,
                        'june': 6, 'jun': 6,
                        'july': 7, 'jul': 7,
                        'august': 8, 'aug': 8,
                        'september': 9, 'sep': 9,
                        'october': 10, 'oct': 10,
                        'november': 11, 'nov': 11,
                        'december': 12, 'dec': 12
                    }
                    month = month_map.get(month_name.lower())
                    if month and 1 <= day <= 31:
                        try:
                            # Validate this is a real date
                            from datetime import date
                            date(year, month, day)
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            date_match = type('obj', (object,), {'group': lambda self, x: date_str})()
                        except ValueError:
                            pass
            
            # Pattern 3: Month Day Year (December 26, 2007)
            if not date_match:
                month_day_year = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', user_input, re.IGNORECASE)
                if month_day_year:
                    month_name = month_day_year.group(1).lower()
                    day = int(month_day_year.group(2))
                    year = int(month_day_year.group(3))
                    
                    # Convert month name to number
                    month_map = {
                        'january': 1, 'jan': 1,
                        'february': 2, 'feb': 2,
                        'march': 3, 'mar': 3,
                        'april': 4, 'apr': 4,
                        'may': 5, 'may': 5,
                        'june': 6, 'jun': 6,
                        'july': 7, 'jul': 7,
                        'august': 8, 'aug': 8,
                        'september': 9, 'sep': 9,
                        'october': 10, 'oct': 10,
                        'november': 11, 'nov': 11,
                        'december': 12, 'dec': 12
                    }
                    month = month_map.get(month_name.lower())
                    if month and 1 <= day <= 31:
                        try:
                            # Validate this is a real date
                            from datetime import date
                            date(year, month, day)
                            date_str = f"{year}-{month:02d}-{day:02d}"
                            date_match = type('obj', (object,), {'group': lambda self, x: date_str})()
                        except ValueError:
                            pass
                            
            # Pattern 4: Day/Month/Year or Month/Day/Year
            if not date_match:
                numeric_date = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})', user_input)
                if numeric_date:
                    # This is ambiguous - could be MM/DD/YYYY or DD/MM/YYYY
                    # We'll try both and validate
                    n1 = int(numeric_date.group(1))
                    n2 = int(numeric_date.group(2))
                    n3 = int(numeric_date.group(3))
                    
                    # If n3 is 2 digits, assume it's the year + 2000 if < 50, else + 1900
                    if n3 < 100:
                        n3 = n3 + 2000 if n3 < 50 else n3 + 1900
                    
                    # Try as MM/DD/YYYY
                    try:
                        from datetime import date
                        date(n3, n1, n2)  # Month, day, year
                        date_str = f"{n3}-{n1:02d}-{n2:02d}"
                        date_match = type('obj', (object,), {'group': lambda self, x: date_str})()
                    except ValueError:
                        # Try as DD/MM/YYYY
                        try:
                            date(n3, n2, n1)  # Day, month, year
                            date_str = f"{n3}-{n2:02d}-{n1:02d}"
                            date_match = type('obj', (object,), {'group': lambda self, x: date_str})()
                        except ValueError:
                            pass
            
            if date_match:
                birthday = date_match.group(1)
                if self.user_manager.set_user_birthday(birthday):
                    # Convert back to natural date for the response
                    try:
                        from datetime import date
                        birth_date = date.fromisoformat(birthday)
                        # Format with full month name and ordinal day
                        day = birth_date.day
                        day_suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                        natural_date = f"{day}{day_suffix} {birth_date.strftime('%B')} {birth_date.year}"
                        return f"I've saved your birthday as {natural_date}. I'll be sure to remember it!"
                    except:
                        return f"I've saved your birthday as {birthday}. I'll be sure to remember it!"
                else:
                    return "I couldn't process that date format. Please use a standard date format like YYYY-MM-DD or a natural format like 'December 26, 2007'."
            else:
                return "I couldn't quite understand your birth date. Please try again with a format like 'December 26, 2007' or 'YYYY-MM-DD'."
        
        # Detect pet information
        pet_match = re.search(r'(?:i have|my) (?:a|an)?\s+pet\s+(?:is|its|it\'s|called|named)?\s+(?:name\s+is\s+)?([A-Za-z]+)', user_input_lower)
        if pet_match:
            pet_name = pet_match.group(1).strip().capitalize()
            
            # Try to determine pet type
            pet_type = "pet"  # Default
            for animal in ["dog", "cat", "fish", "bird", "hamster", "rabbit", "guinea pig", "turtle", "lizard", "snake"]:
                if animal in user_input_lower:
                    pet_type = animal
                    break
            
            # Save to user data
            user_data = self.user_manager.user_data
            personal_info = user_data.get("personal_info", {})
            family = personal_info.get("family", {})
            family[pet_type] = pet_name
            personal_info["family"] = family
            user_data["personal_info"] = personal_info
            self.user_manager.user_data = user_data
            self.user_manager.save_user_data()
            
            return f"I'll remember that your {pet_type}'s name is {pet_name}!"
        
        # Command to set birthday
        if "my birthday is" in user_input_lower or "set my birthday" in user_input_lower:
            # Try to extract date in format YYYY-MM-DD
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', user_input)
            if date_match:
                birthday = date_match.group(1)
                if self.user_manager.set_user_birthday(birthday):
                    return f"Great! I've set your birthday to {birthday}. I'll be sure to remember it!"
                else:
                    return "I couldn't understand that date format. Please use YYYY-MM-DD format (e.g., 1990-01-15)."
            else:
                return "I didn't catch your birthday. Please specify it in YYYY-MM-DD format (e.g., my birthday is 1990-01-15)."
        
        # Command to set name
        elif "my name is" in user_input_lower or "call me" in user_input_lower:
            # Extract name after "my name is" or "call me"
            name_match = re.search(r'(?:my name is|call me)\s+([A-Za-z\s]+)', user_input_lower)
            if name_match:
                name = name_match.group(1).strip().title()
                self.user_manager.set_user_name(name)
                return f"Nice to meet you, {name}! I'll remember that."
            else:
                return "I didn't catch your name. Could you please repeat it?"
        
        # Command to add a preference
        elif "i like" in user_input_lower or "i prefer" in user_input_lower:
            # Extract category and preference
            category_match = re.search(r'i (?:like|prefer) (.*?) (?:for|as) (my|an?) (.*?)(?:\.|\,|$)', user_input_lower)
            if category_match:
                preference = category_match.group(1).strip()
                category = category_match.group(3).strip()
                self.user_manager.add_user_preference(category, preference)
                return f"I'll remember that you like {preference} for {category}!"
            else:
                # Process general interest or hobby
                preference = user_input.replace("i like", "").replace("I like", "").replace("i prefer", "").replace("I prefer", "").strip()
                if preference:
                    # Check if it might be a hobby
                    hobby_indicators = ["doing", "playing", "reading", "watching", "collecting", "making", "building", "studying"]
                    is_hobby = any(indicator in user_input_lower for indicator in hobby_indicators) or len(preference.split()) <= 3
                    
                    if is_hobby:
                        # Add as hobby
                        user_data = self.user_manager.user_data
                        personal_info = user_data.get("personal_info", {})
                        hobbies = personal_info.get("hobbies", [])
                        if preference not in hobbies:
                            hobbies.append(preference)
                        personal_info["hobbies"] = hobbies
                        user_data["personal_info"] = personal_info
                        self.user_manager.user_data = user_data
                        self.user_manager.save_user_data()
                        return f"I'll remember that you enjoy {preference}!"
                    else:
                        # Add as general preference
                        self.user_manager.add_user_preference("general", preference)
                        return f"I'll remember that you like {preference}!"
        
        # Command to show user data
        elif "show my data" in user_input_lower or "show my profile" in user_input_lower or "view my profile" in user_input_lower:
            user_data = self.user_manager.user_data
            
            # Format response
            response = "Here's the information I have about you:\n\n"
            
            # Name
            response += f"Name: {user_data.get('name', 'Not set')}\n"
            
            # Birthday
            birthday = user_data.get('birthday')
            if birthday:
                response += f"Birthday: {birthday}\n"
            
            # Preferences
            preferences = user_data.get('preferences', {})
            if preferences:
                response += "\nPreferences:\n"
                for category, value in preferences.items():
                    response += f"- {category.capitalize()}: {value}\n"
            
            # Notes (only showing count)
            notes = user_data.get('notes', [])
            if notes:
                response += f"\nI have {len(notes)} notes about our conversations.\n"
            
            response += "\nYou can edit this information by saying 'edit my profile'."
            return response
        
        # Not a user command
        return None
            
    def _validate_response(self, response_text: str) -> str:
        """Validate response to prevent training data leaks and ensure quality."""
        # Check for conversation example patterns
        example_patterns = [
            r'^[A-Z]:\s',  # Matches "A: " or "B: " at start
            r'^User:\s',   # Matches "User: " at start
            r'^Assistant:\s',  # Matches "Assistant: " at start
            r'^Human:\s',  # Matches "Human: " at start
            r'^AI:\s',     # Matches "AI: " at start
            r'^Q:\s',      # Matches "Q: " at start
            r'^A:\s',      # Matches "A: " at start
            r'^Example\s', # Matches "Example " at start
            r'^Sample\s',  # Matches "Sample " at start
            r'^Training\s' # Matches "Training " at start
        ]
        
        # Check for multiple lines with letter prefixes (A:, B:, etc.)
        lines = response_text.split('\n')
        if len(lines) > 1:
            letter_prefix_count = sum(1 for line in lines if re.match(r'^[A-Z]:\s', line.strip()))
            if letter_prefix_count > 1:
                return "I apologize, but I need to rephrase my response to be more natural."
        
        # Check for any example patterns
        for pattern in example_patterns:
            if re.search(pattern, response_text, re.MULTILINE):
                return "I apologize, but I need to rephrase my response to be more natural."
        
        return response_text

    def _check_for_goodbye(self, user_input: str) -> Optional[str]:
        """Check if the input contains a goodbye message and generate a natural response."""
        goodbye_phrases = [
            # Direct goodbyes
            "goodbye", "bye", "farewell", "see you", "take care", 
            "until next time", "gotta go", "have to go", "need to go",
            "let me go", "time to go", "i'm leaving", "i'll go now",
            "was nice chatting", "nice talking", "nice chatting",
            "good night", "good evening", "good afternoon",
            
            # More natural variations
            "i should get going", "i better get going", "i ought to go",
            "i need to head out", "i should head out", "i better head out",
            "i need to run", "i should run", "i better run",
            "i need to get going", "i should get going", "i better get going",
            "i need to leave", "i should leave", "i better leave",
            "i need to be going", "i should be going", "i better be going",
            "i need to take off", "i should take off", "i better take off",
            "i need to bounce", "i should bounce", "i better bounce",
            "i need to jet", "i should jet", "i better jet",
            "i need to split", "i should split", "i better split",
            
            # Appreciation phrases
            "was great talking", "was great chatting", "was lovely talking",
            "was lovely chatting", "was wonderful talking", "was wonderful chatting",
            "was nice talking", "was nice chatting", "was good talking",
            "was good chatting", "was fun talking", "was fun chatting",
            
            # Time-based goodbyes
            "good morning", "good afternoon", "good evening", "good night",
            "have a good day", "have a great day", "have a wonderful day",
            "have a nice day", "have a good one", "have a great one",
            "have a wonderful one", "have a nice one",
            
            # Future meeting phrases
            "see you later", "see you soon", "see you around", "see you next time",
            "catch you later", "catch you soon", "catch you around",
            "talk to you later", "talk to you soon", "talk to you next time",
            "speak to you later", "speak to you soon", "speak to you next time"
        ]
        
        user_input_lower = user_input.lower().strip()
        
        # Check for goodbye phrases
        for phrase in goodbye_phrases:
            if phrase in user_input_lower:
                # Get user's name for personalization
                user_data = self.user_manager.user_data
                name = user_data.get("name", "")
                
                # Create a prompt for generating a natural goodbye
                goodbye_prompt = f"""Generate a natural and warm goodbye message. The user's name is {name if name else 'there'}. 
The user said: "{user_input}"
Generate a single, natural-sounding goodbye message that:
1. Acknowledges the conversation
2. Expresses appreciation
3. Wishes them well
4. Sounds natural and conversational
5. Is appropriate for the time of day if mentioned
6. Uses their name if available
7. Is between 1-2 sentences

Response:"""
                
                # Generate response with controlled parameters
                with self.suppress_stderr():
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore')
                        response = self.llm(
                            goodbye_prompt,
                            max_tokens=100,
                            stop=["\n\n", "User:", "Assistant:"],
                            echo=False,
                            temperature=0.7,  # Lower temperature for more controlled output
                            top_p=0.9,
                            frequency_penalty=0.2,
                            presence_penalty=0.2
                        )
                
                # Extract and clean the response
                response_text = response['choices'][0]['text'].strip()
                
                # Remove any potential role markers or unwanted prefixes
                response_text = re.sub(r'^(Assistant|User|A|B):\s*', '', response_text)
                
                # Ensure the response ends with appropriate punctuation
                if not response_text.endswith(('.', '!', '?')):
                    response_text += '!'
                
                return response_text
        
        return None

    def generate_response(self, user_input: str, max_tokens: int = Config.MAX_TOKENS) -> tuple:
        """Generate a response to user input."""
        try:
            # Validate input
            if not user_input or not user_input.strip():
                return "I notice you sent an empty message. I'm here to chat - feel free to share your thoughts!", 0
                
            # Check for very short or incomplete messages
            if len(user_input.strip()) < 3:
                return "I see you're trying to say something, but it seems quite short. Could you elaborate a bit more?", 0
                
            # Check for trailing ellipsis or incomplete sentences
            if user_input.strip().endswith('...') or user_input.strip().endswith('..'):
                return "I notice you ended your message with '...'. Would you like to complete your thought?", 0
                
            # Check for goodbye messages
            goodbye_response = self._check_for_goodbye(user_input)
            if goodbye_response:
                self.user_manager.update_last_interaction()
                return goodbye_response, 0
                
            # First, check for user management commands
            command_response = self._check_for_user_commands(user_input)
            if command_response:
                self.user_manager.update_last_interaction()
                return command_response, 0
            
            # Check if this is a greeting and provide time since last conversation
            greeting_response = self._check_for_greeting(user_input)
            if greeting_response:
                self.user_manager.update_last_interaction()
                return greeting_response, 0
                
            # Check for birthday reminder
            birthday_reminder = self.user_manager.get_birthday_reminder()
            
            # Get user information for context
            user_info = self._get_relevant_user_info(user_input)
            
            # Get the full prompt
            system_prompt = self.prompt_template.get_system_prompt()
            full_prompt = self.prompt_template.get_chat_prompt(
                system_prompt,
                self.conversation_history,
                user_input,
                user_info
            )
            
            # Get conversation style preferences
            conv_style = self.user_manager.user_data.get("conversation_style", {})
            formality = conv_style.get("formality", "casual")
            detail_level = conv_style.get("detail_level", "balanced")
            humor_level = conv_style.get("humor", "moderate")
            
            # Adjust generation parameters based on conversation style
            temperature = 0.8
            if formality == "formal" or formality == "professional":
                temperature = 0.7
            elif formality == "friendly":
                temperature = 0.9
                
            # Adjust max tokens based on detail level
            detail_multiplier = {
                "minimal": 0.7,
                "balanced": 1.0,
                "detailed": 1.3,
                "comprehensive": 1.5
            }.get(detail_level, 1.0)
            adjusted_max_tokens = int(max_tokens * detail_multiplier)
            
            # Generate response
            start_time = time.time()
            with self.suppress_stderr():
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    response = self.llm(
                    full_prompt,
                    max_tokens=adjusted_max_tokens,
                    stop=["User:", "\n\n"],
                    echo=False,
                    temperature=temperature,
                    top_p=0.9,
                    frequency_penalty=0.2,
                    presence_penalty=0.2
            )
            generation_time = time.time() - start_time
            
            # Extract the response text
            response_text = response['choices'][0]['text'].strip()
            
            # Validate response to prevent training data leaks
            response_text = self._validate_response(response_text)
            
            # Add chatty expressions based on content, context, and humor level
            response_text = self._add_chatty_expressions(response_text, user_input, humor_level)
            
            # Add birthday reminder if applicable
            if birthday_reminder:
                response_text = f"{response_text}\n\n{birthday_reminder}"
            
            # Track interaction
            self._track_interaction(user_input, response_text)
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep conversation history manageable
            if len(self.conversation_history) > Config.MAX_HISTORY:
                self.conversation_history = self.conversation_history[-Config.MAX_HISTORY:]
            
            # Update the last meeting time
            self.user_manager.update_last_interaction()
            
            return response_text, generation_time
            
        except Exception as e:
            error_msg = Config.ERROR_MESSAGES['model_error']
            console.print(f"[red]{error_msg}[/red]")
            return self.prompt_template.get_error_prompt("model_error", str(e)), 0
            
    def _check_for_greeting(self, user_input: str) -> Optional[str]:
        """Check if the input is a greeting and respond with time elapsed since last conversation."""
        greetings = [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon", 
            "good evening", "howdy", "what's up", "sup", "yo", "hola", "bonjour"
        ]
        
        user_input_lower = user_input.lower().strip()
        
        # Check if this is a simple greeting (e.g. just "hi" or "hello")
        is_greeting = False
        for greeting in greetings:
            if user_input_lower == greeting or user_input_lower.startswith(f"{greeting} ") or user_input_lower.startswith(f"{greeting}!"):
                is_greeting = True
                break
        
        if is_greeting:
            # Get user's name and last interaction time
            user_data = self.user_manager.user_data
            name = user_data.get("name", "")
            last_interaction = user_data.get("last_interaction", None)
            
            # Build greeting response
            greeting = random.choice(["Hi", "Hello", "Hey", "Greetings"])
            response = greeting
            
            # Add user's name if available
            if name:
                response += f" {name}"
            
            # Add time since last interaction if available
            if last_interaction:
                try:
                    last_time = datetime.fromisoformat(last_interaction)
                    now = datetime.now()
                    time_diff = now - last_time
                    
                    # Format time difference based on how long it's been
                    days = time_diff.days
                    hours, remainder = divmod(time_diff.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    time_str = ""
                    if days > 0:
                        time_str += f"{days} day{'s' if days != 1 else ''}"
                        if hours > 0:
                            time_str += f" {hours} hour{'s' if hours != 1 else ''}"
                        time_str += " since we last talked"
                    elif hours > 0:
                        time_str += f"{hours} hour{'s' if hours != 1 else ''}"
                        if minutes > 0:
                            time_str += f" and {minutes} minute{'s' if minutes != 1 else ''}"
                        time_str += " since we last talked"
                    elif minutes > 0:
                        time_str += f"{minutes} minute{'s' if minutes != 1 else ''} since we last talked"
                    else:
                        # If less than a minute, don't mention time
                        time_str = ""
                    
                    if time_str:
                        response += f"! It's been {time_str}."
                    else:
                        response += "!"
                except:
                    response += "!"
            else:
                response += "!"
            
            # Add a follow-up question or statement
            follow_ups = [
                "How are you today?",
                "How have you been?",
                "What's new with you?",
                "How's your day going?",
                "How has your day been so far?",
                "What brings you here today?",
                "It's good to see you again!",
                "I'm happy to chat with you again!",
                "What can I help you with today?"
            ]
            
            response += f" {random.choice(follow_ups)}"
            
            return response
            
        return None
        
    def _get_relevant_user_info(self, user_input: str) -> str:
        """Get relevant user information based on the input query."""
        user_data = self.user_manager.user_data
        user_info = []
        
        # Always include name
        name = user_data.get("name", "User")
        user_info.append(f"Name: {name}")
        
        # Get keywords from user input
        input_lower = user_input.lower()
        
        # Check for topics that might trigger personal information
        if any(word in input_lower for word in ["hobby", "hobbies", "interest", "interests", "like to do"]):
            hobbies = user_data.get("personal_info", {}).get("hobbies", [])
            if hobbies:
                user_info.append(f"Hobbies: {', '.join(hobbies)}")
                
        if any(word in input_lower for word in ["family", "spouse", "partner", "wife", "husband", "children", "kids"]):
            family = user_data.get("personal_info", {}).get("family", {})
            if family:
                family_info = [f"{relation}: {name}" for relation, name in family.items()]
                user_info.append(f"Family: {', '.join(family_info)}")
                
        if any(word in input_lower for word in ["favorite", "like", "prefer", "love"]):
            # Check for specific categories
            categories = []
            if "movie" in input_lower or "film" in input_lower:
                categories.append("movie")
            if "music" in input_lower or "song" in input_lower:
                categories.append("music")
            if "food" in input_lower or "eat" in input_lower:
                categories.append("food")
            if "book" in input_lower or "read" in input_lower:
                categories.append("book")
                
            favorites = user_data.get("personal_info", {}).get("favorite_things", {})
            if favorites:
                if categories:
                    # Add only relevant favorites
                    for category in categories:
                        if category in favorites:
                            user_info.append(f"Favorite {category}: {favorites[category]}")
                else:
                    # Add all favorites if no specific category
                    for category, item in favorites.items():
                        user_info.append(f"Favorite {category}: {item}")
                        
        if any(word in input_lower for word in ["job", "work", "career", "profession"]):
            occupation = user_data.get("personal_info", {}).get("occupation")
            if occupation:
                user_info.append(f"Occupation: {occupation}")
                
        if any(word in input_lower for word in ["live", "location", "city", "country", "from"]):
            location = user_data.get("personal_info", {}).get("location")
            if location:
                user_info.append(f"Location: {location}")
        
        # Return formatted user info or empty string if none
        return "\n".join(user_info) if user_info else ""
        
    def _add_chatty_expressions(self, response_text: str, user_input: str, humor_level: str = "moderate") -> str:
        """Add appropriate chatty expressions based on context and humor preferences."""
        # Don't modify if response already starts with a chatty expression
        all_expressions = []
        for category in self.chatty_expressions.values():
            all_expressions.extend(category)
            
        if response_text.startswith(tuple(all_expressions)):
            return response_text
            
        # Determine expression category based on user input and response
        category = self._determine_expression_category(user_input, response_text)
        
        # Adjust probability based on humor level
        humor_probability = {
            "none": 0.05,
            "subtle": 0.2,
            "moderate": 0.3,
            "high": 0.5
        }.get(humor_level, 0.3)
        
        # Add expression based on adjusted probability
        if random.random() < humor_probability and category in self.chatty_expressions:
            expression = random.choice(self.chatty_expressions[category])
            # Lowercase first letter if needed
            if expression.endswith(" ") and len(response_text) > 0:
                response_text = expression + response_text[0].lower() + response_text[1:]
            else:
                response_text = expression + response_text
                
        # Adjust follow-up question probability based on humor level
        followup_probability = {
            "none": 0.0,
            "subtle": 0.05,
            "moderate": 0.1,
            "high": 0.2
        }.get(humor_level, 0.1)
        
        # Add follow-up question at the end based on adjusted probability
        if random.random() < followup_probability and "follow_ups" in self.chatty_expressions:
            if not any(q in response_text for q in ["?", "What do you think"]):
                follow_up = random.choice(self.chatty_expressions["follow_ups"])
                response_text = response_text + " " + follow_up
                
        return response_text
        
    def _track_interaction(self, user_input: str, response_text: str):
        """Track interaction details for improved personalization."""
        # Extract potential topics from the conversation
        combined_text = f"{user_input} {response_text}".lower()
        
        # Get existing interaction history
        user_data = self.user_manager.user_data
        history = user_data.get("interaction_history", {
            "first_interaction": user_data.get("interaction_history", {}).get("first_interaction", datetime.now().isoformat()),
            "session_count": user_data.get("interaction_history", {}).get("session_count", 0) + 1,
            "topics_discussed": user_data.get("interaction_history", {}).get("topics_discussed", [])
        })
        
        # Simple topic extraction - could be enhanced with NLP in a production system
        potential_topics = [
            "technology", "science", "art", "music", "movies", "books", 
            "food", "travel", "health", "sports", "education", "work",
            "family", "hobbies", "politics", "news", "history", "philosophy"
        ]
        
        # Check for topics in the conversation
        topics = history.get("topics_discussed", [])
        for topic in potential_topics:
            if topic in combined_text and topic not in topics:
                topics.append(topic)
                
        # Keep only the most recent 20 topics
        history["topics_discussed"] = topics[-20:]
        
        # Update session count
        history["session_count"] = history.get("session_count", 0)
        
        # Save back to user data
        user_data["interaction_history"] = history
        self.user_manager.user_data = user_data
        self.user_manager.save_user_data()
        
    def get_greeting(self) -> str:
        """Get a personalized greeting with time since last meeting."""
        return self.user_manager.get_greeting()
    
    def _determine_expression_category(self, user_input: str, response_text: str) -> str:
        """Choose an appropriate expression category based on context."""
        user_input = user_input.lower()
        response_text = response_text.lower()
        
        # Check for greetings
        if any(word in user_input for word in ["hi", "hello", "hey", "greetings"]):
            return "greetings"
            
        # Check for questions that require thinking
        if "?" in user_input and any(word in user_input for word in ["how", "why", "what", "when", "where"]):
            return "thinking"
            
        # Check for content that might be surprising or interesting
        if any(word in response_text for word in ["surprisingly", "unexpectedly", "contrary"]):
            return "surprise"
            
        # Check for opinions or explanations
        if any(word in response_text for word in ["believe", "think", "opinion", "recommend"]):
            return "opinions"
            
        # Check for enthusiasm opportunities
        if any(word in response_text for word in ["great", "excellent", "amazing", "fantastic"]):
            return "enthusiasm"
            
        # Default to interjections or random selection
        categories = list(self.chatty_expressions.keys())
        return random.choice(categories) if categories else "interjections"
            
    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        
    def get_history(self) -> List[Dict[str, str]]:
        """Get the current conversation history."""
        return self.conversation_history.copy()
        
    def __del__(self):
        """Cleanup when the brain is destroyed."""
        if self.llm:
            del self.llm 

if __name__ == "__main__":
    pass 