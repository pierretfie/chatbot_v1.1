import os
import subprocess
import shlex
import contextlib
import sys
import time
from datetime import datetime
import threading
import json

# Function to temporarily redirect stderr
@contextlib.contextmanager
def redirect_stderr():
    """Temporarily redirect stderr to /dev/null"""
    stderr_fd = sys.stderr.fileno()
    with open(os.devnull, 'w') as devnull:
        # Save a copy of the original stderr
        stderr_copy = os.dup(stderr_fd)
        # Replace stderr with /dev/null
        os.dup2(devnull.fileno(), stderr_fd)
        try:
            yield
        finally:
            # Restore the original stderr
            os.dup2(stderr_copy, stderr_fd)
            os.close(stderr_copy)

# Import rich components
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.box import SIMPLE
import random
from rich.text import Text
from rich.status import Status

# Import GeminiClient
from modules.gemini_client import GeminiClient
# Import ModelSelector
from modules.model_selector import ModelSelector

# Import modules with stderr redirected to suppress NNPACK warnings
with redirect_stderr():
    from modules.brain import Brain
    from modules.resource_manager import ResourceManager
    from modules.gpu_manager import GPUManager
    from modules.coqui import generate_audio, play_audio_file, init
    from modules.config import Config
    from modules.personal_info_manager import PersonalInfoManager
    from modules.user_manager import UserManager
    from modules.prompt_template import PromptTemplate

console = Console()
class VoiceChatbot:
    def __init__(self):
        # Initialize components
        self.resource_manager = ResourceManager()
        self.gpu_manager = GPUManager()
        self.model_selector = ModelSelector()
        if not self.model_selector.select_and_initialize():
            console.print("[red]Model selection failed. Exiting.")
            sys.exit(1)
        self.llm = self.model_selector.get_llm()
        self.using_gemini = self.model_selector.is_using_gemini()
        self.coqui = init()

        # Verify paths
        self._verify_paths()
        self.user_manager = UserManager()
        self.personal_info_manager = PersonalInfoManager(self.user_manager)
        
        self.history = []
        self.history_file = os.path.expanduser("~/my_AI/conversation_history.json")
        self.load_history()
        
    def _verify_paths(self):
        """Verify all required paths exist."""
        paths_to_check = {
            'TinyLlama model': Config.TINYLLAMA_PATH
        }
        
        for name, path in paths_to_check.items():
            if not os.path.exists(path):
                error_msg = Config.ERROR_MESSAGES['file_not_found'].format(path=path)
                console.print(f"[red]{error_msg}[/red]")
                raise FileNotFoundError(f"{name} not found at: {path}")
                

        
    def process_input(self, user_input: str):
        # --- Personal info extraction and query handling ---
        pi_response = self.personal_info_manager.extract_and_store(user_input)
        if pi_response:
            return pi_response, 0
        profile_query_response = self.personal_info_manager.handle_profile_query(user_input)
        if profile_query_response:
            return profile_query_response, 0
        try:
            if not self.resource_manager.check_resources():
                if not self.resource_manager.wait_for_resources():
                    return Config.ERROR_MESSAGES['resource_error']
            import threading
            import time
            from rich.live import Live
            from rich.text import Text
            from modules.prompt_template import PromptTemplate

            # --- MEMORY-AWARE PROMPT CONSTRUCTION ---
            context_turns = Config.MAX_HISTORY if hasattr(Config, 'MAX_HISTORY') else 10
            conversation_history = self.get_recent_history(context_turns)
            system_prompt = PromptTemplate.get_system_prompt()
            user_info = self.user_manager.user_data.get('name', '')
            prompt = PromptTemplate.get_chat_prompt(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                user_input=user_input,
                user_info=user_info
            )

            response_result = [None]
            generation_time = [0]
            error_result = [None]

            def get_timer_display(start_time):
                elapsed = time.time() - start_time
                return Text(f"Generating... {elapsed:.1f}s", style="dim")

            def generate_response_thread():
                try:
                    t0 = time.time()
                    response = self.llm(prompt, max_tokens=Config.MAX_TOKENS, temperature=1.0)
                    response_result[0] = response
                    t1 = time.time()
                    generation_time[0] = t1 - t0
                except Exception as e:
                    error_result[0] = e

            start_time = time.time()
            with Live(get_timer_display(start_time), refresh_per_second=30, transient=True) as live:
                thread = threading.Thread(target=generate_response_thread)
                thread.start()
                while thread.is_alive():
                    live.update(get_timer_display(start_time))
                    time.sleep(0.05)
                thread.join()

            if error_result[0] is not None:
                raise error_result[0]
            if response_result[0] is None:
                return Config.ERROR_MESSAGES['model_error'], 0
            if isinstance(response_result[0], dict) and 'choices' in response_result[0] and response_result[0]['choices']:
                return response_result[0]['choices'][0]['text'], generation_time[0]
            elif isinstance(response_result[0], str):
                return response_result[0], generation_time[0]
            else:
                return "[No response]", generation_time[0]
        except Exception as e:
            if 'error_result' in locals() and error_result[0] is None:
                pass
            return Config.ERROR_MESSAGES['model_error'], 0
        
    def get_recent_history(self, context_turns=20):
        """Return the last N turns of conversation as a list of dicts."""
        return self.history[-context_turns:]

    def add_to_history(self, role, content):
        """Add a message to the conversation history."""
        self.history.append({"role": role, "content": content})
        self.save_history()  # Save after each addition for persistence

    def save_history(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                self.history = json.load(f)
        else:
            self.history = []
        
    def get_resource_table(self) -> Table:
        """Create a table showing current resource usage."""
        # dim the table box lines
        table = Table(box=SIMPLE)
        table.add_column(f"[dim]Metric[/dim]", style="cyan")
        table.add_column(f"[dim]Value[/dim]", style="green")
        
        # Get resource metrics
        cpu_percent = self.resource_manager.get_cpu_usage()
        target_cores = self.resource_manager.get_target_cores()
        memory_percent = self.resource_manager.get_memory_usage()
        
        # Get GPU metrics if available
        gpu_percent = self.gpu_manager.get_gpu_usage()
        gpu_memory = self.gpu_manager.get_gpu_memory_usage()
        
        # Add rows
        table.add_row(f"[dim]Target CPU Cores[/dim]", f"[dim]{target_cores}[/dim]")
        table.add_row(f"[dim]CPU Usage[/dim]", f"[dim]{cpu_percent:.1f}%[/dim]")
        table.add_row(f"[dim]Memory Usage[/dim]", f"[dim]{memory_percent:.1f}%[/dim]")
        
        # Add GPU rows if GPU is available
        if gpu_percent > 0 or gpu_memory > 0:
            table.add_row(f"[dim]GPU Usage[/dim]", f"[dim]{gpu_percent:.1f}%[/dim]")
            table.add_row(f"[dim]GPU Memory[/dim]", f"[dim]{gpu_memory:.1f}%[/dim]")
        
        return table
        
    def run(self):
        # Update last interaction immediately at session start for accurate greeting
        self.user_manager.update_last_interaction()
        # Show initial resource status
        resource_table = self.get_resource_table()
        console.print(Panel.fit(resource_table, title="System Status"))

        # Show available commands/tips above the welcome block
        console.print("[dim]Type 'exit' to quit, 'clear' to clear history[/dim]")

        # Get personalized greeting string (time-aware, brief, with time-of-day)
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            time_greeting = "Good morning"
        elif 12 <= hour < 18:
            time_greeting = "Good afternoon"
        elif 18 <= hour < 22:
            time_greeting = "Good evening"
        else:
            time_greeting = "Hello"
        days, hours, minutes, seconds = self.user_manager.get_time_since_last_meeting()
        name = self.user_manager.user_data.get("name", "User")
        if days > 0:
            time_str = f"{days} day{'s' if days != 1 else ''}"
        elif hours > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
        elif minutes > 0:
            time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            time_str = "a moment"
        brief_greeting = f"{time_greeting} {name}, it has been {time_str} since we spoke. How can I help you?"

        # Show welcome message with brief greeting (no tips inside)
        console.print(Panel.fit(
            f"[bold red]Rena Chatbot[/bold red] 🤖\n\n"
            f"{brief_greeting}",
            title="Welcome"
        ))
        # Play audio for the opening greeting
        try:
            audio_path = generate_audio(brief_greeting)
            play_audio_file(audio_path)
        except Exception as e:
            console.print(f"[yellow]Audio playback failed: {e}[/yellow]")

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n\n[bold green]You[/bold green]")
                
                # Check for special commands
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'clear':
                    console.print("[yellow]Conversation history cleared.[/yellow]")
                    self.history = []
                    self.save_history()
                    continue
                    
                # Process input and get response
                response, generation_time = self.process_input(user_input)

                # --- Audio Synthesis and Playback Start ---
                audio_file_path = None
                audio_thread = None
                try:
                    # Show spinner while synthesizing (no text)
                    with console.status("", spinner="dots") as status:
                        audio_file_path = generate_audio(response)
                    
                    # Synthesis finished (spinner stops automatically)
                    
                        if audio_file_path:
                            # Start audio playback in a separate thread
                            audio_thread = threading.Thread(target=play_audio_file, args=(audio_file_path,))
                            audio_thread.start()
                        else:
                            console.print("[yellow]Skipping audio playback due to synthesis error.[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error during TTS synthesis or playback initiation: {str(e)}[/red]")
                # --- Audio Synthesis and Playback End ---

                # --- Text Animation Start ---
                # Use a fixed, natural typing speed instead of calculating based on total duration
                # Adjust this value (seconds per character) for desired speed
                typing_char_delay = 0.05 # Example: 30 milliseconds per character

                console.print("\n[bold blue]Rena:[/bold blue] ", end="")
                for char in response:
                    print(char, end="", flush=True)
                    time.sleep(typing_char_delay) # Use the fixed delay
                print("\n")
                #add timer emoji 
                console.print(f'[dim]🕒 {generation_time:.1f}s[/dim]'.ljust(25)) # Pad to overwrite "Synthesizing..."

                # --- Text Animation End ---

                # Note: We don't explicitly join the audio_thread here.
                # This allows the loop to continue to the next prompt even if audio is finishing.
                # The play_audio_file function handles cleanup in the thread.

                self.add_to_history("user", user_input)
                self.add_to_history("assistant", response)

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user. Exiting...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                # If an error occurred, ensure any potentially orphaned audio thread is handled
                # (though in this simple case, letting it finish or error out is usually okay)
                continue
                
    def cleanup(self):
        """Cleanup resources."""
        if not self.using_gemini and hasattr(self.llm, 'clear_history'):
            self.llm.clear_history()
        if hasattr(self, 'gpu_manager'):
            self.gpu_manager.cleanup()

def main():
    chatbot = None
    try:
        chatbot = VoiceChatbot()
        chatbot.run()
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
    finally:
        if chatbot:
            chatbot.cleanup()

if __name__ == "__main__":
    main() 
