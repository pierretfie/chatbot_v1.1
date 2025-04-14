#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable

// Debug info structure
typedef struct {
    uchar password[4];
    uchar hash[16];
    uchar is_match;
} debug_info_t;

// Result structure
typedef struct {
    int found;
    uchar password[4];
} result_t;

// MD5 helper functions
#define F(x, y, z) (((x) & (y)) | (~(x) & (z)))
#define G(x, y, z) (((x) & (z)) | ((y) & ~(z)))
#define H(x, y, z) ((x) ^ (y) ^ (z))
#define I(x, y, z) ((y) ^ ((x) | ~(z)))

#define ROTATE_LEFT(x, n) (((x) << (n)) | ((x) >> (32-(n))))

#define STEP(f, a, b, c, d, x, t, s) \
    (a) += f((b), (c), (d)) + (x) + (t); \
    (a) = ROTATE_LEFT((a), (s)); \
    (a) += (b);

void md5_process_block(__private const uchar* block, __private uint* state) {
    uint a = state[0];
    uint b = state[1];
    uint c = state[2];
    uint d = state[3];
    
    uint W[16];
    for(int i = 0; i < 16; i++) {
        W[i] = ((uint)block[i*4 + 3] << 24) |
               ((uint)block[i*4 + 2] << 16) |
               ((uint)block[i*4 + 1] << 8) |
               ((uint)block[i*4]);
    }
    
    // Round 1
    STEP(F, a, b, c, d, W[0], 0xd76aa478, 7);
    STEP(F, d, a, b, c, W[1], 0xe8c7b756, 12);
    STEP(F, c, d, a, b, W[2], 0x242070db, 17);
    STEP(F, b, c, d, a, W[3], 0xc1bdceee, 22);
    STEP(F, a, b, c, d, W[4], 0xf57c0faf, 7);
    STEP(F, d, a, b, c, W[5], 0x4787c62a, 12);
    STEP(F, c, d, a, b, W[6], 0xa8304613, 17);
    STEP(F, b, c, d, a, W[7], 0xfd469501, 22);
    STEP(F, a, b, c, d, W[8], 0x698098d8, 7);
    STEP(F, d, a, b, c, W[9], 0x8b44f7af, 12);
    STEP(F, c, d, a, b, W[10], 0xffff5bb1, 17);
    STEP(F, b, c, d, a, W[11], 0x895cd7be, 22);
    STEP(F, a, b, c, d, W[12], 0x6b901122, 7);
    STEP(F, d, a, b, c, W[13], 0xfd987193, 12);
    STEP(F, c, d, a, b, W[14], 0xa679438e, 17);
    STEP(F, b, c, d, a, W[15], 0x49b40821, 22);
    
    // Round 2
    STEP(G, a, b, c, d, W[1], 0xf61e2562, 5);
    STEP(G, d, a, b, c, W[6], 0xc040b340, 9);
    STEP(G, c, d, a, b, W[11], 0x265e5a51, 14);
    STEP(G, b, c, d, a, W[0], 0xe9b6c7aa, 20);
    STEP(G, a, b, c, d, W[5], 0xd62f105d, 5);
    STEP(G, d, a, b, c, W[10], 0x02441453, 9);
    STEP(G, c, d, a, b, W[15], 0xd8a1e681, 14);
    STEP(G, b, c, d, a, W[4], 0xe7d3fbc8, 20);
    STEP(G, a, b, c, d, W[9], 0x21e1cde6, 5);
    STEP(G, d, a, b, c, W[14], 0xc33707d6, 9);
    STEP(G, c, d, a, b, W[3], 0xf4d50d87, 14);
    STEP(G, b, c, d, a, W[8], 0x455a14ed, 20);
    STEP(G, a, b, c, d, W[13], 0xa9e3e905, 5);
    STEP(G, d, a, b, c, W[2], 0xfcefa3f8, 9);
    STEP(G, c, d, a, b, W[7], 0x676f02d9, 14);
    STEP(G, b, c, d, a, W[12], 0x8d2a4c8a, 20);
    
    // Round 3
    STEP(H, a, b, c, d, W[5], 0xfffa3942, 4);
    STEP(H, d, a, b, c, W[8], 0x8771f681, 11);
    STEP(H, c, d, a, b, W[11], 0x6d9d6122, 16);
    STEP(H, b, c, d, a, W[14], 0xfde5380c, 23);
    STEP(H, a, b, c, d, W[1], 0xa4beea44, 4);
    STEP(H, d, a, b, c, W[4], 0x4bdecfa9, 11);
    STEP(H, c, d, a, b, W[7], 0xf6bb4b60, 16);
    STEP(H, b, c, d, a, W[10], 0xbebfbc70, 23);
    STEP(H, a, b, c, d, W[13], 0x289b7ec6, 4);
    STEP(H, d, a, b, c, W[0], 0xeaa127fa, 11);
    STEP(H, c, d, a, b, W[3], 0xd4ef3085, 16);
    STEP(H, b, c, d, a, W[6], 0x04881d05, 23);
    STEP(H, a, b, c, d, W[9], 0xd9d4d039, 4);
    STEP(H, d, a, b, c, W[12], 0xe6db99e5, 11);
    STEP(H, c, d, a, b, W[15], 0x1fa27cf8, 16);
    STEP(H, b, c, d, a, W[2], 0xc4ac5665, 23);
    
    // Round 4
    STEP(I, a, b, c, d, W[0], 0xf4292244, 6);
    STEP(I, d, a, b, c, W[7], 0x432aff97, 10);
    STEP(I, c, d, a, b, W[14], 0xab9423a7, 15);
    STEP(I, b, c, d, a, W[5], 0xfc93a039, 21);
    STEP(I, a, b, c, d, W[12], 0x655b59c3, 6);
    STEP(I, d, a, b, c, W[3], 0x8f0ccc92, 10);
    STEP(I, c, d, a, b, W[10], 0xffeff47d, 15);
    STEP(I, b, c, d, a, W[1], 0x85845dd1, 21);
    STEP(I, a, b, c, d, W[8], 0x6fa87e4f, 6);
    STEP(I, d, a, b, c, W[15], 0xfe2ce6e0, 10);
    STEP(I, c, d, a, b, W[6], 0xa3014314, 15);
    STEP(I, b, c, d, a, W[13], 0x4e0811a1, 21);
    STEP(I, a, b, c, d, W[4], 0xf7537e82, 6);
    STEP(I, d, a, b, c, W[11], 0xbd3af235, 10);
    STEP(I, c, d, a, b, W[2], 0x2ad7d2bb, 15);
    STEP(I, b, c, d, a, W[9], 0xeb86d391, 21);
    
    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
}

bool compare_hash(__private const uint* computed, __global const uchar* target) {
    // Compare each byte of the hash
    for (int i = 0; i < 16; i++) {
        if (((uchar*)computed)[i] != target[i]) {
            return false;
        }
    }
    return true;
}

__kernel void bruteforce_md5_debug(
    __global const uchar* target_hash,
    __global const uchar* charset,
    const int charset_len,
    const int password_len,
    __global int* result_found,
    __global uchar* found_password,
    __global uchar* debug_output
) {
    int gid = get_global_id(0);
    
    // Only process 4-digit passwords
    if (password_len != 4) {
        return;
    }

    // Calculate the four digits with bounds checking
    int first_digit = min(gid / 1000, charset_len - 1);
    int remainder = gid % 1000;
    int second_digit = min(remainder / 100, charset_len - 1);
    remainder = remainder % 100;
    int third_digit = min(remainder / 10, charset_len - 1);
    int fourth_digit = min(remainder % 10, charset_len - 1);

    // Initialize password array with proper alignment
    uchar current_password[64] __attribute__((aligned(16))) = {0};
    
    // Copy characters from charset with bounds checking
    current_password[0] = charset[first_digit];
    current_password[1] = charset[second_digit];
    current_password[2] = charset[third_digit];
    current_password[3] = charset[fourth_digit];
    
    // Set padding marker and message length in bits
    current_password[4] = 0x80;  // Padding marker
    for (int i = 5; i < 56; i++) {
        current_password[i] = 0;
    }
    // Message length in bits (4 bytes * 8 = 32 bits)
    current_password[56] = 32;   // Low byte
    current_password[57] = 0;    // High byte
    current_password[58] = 0;
    current_password[59] = 0;
    current_password[60] = 0;
    current_password[61] = 0;
    current_password[62] = 0;
    current_password[63] = 0;

    // Initialize hash state with proper alignment
    uint state[4] __attribute__((aligned(16))) = {
        0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
    };
    
    // Process the message block
    md5_process_block(current_password, state);
    
    // Compare the computed hash with target
    bool is_match = compare_hash(state, target_hash);

    // Store debug info with proper alignment
    int debug_offset = gid * 21;  // 4 chars + 16 bytes hash + 1 byte status
    
    // Store password characters
    debug_output[debug_offset] = current_password[0];
    debug_output[debug_offset + 1] = current_password[1];
    debug_output[debug_offset + 2] = current_password[2];
    debug_output[debug_offset + 3] = current_password[3];
    
    // Store hash with proper byte ordering
    for (int i = 0; i < 16; i++) {
        debug_output[debug_offset + 4 + i] = ((uchar*)state)[i];
    }
    
    // Store match status
    debug_output[debug_offset + 20] = is_match ? 1 : 0;

    // Update result if match found
    if (is_match) {
        atomic_cmpxchg(result_found, 0, 1);
        found_password[0] = current_password[0];
        found_password[1] = current_password[1];
        found_password[2] = current_password[2];
        found_password[3] = current_password[3];
    }
} 