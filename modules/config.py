import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Model paths
    TINYLLAMA_PATH: str = os.path.expanduser('~/tinyllama/tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf')
    #TINYLLAMA_PATH: str = os.path.expanduser('~/Nikita_Agent_model/ggml-nomic-ai-gpt4all-falcon-Q4_1.gguf')

    # Audio settings
    SAMPLE_RATE: str = '22050'
    
    # Model settings
    CONTEXT_SIZE: int = 1024
    MAX_TOKENS: int = 1024
    N_THREADS: int = 8
    
    # Conversation settings
    MAX_HISTORY: int = 10
    
    
    # Resource thresholds
    MEMORY_THRESHOLD: float = 80.0  # percentage
    GPU_MEMORY_THRESHOLD: float = 80.0  # percentage
    CPU_THRESHOLD: float = 80.0  # percentage
    
    # Error messages
    ERROR_MESSAGES = {
        'model_error': "I apologize, but I encountered an error while processing your request.",
        'resource_error': "I'm currently experiencing high resource usage. Please try again in a moment.",
        'file_not_found': "Required file not found: {path}",
        'initialization_error': "Failed to initialize: {error}"
    }
