"""
Chatbot modules package.

This package contains the core modules for the chatbot application:
- brain: Core language model and response generation
- config: Configuration settings
- gpu_manager: GPU resource monitoring
- resource_manager: System resource monitoring
- tts_module: Text-to-speech functionality using TTS library
- user_profile: User profile management
"""

# Make key modules available at the package level for easier imports
from modules.config import Config
from modules.tts_module import synthesize_and_play 