import numpy as np
import time
import sys
import platform
import subprocess
import os
import threading
import queue
import gc
import contextlib
import pynvml
import logging
from rich.console import Console

console = Console()

# Optional PyOpenCL import
try:
    import pyopencl as cl
    PYOPENCL_AVAILABLE = True
except ImportError:
    PYOPENCL_AVAILABLE = False
    # Define dummy cl.Error if pyopencl is not installed
    class CLError(Exception): pass
    class cl:
        class Error(CLError): pass
        device_type = type('obj', (object,), {'GPU': None})()
        device_info = type('obj', (object,), {})()
        command_queue_properties = type('obj', (object,), {'PROFILING_ENABLE': None})()
        mem_flags = type('obj', (object,), {'READ_ONLY': None, 'COPY_HOST_PTR': None, 'WRITE_ONLY': None})()
        @staticmethod
        def get_platforms(): return []
        @staticmethod
        def Context(*args, **kwargs): raise ImportError("pyopencl not installed")
        @staticmethod
        def CommandQueue(*args, **kwargs): raise ImportError("pyopencl not installed")
        @staticmethod
        def Buffer(*args, **kwargs): raise ImportError("pyopencl not installed")
        @staticmethod
        def Program(*args, **kwargs): raise ImportError("pyopencl not installed")
        @staticmethod
        def enqueue_nd_range_kernel(*args, **kwargs): raise ImportError("pyopencl not installed")
        @staticmethod
        def enqueue_copy(*args, **kwargs): raise ImportError("pyopencl not installed")

# Required imports
import torch
import psutil

class GPUManager:
    def __init__(self):
        # Core state
        self.initialized = False
        self.selected_device_info = None
        self.selected_device_source = None

        # CUDA specific state (PyTorch)
        self.torch_device = None

        # OpenCL specific state
        self.cl_context = None
        self.cl_device = None
        self.cl_queue = None
        self.cl_platform = None

        # Detected devices
        self._detected_cuda_devices = []
        self._detected_opencl_devices = []

        # Internal state
        self._suppress_output = False
        self._opencl_available_runtime = PYOPENCL_AVAILABLE

    def _log(self, message, level="info"):
        """Controlled logging method."""
        if self._suppress_output:
            return
        styles = {"info": "green", "warning": "yellow", "error": "red", "debug": "dim"}
        console.print(f"[{styles.get(level, 'white')}]{message}[/]")

    def set_suppress_output(self, suppress=True):
        """Enable or disable logging output."""
        self._suppress_output = suppress

    def _get_cuda_device_info(self, device_id):
        """Get detailed info for a specific CUDA device using PyTorch."""
        try:
            props = torch.cuda.get_device_properties(device_id)
            free_mem, total_mem = torch.cuda.mem_get_info(device_id)
            gpu_memory_gb = total_mem / (1024**3)
            compute_capability = f"{props.major}.{props.minor}"

            return {
                'id': device_id,
                'source': 'cuda',
                'name': props.name,
                'vendor': 'NVIDIA',
                'version': f"CUDA {torch.version.cuda}",
                'compute_capability': compute_capability,
                'multi_processor_count': props.multi_processor_count,
                'global_mem_size': total_mem,
                'free_mem_size': free_mem,
                'max_work_group_size': getattr(props, 'maxThreadsPerBlock', 1024),
            }
        except Exception as e:
            self._log(f"Warning: Could not get CUDA device info for ID {device_id}: {e}", "warning")
            return None

    def _get_opencl_device_info(self, device, platform):
        """Get detailed info for a specific OpenCL device."""
        if not self._opencl_available_runtime:
            return None
        try:
            mem_size = device.get_info(cl.device_info.GLOBAL_MEM_SIZE)
            return {
                'id': device.int_ptr,
                'source': 'opencl',
                'name': device.get_info(cl.device_info.NAME).strip(),
                'vendor': device.get_info(cl.device_info.VENDOR).strip(),
                'version': device.get_info(cl.device_info.VERSION).strip(),
                'driver_version': device.get_info(cl.device_info.DRIVER_VERSION).strip(),
                'max_compute_units': device.get_info(cl.device_info.MAX_COMPUTE_UNITS),
                'global_mem_size': mem_size,
                'max_work_group_size': device.get_info(cl.device_info.MAX_WORK_GROUP_SIZE),
                'cl_device': device,
                'cl_platform': platform,
            }
        except cl.Error as e:
            self._log(f"Warning: Could not get OpenCL device info for {device.name}: {e}", "warning")
            return None
        except Exception as e:
            self._log(f"Warning: Unexpected error getting OpenCL info for {device.name}: {e}", "warning")
            return None

    def _discover_devices(self):
        """Discover available CUDA and OpenCL devices."""
        self._detected_cuda_devices = []
        self._detected_opencl_devices = []

        # 1. Discover CUDA devices via PyTorch
        if torch.cuda.is_available():
            try:
                count = torch.cuda.device_count()
                self._log(f"Found {count} CUDA device(s) via PyTorch.")
                for i in range(count):
                    info = self._get_cuda_device_info(i)
                    if info:
                        self._detected_cuda_devices.append(info)
            except Exception as e:
                self._log(f"Error discovering CUDA devices: {e}", "error")
        else:
            self._log("PyTorch CUDA not available.", "info")

        # 2. Discover OpenCL devices (if available)
        if self._opencl_available_runtime:
            self._log("Attempting to discover OpenCL devices...")
            try:
                platforms = cl.get_platforms()
                if not platforms:
                    self._log("No OpenCL platforms found.", "warning")

                for platform in platforms:
                    try:
                        gpu_devices = platform.get_devices(device_type=cl.device_type.GPU)
                        self._log(f"Platform '{platform.name}' has {len(gpu_devices)} GPU device(s).")
                        for device in gpu_devices:
                            # Avoid adding duplicates if a CUDA device also appears here
                            is_duplicate_cuda = False
                            if self._detected_cuda_devices:
                                cl_name = device.get_info(cl.device_info.NAME).strip()
                                if any(cuda_dev['name'] == cl_name for cuda_dev in self._detected_cuda_devices):
                                    self._log(f"Skipping OpenCL device '{cl_name}' as it seems to be a duplicate of a detected CUDA device.", "debug")
                                    is_duplicate_cuda = True

                            if not is_duplicate_cuda:
                                info = self._get_opencl_device_info(device, platform)
                                if info:
                                    self._detected_opencl_devices.append(info)
                    except cl.Error as e:
                        self._log(f"Warning: OpenCL error querying devices on platform '{platform.name}': {e}", "warning")
                    except Exception as e:
                        self._log(f"Warning: Unexpected error querying devices on platform '{platform.name}': {e}", "warning")

            except cl.Error as e:
                self._log(f"Error getting OpenCL platforms: {e}", "warning")
                self._opencl_available_runtime = False
            except Exception as e:
                self._log(f"Unexpected error during OpenCL discovery: {e}", "error")
                self._opencl_available_runtime = False
        else:
            self._log("PyOpenCL not installed or available.", "info")

    def _select_device(self, device_index=None, preferred_gpu=None):
        """Selects the best available device based on criteria."""
        all_devices = self._detected_cuda_devices + self._detected_opencl_devices

        if not all_devices:
            self._log("No compatible GPU devices found.", "error")
            return None

        selected_device = None

        # 1. By Index (if specified and valid)
        if device_index is not None:
            if 0 <= device_index < len(all_devices):
                selected_device = all_devices[device_index]
                self._log(f"Selected device by index {device_index}: {selected_device['name']} ({selected_device['source']})")
            else:
                self._log(f"Warning: Invalid device_index {device_index}. Max index is {len(all_devices)-1}.", "warning")

        # 2. By Preferred Name/Vendor (if index not used or invalid)
        if not selected_device and preferred_gpu:
            preference = preferred_gpu.lower()
            for device in all_devices:
                if preference == device['name'].lower():
                    selected_device = device
                    break
            if not selected_device:
                for device in all_devices:
                    if preference in device['vendor'].lower():
                        selected_device = device
                        break
            if selected_device:
                self._log(f"Selected device by preference '{preferred_gpu}': {selected_device['name']} ({selected_device['source']})")
            else:
                self._log(f"Warning: Preferred GPU '{preferred_gpu}' not found.", "warning")

        # 3. Default: Select first CUDA device if available, otherwise first OpenCL
        if not selected_device:
            if self._detected_cuda_devices:
                selected_device = self._detected_cuda_devices[0]
            elif self._detected_opencl_devices:
                selected_device = self._detected_opencl_devices[0]

        if selected_device:
            self._log(f"Final selected device: {selected_device['name']} ({selected_device['source']})")
            return selected_device
        else:
            self._log("Could not select a suitable device.", "error")
            return None

    def initialize(self, device_index=None, preferred_gpu=None):
        """Initialize the GPU Manager."""
        self._log("Initializing GPU Manager...")
        self.cleanup()

        self._discover_devices()
        self.selected_device_info = self._select_device(device_index, preferred_gpu)

        if not self.selected_device_info:
            self._log("Initialization failed: No suitable GPU device selected.", "error")
            return False

        self.selected_device_source = self.selected_device_info['source']

        init_success = False

        # Initialize based on the source of the selected device
        if self.selected_device_source == 'cuda':
            try:
                cuda_id = self.selected_device_info['id']
                self.torch_device = torch.device(f'cuda:{cuda_id}')
                self._log(f"Initializing CUDA device: {self.selected_device_info['name']} (torch.device='{self.torch_device}')")
                init_success = True
            except Exception as e:
                self._log(f"Failed to initialize selected CUDA device: {e}", "error")
                init_success = False

        elif self.selected_device_source == 'opencl':
            if not self._opencl_available_runtime:
                self._log("Initialization failed: OpenCL selected but PyOpenCL is not available.", "error")
                return False
            try:
                self.cl_device = self.selected_device_info['cl_device']
                self.cl_platform = self.selected_device_info['cl_platform']
                self._log(f"Initializing OpenCL device: {self.selected_device_info['name']}")

                # Create context and queue
                self.cl_context = cl.Context(devices=[self.cl_device])
                self.cl_queue = cl.CommandQueue(
                    self.cl_context,
                    properties=cl.command_queue_properties.PROFILING_ENABLE
                )
                init_success = True

            except cl.Error as e:
                self._log(f"Failed to initialize selected OpenCL device: {e}", "error")
                init_success = False
            except Exception as e:
                self._log(f"Unexpected error initializing OpenCL device: {e}", "error")
                init_success = False
        else:
            self._log(f"Initialization failed: Unknown device source '{self.selected_device_source}'.", "error")
            return False

        if init_success:
            self.initialized = True
            self._log("GPU Manager initialized successfully.", "info")
            self.display_selected_device_summary()
            return True
        else:
            self._log("Initialization failed. Cleaning up.", "error")
            self.cleanup()
            return False

    def display_selected_device_summary(self):
        """Prints a summary of the initialized device."""
        if not self.initialized or not self.selected_device_info:
            self._log("Cannot display summary: GPU Manager not initialized.", "warning")
            return

        info = self.selected_device_info
        console.print("\n--- Initialized GPU Summary ---", style="bold cyan")
        print(f"  Name:       {info.get('name', 'N/A')}")
        print(f"  Source:     {info.get('source', 'N/A').upper()}")
        print(f"  Vendor:     {info.get('vendor', 'N/A')}")
        mem_gb = info.get('global_mem_size', 0) / (1024**3)
        print(f"  Memory:     {mem_gb:.2f} GB")
        if info['source'] == 'cuda':
            free_mem_gb = info.get('free_mem_size', 0) / (1024**3)
            print(f"  Free Mem:   {free_mem_gb:.2f} GB (approx)")
            print(f"  Capability: {info.get('compute_capability', 'N/A')}")
        console.print("-----------------------------", style="bold cyan")

    def get_device_info(self):
        """Get information about the currently initialized GPU device."""
        if not self.initialized:
            self._log("Cannot get device info: GPU Manager not initialized.", "warning")
            return None
        return self.selected_device_info.copy() if self.selected_device_info else None

    def is_initialized(self):
        """Check if the GPU Manager has been successfully initialized."""
        return self.initialized

    def cleanup(self):
        """Clean up resources."""
        self._log("Cleaning up GPU Manager resources...", "debug")
        
        # Release OpenCL resources
        if self.cl_queue:
            try:
                self.cl_queue.finish()
                self._log("Finished OpenCL command queue.", "debug")
            except Exception as e:
                print(f"GPUManager Cleanup Warning: Error finishing OpenCL queue: {e}")
        
        # Reset state
        self.cl_queue = None
        self.cl_context = None
        self.cl_device = None
        self.cl_platform = None
        self.torch_device = None
        self.selected_device_info = None
        self.selected_device_source = None
        self.initialized = False

        self._log("GPU Manager cleanup complete.", "debug")
        return True

    def __del__(self):
        """Destructor attempts to clean up resources."""
        try:
            if self.initialized:
                print("GPUManager: __del__ triggering cleanup...")
                self.cleanup()
        except Exception as e:
            print(f"GPUManager: Error in __del__ cleanup: {e}")
            pass

    def get_gpu_usage(self) -> float:
        """Get current GPU utilization percentage."""
        if not self.initialized:
            return 0.0
            
        try:
            if self.selected_device_source == 'cuda':
                # Use PyTorch's CUDA utilities
                if torch.cuda.is_available():
                    return torch.cuda.utilization(self.selected_device_info['id'])
            elif self.selected_device_source == 'opencl':
                # OpenCL doesn't provide direct utilization info
                return 0.0
                
            # Fallback to NVML if available
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.selected_device_info['id'])
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                return utilization.gpu
            except pynvml.NVMLError:
                return 0.0
            finally:
                try:
                    pynvml.nvmlShutdown()
                except pynvml.NVMLError:
                    pass
                    
        except Exception as e:
            self._log(f"Error getting GPU usage: {e}", "warning")
            return 0.0

    def get_gpu_memory_usage(self) -> float:
        """Get current GPU memory usage percentage."""
        if not self.initialized:
            return 0.0
            
        try:
            if self.selected_device_source == 'cuda':
                # Use PyTorch's CUDA utilities
                if torch.cuda.is_available():
                    total = torch.cuda.get_device_properties(self.selected_device_info['id']).total_memory
                    used = torch.cuda.memory_allocated(self.selected_device_info['id'])
                    return (used / total) * 100
            elif self.selected_device_source == 'opencl':
                # OpenCL doesn't provide direct memory usage info
                return 0.0
                
            # Fallback to NVML if available
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.selected_device_info['id'])
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                return (mem_info.used / mem_info.total) * 100
            except pynvml.NVMLError:
                return 0.0
            finally:
                try:
                    pynvml.nvmlShutdown()
                except pynvml.NVMLError:
                    pass
                    
        except Exception as e:
            self._log(f"Error getting GPU memory usage: {e}", "warning")
            return 0.0

# Initialize NVML for GPU management
def is_gpu_available() -> bool:
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        logging.debug(f"Detected {device_count} GPU(s).")
        return device_count > 0
    except pynvml.NVMLError as e:
        logging.warning(f"GPU check failed: {str(e)}")
        return False
    finally:
        try:
            pynvml.nvmlShutdown()
        except pynvml.NVMLError:
            pass

def get_gpu_memory() -> float:
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        return mem_info.total / (1024 ** 3)
    except pynvml.NVMLError as e:
        logging.warning(f"GPU memory retrieval failed: {str(e)}")
        return 0.0
    finally:
        try:
            pynvml.nvmlShutdown()
        except pynvml.NVMLError:
            pass 