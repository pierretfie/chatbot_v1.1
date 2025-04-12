import os
import subprocess
import shlex
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.box import SIMPLE
import random
import time
from datetime import datetime
from modules.brain import Brain
from modules.resource_manager import ResourceManager
from modules.gpu_manager import GPUManager
from modules.tts_module import synthesize_and_play, tts
from modules.config import Config
from rich.text import Text

console = Console()

class VoiceChatbot:
    def __init__(self):
        # Initialize components
        self.resource_manager = ResourceManager()
        self.gpu_manager = GPUManager()
        self.brain = Brain()
        self.tts_module = tts
        
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
                

        
    def speak(self, text: str):
        """Convert text to speech using TTS module."""
        try:
            console.print(f"[dim]Synthesizing audio...[/dim]")
            synthesize_and_play(text)
        except Exception as e:
            console.print(f"[red]Error in text-to-speech: {str(e)}[/red]")
            
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
                    
                    def generate_response_thread():
                        response_result[0], generation_time[0] = self.brain.generate_response(user_input)
                    
                    gen_thread = threading.Thread(target=generate_response_thread)
                    gen_thread.start()
                    
                    # Update the display while waiting for response
                    while gen_thread.is_alive():
                        live.update(get_timer_display())
                        time.sleep(0.01)  # Update every 10ms
                    
                    # Update final display
                    live.update(Text(f"Generation completed in {generation_time[0]:.1f}s", style="dim"))
                    
                    return response_result[0], generation_time[0]
                except Exception as e:
                    raise e
                    
        except Exception as e:
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
                
                # Calculate typing delay based on response length
                # Average speaking rate is about 150 words per minute
                # Average word length is about 5 characters
                words = len(response.split())
                estimated_speech_duration = (words / 150) * 60  # in seconds
                
                # Calculate delay per character to match speech duration
                char_delay = estimated_speech_duration / len(response)
                
                # Ensure delay is within reasonable bounds
                char_delay = max(Config.MIN_TYPING_DELAY, 
                               min(char_delay, Config.MAX_TYPING_DELAY))
                
                # Start typing animation first
                console.print(f'[dim] {generation_time:.1f}s')
                console.print("\n[bold blue]Rena:[/bold blue] ", end="")
                for char in response:
                    print(char, end="", flush=True)
                    time.sleep(char_delay)
                print("\n")
                
                # Use TTS module for speech generation
                self.tts_module.speak(response)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user. Exiting...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
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