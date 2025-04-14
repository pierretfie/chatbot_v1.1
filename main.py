import os
import subprocess
import shlex
import contextlib
import sys
import time
from datetime import datetime
import threading

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

# Import modules with stderr redirected to suppress NNPACK warnings
with redirect_stderr():
    from modules.brain import Brain
    from modules.resource_manager import ResourceManager
    from modules.gpu_manager import GPUManager
    from modules.tts_module import synthesize_to_temp_file, play_audio_file
    from modules.config import Config

console = Console()

class VoiceChatbot:
    def __init__(self):
        # Initialize components
        self.resource_manager = ResourceManager()
        self.gpu_manager = GPUManager()
        self.brain = Brain()
        self.tts_module = synthesize_to_temp_file
        
        # Verify paths
        self._verify_paths()
        
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
                

        
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response."""
        try:
            # Check resources before processing
            if not self.resource_manager.check_resources():
                if not self.resource_manager.wait_for_resources():
                    return Config.ERROR_MESSAGES['resource_error']
            
            # Create a single-line live display for the timer
            import threading
            import time
            
            # Variable to track the timer
            start_time = time.time()
            stop_timer = threading.Event()
            
            # Function to get the current timer display
            def get_timer_display():
                elapsed = time.time() - start_time
                return Text(f"Generating..... {elapsed:.1f}s", style="dim")
            
            # Start the live display with a higher refresh rate
            with Live(get_timer_display(), refresh_per_second=30, transient=True) as live:
                try:
                    # Start response generation in a separate thread
                    response_result = [None]
                    generation_time = [0]
                    error_result = [None]  # Variable to store errors from the thread

                    def generate_response_thread():
                        try:
                            response_result[0], generation_time[0] = self.brain.generate_response(user_input)
                        except Exception as e:
                            error_result[0] = e # Store the exception

                    gen_thread = threading.Thread(target=generate_response_thread)
                    gen_thread.start()

                    # Update the display while waiting for response
                    while gen_thread.is_alive():
                        live.update(get_timer_display())
                        time.sleep(0.01)  # Update every 10ms
                    
                    gen_thread.join() # Ensure thread finishes before checking results

                    # Check if an error occurred in the thread
                    if error_result[0] is not None:
                        # console.print(f"[red]Error in generation thread: {error_result[0]}[/red]") # Debug print commented out
                        # Optionally, print the full traceback for more detail
                        # import traceback
                        # console.print(f"[red]{traceback.format_exc()}[/red]")
                        return Config.ERROR_MESSAGES['model_error'], 0

                    # Update final display if no error
                    live.update(Text(f"Generation completed in {generation_time[0]:.1f}s", style="dim"))

                    # Check if response generation was successful but returned None (unexpected)
                    if response_result[0] is None:
                        # console.print("[red]Error: Response generation finished but result is None.[/red]") # Debug print commented out
                        return Config.ERROR_MESSAGES['model_error'], 0

                    return response_result[0], generation_time[0]

                except Exception as e: # Catch errors starting/managing the thread
                    # Removed the print here as it's less likely and covered above/below
                    raise e # Re-raise for the outer handler

        except Exception as e: # Catch errors from resource checks or re-raised exceptions
            # Print the specific error for debugging if it wasn't caught above
            # This is now mainly for errors *outside* the generation thread logic
            if error_result[0] is None: # Avoid double printing if thread error was already handled
                # console.print(f"[red]Error during process_input setup or resource check: {e}[/red]") # Debug print commented out
                pass # No need to print here, just return the error message
            # Ensure we still return the generic error message
            return Config.ERROR_MESSAGES['model_error'], 0
        
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
        """Main chatbot loop."""
        # Show initial resource status
        resource_table = self.get_resource_table()
        console.print(Panel.fit(resource_table, title="System Status"))
        
        # Get personalized greeting
        greeting = self.brain.get_greeting()
        
        # Show welcome message with personalized greeting
        console.print(Panel.fit(
            #add a unique emoji to the title
            f"[bold red]Rena Chatbot[/bold red] 🤖\n\n"
            "[dim]Type 'exit' to quit, 'clear' to clear history[/dim]",
            title="Welcome"
        ))
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n\n[bold green]You[/bold green]")
                
                # Check for special commands
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'clear':
                    self.brain.clear_history()
                    console.print("[yellow]Conversation history cleared.[/yellow]")
                    continue
                    
                # Process input and get response
                response, generation_time = self.process_input(user_input)

                # --- Audio Synthesis and Playback Start ---
                audio_file_path = None
                audio_thread = None
                try:
                    # Show spinner while synthesizing (no text)
                    with console.status("", spinner="dots") as status:
                        audio_file_path = self.tts_module(response)
                    
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
                typing_char_delay = 0.07 # Example: 30 milliseconds per character

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
        self.brain.clear_history()
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
