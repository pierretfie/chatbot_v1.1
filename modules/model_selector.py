import os
from rich.console import Console
from rich.prompt import Prompt
from modules.gemini_client import GeminiClient
from modules.brain import Brain

console = Console()

class ModelSelector:
    """
    Handles user selection and initialization of response generation backend (local or Gemini).
    """
    def __init__(self):
        self.llm = None
        self.gemini_client = None
        self.gpu_manager = None
        self.backend = None

    def select_and_initialize(self):
        choices = ["Local Model (on-device)", "Gemini API (cloud)"]
        console.print("[bold cyan]Select response generation backend:[/bold cyan]")
        for i, c in enumerate(choices, 1):
            console.print(f"  {i}. {c}")
        choice = Prompt.ask(f"Choose backend [1-{len(choices)}] (default: 1)", default="1")
        try:
            idx = int(choice) - 1
        except Exception:
            idx = 0
        self.backend = "local" if idx == 0 else "gemini"
        if self.backend == "local":
            self.llm = Brain()
            # Optionally, set gpu_manager if needed
            # from modules.gpu_manager import GPUManager
            # self.gpu_manager = GPUManager()
        else:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                api_key = Prompt.ask("[bold cyan]Enter your Gemini API key[/bold cyan]", password=True)
            model = "gemini-1.5-flash"
            self.gemini_client = GeminiClient(api_key, model)
        return True

    def get_llm(self):
        return self.llm if self.backend == "local" else self.gemini_client

    def is_using_gemini(self):
        return self.backend == "gemini"

    def get_gpu_manager(self):
        return self.gpu_manager
