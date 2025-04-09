import psutil
import time
from typing import Dict, Optional
from rich.console import Console
import os
from config import Config

console = Console()

class ResourceManager:
    """Manages system resources for the chatbot."""
    
    def __init__(self):
        self.cpu_threshold = Config.CPU_THRESHOLD
        self.memory_threshold = Config.MEMORY_THRESHOLD
        self._last_check_time = 0
        self._check_interval = 1.0  # seconds between checks
        
    def get_system_stats(self) -> Dict[str, float]:
        """Get current system resource usage statistics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'cpu_count' : os.cpu_count(),
            'memory_percent': psutil.virtual_memory().percent,
            'swap_percent': psutil.swap_memory().percent if hasattr(psutil, 'swap_memory') else 0.0
        }
    
    def get_cpu_cores(self) -> int:
        """Get the number of CPU cores."""
        return psutil.cpu_count(logical=False)
        
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=0.1)
        
    def get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent
    
    def check_resources(self) -> bool:
        """Check if system resources are within acceptable limits."""
        current_time = time.time()
        if current_time - self._last_check_time < self._check_interval:
            return True  # Skip check if too soon
            
        cpu_percent = self.get_cpu_usage()
        memory_percent = self.get_memory_usage()
        
        self._last_check_time = current_time
        
        # Log resource usage if high
        if cpu_percent > self.cpu_threshold or memory_percent > self.memory_threshold:
            console.print(f"[yellow]Warning: High resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%[/yellow]")
            return False
            
        return True
    
    def wait_for_resources(self, timeout: float = 30.0) -> bool:
        """Wait for system resources to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_resources():
                return True
            time.sleep(1.0)
        return False
    
    def get_resource_status(self) -> Dict[str, str]:
        """Get human-readable status of system resources."""
        stats = self.get_system_stats()
        return {
            'cpu': f"{stats['cpu_percent']:.1f}%",
            'memory': f"{stats['memory_percent']:.1f}%",
            'swap': f"{stats['swap_percent']:.1f}%",
            'status': 'OK' if self.check_resources() else 'WARNING'
        }
    
    def adjust_limits(self, new_cpu_limit: Optional[float] = None, 
                     new_memory_limit: Optional[float] = None):
        """Adjust resource limits dynamically."""
        if new_cpu_limit is not None:
            self.cpu_threshold = new_cpu_limit
        if new_memory_limit is not None:
            self.memory_threshold = new_memory_limit 
    
    def get_target_cores(self) -> int:
        """Get the number of CPU cores being used by the model."""
        _, target_cores, _ = self.optimize_cpu_usage()
        return target_cores

    def optimize_cpu_usage(self):
        process = psutil.Process()
        stats = self.get_system_stats()

        if stats['cpu_count'] > 1:
            current_load = psutil.getloadavg()[0] / stats['cpu_count']
            if current_load < 0.8:
                target_cores = max(1, min(int(stats['cpu_count']*0.75), 4))
            else:
                target_cores = max(1, min(int(stats['cpu_count']*0.5), 2))
            affinity = list(range(target_cores))
            try:
                process.cpu_affinity(affinity)
            
            # Try to set moderate process priority
                try:
                    if os.name == 'nt':  # Windows
                        process.nice(psutil.NORMAL_PRIORITY_CLASS)
                    else:  # Linux/Unix
                        process.nice(0)  # Normal priority
                except:
                    pass

                return True, target_cores, current_load
            except Exception as e:
                return False, stats['cpu_count'], current_load
        else:
            return False, 1, 0