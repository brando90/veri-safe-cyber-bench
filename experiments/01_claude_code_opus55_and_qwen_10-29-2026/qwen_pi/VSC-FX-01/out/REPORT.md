## Root Cause Analysis

The original code checked `offset + length > buffer_len` to detect truncation. This condition is equivalent to `(buffer_len - offset) < length`, but the latter explicitly clarifies the intent. The fix ensures that the program correctly rejects archives where the declared length exceeds available bytes, aligning with the documented behavior.