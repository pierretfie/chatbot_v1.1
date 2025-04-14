# test_vector_add.py
import pyopencl as cl
import numpy as np
import time
import sys

# --- get_clover_turks_context function (same as before) ---
def get_clover_turks_context():
    target_platform_name = "Clover"
    target_device_name = "AMD TURKS"
    platform = None
    device = None

    print("Looking for OpenCL platforms and devices...")
    try:
        platforms = cl.get_platforms()
        if not platforms:
            print("ERROR: No OpenCL platforms found!")
            return None

        for p in platforms:
            p_name = p.get_info(cl.platform_info.NAME).strip()
            if target_platform_name in p_name:
                platform = p
                try:
                    gpu_devices = platform.get_devices(device_type=cl.device_type.GPU)
                    if not gpu_devices: continue

                    for d in gpu_devices:
                        d_name = d.get_info(cl.device_info.NAME).strip()
                        if target_device_name in d_name:
                            device = d
                            print(f"\nUsing Platform: {p_name}")
                            print(f"Using Device: {d_name}\n")
                            break
                    if device: break
                except cl.Error as e:
                     print(f"  -> CL Error getting devices for '{p_name}': {e}")
                except Exception as e:
                     print(f"  -> Error getting devices for '{p_name}': {e}")


        if not device:
            print(f"ERROR: Target device '{target_device_name}' on platform '{target_platform_name}' not found.")
            print("Check 'clinfo' output again for the exact device name.")
            return None

        # Optional: Add OpenCL version check if needed
        # cl_version_str = device.get_info(cl.device_info.VERSION)
        # print(f"Device OpenCL Version: {cl_version_str}")

        return cl.Context([device])

    except cl.Error as e:
        print(f"OpenCL setup error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during setup: {e}")
        return None
# --- End of get_clover_turks_context ---

# --- Configuration ---
VECTOR_SIZE = 1024 * 1024 # Size of vectors (e.g., 1 million elements)

# --- OpenCL Setup ---
context = get_clover_turks_context()
if not context:
    sys.exit(1)

device = context.devices[0]
queue = cl.CommandQueue(context)

# --- Prepare Data ---
print(f"Preparing data (vector size: {VECTOR_SIZE})...")
# Use float32 for GPU compatibility
A_host = np.random.rand(VECTOR_SIZE).astype(np.float32)
B_host = np.random.rand(VECTOR_SIZE).astype(np.float32)
C_host = np.empty(VECTOR_SIZE, dtype=np.float32) # Result buffer

# --- Create Device Buffers ---
mf = cl.mem_flags
try:
    print("Creating device buffers...")
    A_device = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=A_host)
    B_device = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=B_host)
    # Buffer for the result, only needs writing from the device
    C_device = cl.Buffer(context, mf.WRITE_ONLY, C_host.nbytes)
except cl.Error as e:
    print(f"ERROR creating buffers: {e}")
    sys.exit(1)

# --- Kernel Source (Vector Addition) ---
kernel_source = """
__kernel void vector_add(__global const float *A,
                         __global const float *B,
                         __global float *C,
                         const int size) // Size of the vectors
{
    int i = get_global_id(0); // Get the unique ID for this work item

    // Boundary check: Make sure we don't go past the vector size
    // Necessary if global_size is not an exact multiple of local_size
    // or if global_size is larger than needed (though ideally it matches size)
    if (i < size) {
        C[i] = A[i] + B[i]; // The core operation
    }
}
"""

# --- Compile Kernel ---
print("Compiling kernel...")
try:
    program = cl.Program(context, kernel_source).build()
    vector_add_kernel = program.vector_add
    print("Kernel compiled successfully.")
except cl.RuntimeError as e:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("ERROR: Kernel compilation failed!")
    try:
        print("Build Log:")
        print(program.get_build_info(device, cl.program_build_info.LOG))
    except Exception:
         print("(Could not retrieve build log)")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    sys.exit(1)
except cl.Error as e:
    print(f"ERROR during kernel compilation setup: {e}")
    sys.exit(1)

# --- Execute Kernel ---
print("Executing kernel...")
# Define global size: one work item for each element in the vector
global_size = (VECTOR_SIZE,)
# Local size: Let the driver decide optimal grouping (often reasonable for simple kernels)
local_size = None

# Set kernel arguments (must match the __kernel function signature)
vector_size_arg = np.int32(VECTOR_SIZE) # Pass size as a 32-bit integer
kernel_args = (A_device, B_device, C_device, vector_size_arg)
vector_add_kernel.set_args(*kernel_args)

try:
    start_time = time.time()
    # Enqueue the kernel for execution
    exec_event = cl.enqueue_nd_range_kernel(queue, vector_add_kernel, global_size, local_size)
    # Wait for the kernel execution to finish
    exec_event.wait()
    end_time = time.time()
    gpu_time = end_time - start_time

    print(f"Kernel execution finished.")
    print(f"GPU Kernel Time: {gpu_time:.6f} seconds.")

    # --- Read Result Back ---
    print("Reading result back from device...")
    read_event = cl.enqueue_copy(queue, C_host, C_device)
    read_event.wait() # Wait for the copy operation to complete
    print("Result copied back.")

    # --- Verify Result ---
    print("Verifying result...")
    start_verify_time = time.time()
    # Calculate expected result using NumPy on the CPU
    expected_result = A_host + B_host
    verify_time = time.time() - start_verify_time
    print(f"(CPU verification took {verify_time:.4f} seconds)")

    # Compare using np.allclose for floating point tolerance
    tolerance = 1e-6 # Tolerance for float32 addition
    if np.allclose(C_host, expected_result, atol=tolerance):
        print("\nResult verification PASSED!")
    else:
        diff = np.abs(C_host - expected_result)
        max_diff = np.max(diff)
        print(f"\nResult verification FAILED!")
        print(f"  Max absolute difference: {max_diff:.4E}")

except cl.Error as e:
    print(f"\nAn OpenCL error occurred during execution/copy: {e.what()} (Code: {e.code})")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
finally:
    # Clean up OpenCL objects (optional in Python, but good practice)
    try:
        A_device.release()
        B_device.release()
        C_device.release()
    except Exception:
        pass # Ignore errors if already released or failed earlier
    print("Script finished.") 