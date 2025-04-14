#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable

// --- Start of MD5 Implementation ---
// Based on public domain code by Solar Designer et al.

typedef unsigned int uint;
typedef unsigned char uchar;
typedef unsigned long ulong;

/* The basic MD5 functions */
#define F(x, y, z) ((z) ^ ((x) & ((y) ^ (z))))
#define G(x, y, z) ((y) ^ ((z) & ((x) ^ (y))))
#define H(x, y, z) ((x) ^ (y) ^ (z))
#define I(x, y, z) ((y) ^ ((x) | ~(z)))

/* The MD5 transformation for all four rounds. */
#define STEP(f, a, b, c, d, x, t, s) \
 (a) += f((b), (c), (d)) + (x) + (t); \
 (a) = rotate((a), (uint)(s)); \
 (a) += (b)

// Process a 512-bit block (16 uint words)
inline void md5_process_block(__private uint *hash, __private const uint *W)
{
 uint a = hash[0]; uint b = hash[1]; uint c = hash[2]; uint d = hash[3];
 STEP(F, a, b, c, d, W[ 0], 0xd76aa478,  7); STEP(F, d, a, b, c, W[ 1], 0xe8c7b756, 12);
 STEP(F, c, d, a, b, W[ 2], 0x242070db, 17); STEP(F, b, c, d, a, W[ 3], 0xc1bdceee, 22);
 STEP(F, a, b, c, d, W[ 4], 0xf57c0faf,  7); STEP(F, d, a, b, c, W[ 5], 0x4787c62a, 12);
 STEP(F, c, d, a, b, W[ 6], 0xa8304613, 17); STEP(F, b, c, d, a, W[ 7], 0xfd469501, 22);
 STEP(F, a, b, c, d, W[ 8], 0x698098d8,  7); STEP(F, d, a, b, c, W[ 9], 0x8b44f7af, 12);
 STEP(F, c, d, a, b, W[10], 0xffff5bb1, 17); STEP(F, b, c, d, a, W[11], 0x895cd7be, 22);
 STEP(F, a, b, c, d, W[12], 0x6b901122,  7); STEP(F, d, a, b, c, W[13], 0xfd987193, 12);
 STEP(F, c, d, a, b, W[14], 0xa679438e, 17); STEP(F, b, c, d, a, W[15], 0x49b40821, 22);
 STEP(G, a, b, c, d, W[ 1], 0xf61e2562,  5); STEP(G, d, a, b, c, W[ 6], 0xc040b340,  9);
 STEP(G, c, d, a, b, W[11], 0x265e5a51, 14); STEP(G, b, c, d, a, W[ 0], 0xe9b6c7aa, 20);
 STEP(G, a, b, c, d, W[ 5], 0xd62f105d,  5); STEP(G, d, a, b, c, W[10], 0x02441453,  9);
 STEP(G, c, d, a, b, W[15], 0xd8a1e681, 14); STEP(G, b, c, d, a, W[ 4], 0xe7d3fbc8, 20);
 STEP(G, a, b, c, d, W[ 9], 0x21e1cde6,  5); STEP(G, d, a, b, c, W[14], 0xc33707d6,  9);
 STEP(G, c, d, a, b, W[ 3], 0xf4d50d87, 14); STEP(G, b, c, d, a, W[ 8], 0x455a14ed, 20);
 STEP(G, a, b, c, d, W[13], 0xa9e3e905,  5); STEP(G, d, a, b, c, W[ 2], 0xfcefa3f8,  9);
 STEP(G, c, d, a, b, W[ 7], 0x676f02d9, 14); STEP(G, b, c, d, a, W[12], 0x8d2a4c8a, 20);
 STEP(H, a, b, c, d, W[ 5], 0xfffa3942,  4); STEP(H, d, a, b, c, W[ 8], 0x8771f681, 11);
 STEP(H, c, d, a, b, W[11], 0x6d9d6122, 16); STEP(H, b, c, d, a, W[14], 0xfde5380c, 23);
 STEP(H, a, b, c, d, W[ 1], 0xa4beea44,  4); STEP(H, d, a, b, c, W[ 4], 0x4bdecfa9, 11);
 STEP(H, c, d, a, b, W[ 7], 0xf6bb4b60, 16); STEP(H, b, c, d, a, W[10], 0xbebfbc70, 23);
 STEP(H, a, b, c, d, W[13], 0x289b7ec6,  4); STEP(H, d, a, b, c, W[ 0], 0xeaa127fa, 11);
 STEP(H, c, d, a, b, W[ 3], 0xd4ef3085, 16); STEP(H, b, c, d, a, W[ 6], 0x04881d05, 23);
 STEP(H, a, b, c, d, W[ 9], 0xd9d4d039,  4); STEP(H, d, a, b, c, W[12], 0xe6db99e5, 11);
 STEP(H, c, d, a, b, W[15], 0x1fa27cf8, 16); STEP(H, b, c, d, a, W[ 2], 0xc4ac5665, 23);
 STEP(I, a, b, c, d, W[ 0], 0xf4292244,  6); STEP(I, d, a, b, c, W[ 7], 0x432aff97, 10);
 STEP(I, c, d, a, b, W[14], 0xab9423a7, 15); STEP(I, b, c, d, a, W[ 5], 0xfc93a039, 21);
 STEP(I, a, b, c, d, W[12], 0x655b59c3,  6); STEP(I, d, a, b, c, W[ 3], 0x8f0ccc92, 10);
 STEP(I, c, d, a, b, W[10], 0xffeff47d, 15); STEP(I, b, c, d, a, W[ 1], 0x85845dd1, 21);
 STEP(I, a, b, c, d, W[ 8], 0x6fa87e4f,  6); STEP(I, d, a, b, c, W[15], 0xfe2ce6e0, 10);
 STEP(I, c, d, a, b, W[ 6], 0xa3014314, 15); STEP(I, b, c, d, a, W[13], 0x4e0811a1, 21);
 STEP(I, a, b, c, d, W[ 4], 0xf7537e82,  6); STEP(I, d, a, b, c, W[11], 0xbd3af235, 10);
 STEP(I, c, d, a, b, W[ 2], 0x2ad7d2bb, 15); STEP(I, b, c, d, a, W[ 9], 0xeb86d391, 21);
 hash[0] += a; hash[1] += b; hash[2] += c; hash[3] += d;
}
inline void md5_init(__private uint* hash) {
    hash[0] = 0x67452301; hash[1] = 0xefcdab89;
    hash[2] = 0x98badcfe; hash[3] = 0x10325476;
}
// --- End of MD5 Implementation ---

// --- Brute-force Kernel (DEBUG VERSION) ---

// Byte-wise comparison helper
inline int compare_hash(__private uint* computed, __global const uchar* target) {
    __private uchar* computed_bytes = (__private uchar*)computed;
    for (int i = 0; i < 16; ++i) {
        if (computed_bytes[i] != target[i]) return 0;
    }
    return 1;
}

__kernel void bruteforce_md5_debug(__global const uchar* target_hash,
                                   __global const uchar* charset,
                                   const int charset_len,
                                   const int password_len, // Should be 1
                                   __global int* result_found, // Unused
                                   __global uchar* found_password, // Unused
                                   __global uchar* debug_output) // New debug buffer
{
    int gid = get_global_id(0);
    // No early exit in debug mode

    // --- Generate Password Candidate (single char) --- 
    uchar current_password[64];
    if (password_len != 1) return; // Only support len 1 in this debug

    // GID corresponds directly to index in charset for len 1
    if (gid >= charset_len) return; // Bounds check
    current_password[0] = charset[gid];
    
    // --- Padding (for len 1) --- 
    current_password[1] = 0x80; // Append 0x80
    for (int i = 2; i < 56; ++i) current_password[i] = 0x00; // Zero padding
    ulong bit_len = (ulong)password_len * 8; // 1 * 8 = 8 bits
    uchar* len_ptr = (uchar*)&bit_len;
    for(int i = 0; i < 8; ++i) current_password[56 + i] = len_ptr[i]; // Append length

    // --- Compute MD5 --- 
    uint hash_state[4];
    md5_init(hash_state);
    uint W_buffer[16];
    for(int i = 0; i < 16; ++i) {
        W_buffer[i] = ((uint)current_password[i*4 + 3] << 24) |
                      ((uint)current_password[i*4 + 2] << 16) |
                      ((uint)current_password[i*4 + 1] <<  8) |
                      ((uint)current_password[i*4 + 0]);
    }
    // Inlined md5_process_block logic:
    __private const uint *W = W_buffer; 
    uint a = hash_state[0]; uint b = hash_state[1]; uint c = hash_state[2]; uint d = hash_state[3];
    // ... STEP calls ...
    STEP(F, a, b, c, d, W[ 0], 0xd76aa478,  7); STEP(F, d, a, b, c, W[ 1], 0xe8c7b756, 12);
    STEP(F, c, d, a, b, W[ 2], 0x242070db, 17); STEP(F, b, c, d, a, W[ 3], 0xc1bdceee, 22);
    STEP(F, a, b, c, d, W[ 4], 0xf57c0faf,  7); STEP(F, d, a, b, c, W[ 5], 0x4787c62a, 12);
    STEP(F, c, d, a, b, W[ 6], 0xa8304613, 17); STEP(F, b, c, d, a, W[ 7], 0xfd469501, 22);
    STEP(F, a, b, c, d, W[ 8], 0x698098d8,  7); STEP(F, d, a, b, c, W[ 9], 0x8b44f7af, 12);
    STEP(F, c, d, a, b, W[10], 0xffff5bb1, 17); STEP(F, b, c, d, a, W[11], 0x895cd7be, 22);
    STEP(F, a, b, c, d, W[12], 0x6b901122,  7); STEP(F, d, a, b, c, W[13], 0xfd987193, 12);
    STEP(F, c, d, a, b, W[14], 0xa679438e, 17); STEP(F, b, c, d, a, W[15], 0x49b40821, 22);
    STEP(G, a, b, c, d, W[ 1], 0xf61e2562,  5); STEP(G, d, a, b, c, W[ 6], 0xc040b340,  9);
    STEP(G, c, d, a, b, W[11], 0x265e5a51, 14); STEP(G, b, c, d, a, W[ 0], 0xe9b6c7aa, 20);
    STEP(G, a, b, c, d, W[ 5], 0xd62f105d,  5); STEP(G, d, a, b, c, W[10], 0x02441453,  9);
    STEP(G, c, d, a, b, W[15], 0xd8a1e681, 14); STEP(G, b, c, d, a, W[ 4], 0xe7d3fbc8, 20);
    STEP(G, a, b, c, d, W[ 9], 0x21e1cde6,  5); STEP(G, d, a, b, c, W[14], 0xc33707d6,  9);
    STEP(G, c, d, a, b, W[ 3], 0xf4d50d87, 14); STEP(G, b, c, d, a, W[ 8], 0x455a14ed, 20);
    STEP(G, a, b, c, d, W[13], 0xa9e3e905,  5); STEP(G, d, a, b, c, W[ 2], 0xfcefa3f8,  9);
    STEP(G, c, d, a, b, W[ 7], 0x676f02d9, 14); STEP(G, b, c, d, a, W[12], 0x8d2a4c8a, 20);
    STEP(H, a, b, c, d, W[ 5], 0xfffa3942,  4); STEP(H, d, a, b, c, W[ 8], 0x8771f681, 11);
    STEP(H, c, d, a, b, W[11], 0x6d9d6122, 16); STEP(H, b, c, d, a, W[14], 0xfde5380c, 23);
    STEP(H, a, b, c, d, W[ 1], 0xa4beea44,  4); STEP(H, d, a, b, c, W[ 4], 0x4bdecfa9, 11);
    STEP(H, c, d, a, b, W[ 7], 0xf6bb4b60, 16); STEP(H, b, c, d, a, W[10], 0xbebfbc70, 23);
    STEP(H, a, b, c, d, W[13], 0x289b7ec6,  4); STEP(H, d, a, b, c, W[ 0], 0xeaa127fa, 11);
    STEP(H, c, d, a, b, W[ 3], 0xd4ef3085, 16); STEP(H, b, c, d, a, W[ 6], 0x04881d05, 23);
    STEP(H, a, b, c, d, W[ 9], 0xd9d4d039,  4); STEP(H, d, a, b, c, W[12], 0xe6db99e5, 11);
    STEP(H, c, d, a, b, W[15], 0x1fa27cf8, 16); STEP(H, b, c, d, a, W[ 2], 0xc4ac5665, 23);
    STEP(I, a, b, c, d, W[ 0], 0xf4292244,  6); STEP(I, d, a, b, c, W[ 7], 0x432aff97, 10);
    STEP(I, c, d, a, b, W[14], 0xab9423a7, 15); STEP(I, b, c, d, a, W[ 5], 0xfc93a039, 21);
    STEP(I, a, b, c, d, W[12], 0x655b59c3,  6); STEP(I, d, a, b, c, W[ 3], 0x8f0ccc92, 10);
    STEP(I, c, d, a, b, W[10], 0xffeff47d, 15); STEP(I, b, c, d, a, W[ 1], 0x85845dd1, 21);
    STEP(I, a, b, c, d, W[ 8], 0x6fa87e4f,  6); STEP(I, d, a, b, c, W[15], 0xfe2ce6e0, 10);
    STEP(I, c, d, a, b, W[ 6], 0xa3014314, 15); STEP(I, b, c, d, a, W[13], 0x4e0811a1, 21);
    STEP(I, a, b, c, d, W[ 4], 0xf7537e82,  6); STEP(I, d, a, b, c, W[11], 0xbd3af235, 10);
    STEP(I, c, d, a, b, W[ 2], 0x2ad7d2bb, 15); STEP(I, b, c, d, a, W[ 9], 0xeb86d391, 21);
    hash_state[0] += a; hash_state[1] += b; hash_state[2] += c; hash_state[3] += d;
    // --- END of MANUAL INLINING --- 

    // --- DEBUG: Write result to debug buffer ---
    int match = compare_hash(hash_state, target_hash);
    int offset = gid * 18; // Calculate offset for this gid

    // Check buffer bounds before writing (optional but safe)
    // Total buffer size is keyspace_size * 18 
    // Max offset is (keyspace_size - 1) * 18
    // Max index written is offset + 17
    // Need offset + 17 < total_buffer_size
    // Need (gid * 18) + 17 < (keyspace_size * 18)
    // Since gid < keyspace_size, this should always hold

    debug_output[offset] = (uchar)match;         // Byte 0: Match result (0 or 1)
    debug_output[offset + 1] = current_password[0]; // Byte 1: Candidate char

    __private uchar* computed_bytes = (__private uchar*)hash_state;
    for (int i = 0; i < 16; ++i) {              // Bytes 2-17: Calculated hash
        debug_output[offset + 2 + i] = computed_bytes[i];
    }
} 