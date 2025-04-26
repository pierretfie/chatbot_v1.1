import re
from typing import Optional

class PersonalInfoManager:
    """
    Handles extraction, storage, and retrieval of personal information (e.g., name, birthday, location) from user input.
    Integrates with UserManager for persistent storage.
    """
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def extract_and_store(self, user_input: str) -> Optional[str]:
        """
        Detects personal info statements in user_input and updates user_manager if found.
        Returns a special response if info is stored, else None.
        """
        # Patterns for various personal info fields
        patterns = [
            (r"i[' ]?m ([a-zA-Z]+)", 'name'),
            (r"i am ([a-zA-Z]+)", 'name'),
            (r"my name is ([a-zA-Z]+)", 'name'),
            (r"my birthday is ([\\w\\s,]+)", 'birthday'),
            (r"i was born on ([\\w\\s,]+)", 'birthday'),
            (r"i live in ([\\w\\s]+)", 'location'),
            (r"my (?:favourite|favorite) color is ([\\w\\s]+)", 'favorite_color'),
            (r"i like ([\\w\\s]+)", 'preferences'),
            (r"my pronouns are ([\\w\\s]+)", 'pronouns'),
            (r"my occupation is ([\\w\\s]+)", 'occupation'),
            (r"my email is ([^ ]+@[^ ]+)", 'email'),
            (r"my phone number is ([0-9\- +]+)", 'phone'),
        ]
        for pat, field in patterns:
            match = re.match(pat, user_input, re.I)
            if match:
                value = match.group(1).strip()
                self.user_manager.user_data[field] = value
                self.user_manager.save_user_data()
                return f"Got it! I'll remember your {field.replace('_', ' ')} is {value}."
        return None

    def handle_profile_query(self, user_input: str) -> Optional[str]:
        """
        Answers profile-related questions (e.g., "What is my name?", "What is my birthday?") from stored data.
        Returns a response if the question matches, else None.
        """
        queries = {
            "what is my name": "name",
            "what is my birthday": "birthday",
            "when is my birthday": "birthday",
            "where do i live": "location",
            "what is my location": "location",
            "what is my favourite color": "favorite_color",
            "what is my favorite color": "favorite_color",
            "what are my preferences": "preferences",
            "what are my pronouns": "pronouns",
            "what is my occupation": "occupation",
            "what is my email": "email",
            "what is my phone number": "phone",
        }
        for q, field in queries.items():
            if q in user_input.lower():
                value = self.user_manager.user_data.get(field)
                if value:
                    return f"Your {field.replace('_', ' ')} is {value}!"
                else:
                    return f"I don't know your {field.replace('_', ' ')}. Please tell me!"
        return None

    def inject_profile_context(self, prompt: str) -> str:
        """
        Optionally injects user profile info into the prompt for LLM context.
        """
        profile_fields = ['name', 'birthday', 'location', 'favorite_color', 'preferences', 'pronouns', 'occupation', 'email', 'phone']
        info_lines = []
        for field in profile_fields:
            value = self.user_manager.user_data.get(field)
            if value:
                info_lines.append(f"The user's {field.replace('_', ' ')} is {value}.")
        if info_lines:
            profile_context = "\n".join(info_lines) + "\n"
            return profile_context + prompt
        return prompt
