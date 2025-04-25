import re
from typing import Optional

class PersonalInfoManager:
    """
    Handles extraction, storage, and retrieval of personal information (e.g., name) from user input.
    Integrates with UserManager for persistent storage.
    """
    def __init__(self, user_manager):
        self.user_manager = user_manager

    def extract_and_store(self, user_input: str) -> Optional[str]:
        """
        Detects personal info statements in user_input and updates user_manager if found.
        Returns a special response if info is stored, else None.
        """
        # Detect self-introduction: "I'm <name>", "I am <name>", "My name is <name>"
        patterns = [
            r"i[' ]?m ([a-zA-Z]+)",
            r"i am ([a-zA-Z]+)",
            r"my name is ([a-zA-Z]+)"
        ]
        for pat in patterns:
            match = re.match(pat, user_input, re.I)
            if match:
                name = match.group(1)
                self.user_manager.user_data['name'] = name
                self.user_manager.save_user_data()
                return f"Hello {name}! How can I help you today?"
        return None

    def handle_profile_query(self, user_input: str) -> Optional[str]:
        """
        Answers profile-related questions (e.g., "What is my name?") from stored data.
        Returns a response if the question matches, else None.
        """
        if "what is my name" in user_input.lower():
            name = self.user_manager.user_data.get('name')
            if name and name.lower() != "user":
                return f"Your name is {name}!"
            else:
                return "I do not know your name. Please tell me!"
        return None

    def inject_profile_context(self, prompt: str) -> str:
        """
        Optionally injects user profile info into the prompt for LLM context.
        """
        name = self.user_manager.user_data.get('name')
        if name and name.lower() != "user":
            profile_context = f"The user's name is {name}.\n"
            return profile_context + prompt
        return prompt
