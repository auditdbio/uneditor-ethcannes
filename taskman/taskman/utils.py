"""
Utility functions for taskman.
Contains helper functions for hashing, serialization, and other common operations.
"""
import json
import hashlib
from typing import Any, Union, Callable, List
import asyncio
import threading

# Type definitions
RetryDelayType = Union[int, float, Callable[[int], Union[int, float]]]
SemaphoreType = Any # threading.Semaphore or asyncio.Semaphore


def hash_json(data: Any) -> str:
    """
    Sorts keys, removes extra spaces and returns hex-digest SHA-256.
    
    Args:
        data: Any JSON-serializable object
        
    Returns:
        SHA-256 hex digest of the JSON representation
    """
    # Convert the dictionary to a JSON string. sort_keys=True ensures consistency.
    json_string = json.dumps(data, sort_keys=True, default=str)
    
    # Encode the JSON string to bytes
    encoded_string = json_string.encode('utf-8')
    
    # Compute the SHA256 hash
    hash_object = hashlib.sha256(encoded_string)
    
    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()


def calculate_retry_delay(delay: RetryDelayType, attempt: int) -> Union[int, float]:
    """
    Calculate the delay between retries.
    
    Args:
        delay: Either an integer delay or a function that takes attempt number
        attempt: Current attempt number (0-based)
        
    Returns:
        Delay in seconds
    """
    if callable(delay):
        return delay(attempt)
    return delay


def hash_to_pictogram(hash_string: str, num_chars: int = 4) -> str:
    """Converts a hex hash string to a sequence of unicode pictograms."""
    if not hash_string or len(hash_string) < num_chars * 2 or hash_string == "unknown":
        return ""
    
    pictos = []
    for i in range(num_chars):
        hex_byte = hash_string[i*2 : i*2 + 2]
        try:
            # Map a byte (0-255) to the Unicode range U+1F300-U+1F3FF
            code_point = int(hex_byte, 16)
            pictos.append(chr(0x1F300 + code_point))
        except (ValueError, IndexError):
            return ""  # Return empty if hash is not as expected
    return "".join(pictos) 