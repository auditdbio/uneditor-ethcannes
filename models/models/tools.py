import json
from typing import Any, Dict, Tuple
import re

def parse_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract the last JSON object or array from arbitrary text in linear time.
    """

    def _is_escaped(s: str, pos: int) -> bool:
        """
        Return True if the character at s[pos] is escaped by an odd number of backslashes.
        """
        backslashes = 0
        j = pos - 1
        while j >= 0 and s[j] == '\\':
            backslashes += 1
            j -= 1
        return (backslashes % 2) == 1

    s = text.rstrip()
    search_end = len(s)
    
    while search_end > 0:
        end_brace = s.rfind('}', 0, search_end)
        end_bracket = s.rfind(']', 0, search_end)
        end = max(end_brace, end_bracket)
        
        if end == -1:
            break
        
        try:
            balance = 0
            in_string = False
            start = None
            
            for i in range(end, -1, -1):
                ch = s[i]
                if ch == '"' and not _is_escaped(s, i):
                    in_string = not in_string
                
                if not in_string:
                    if ch in ('}', ']'):
                        balance += 1
                    elif ch in ('{', '['):
                        balance -= 1
                        if balance == 0:
                            start = i
                            break
            
            if start is None:
                search_end = end
                continue
            
            candidate = s[start : end + 1]
            return json.loads(candidate)
            
        except json.JSONDecodeError:
            search_end = end
    
    raise ValueError("No valid JSON found in the text") 

def exponential_backoff(n_try:int) -> int:
    return 2 ** n_try


def extract_metadata(text: str) -> Dict[str, Any]:
    """
    Extract metadata from markdown text.
    
    Args:
        text: The markdown text containing metadata section
        
    Returns:
        Dict[str, Any]: Parsed metadata as dictionary
        
    Raises:
        ValueError: If no metadata section found
    """
    metadata_pattern = r"###\s*Metadata\s*[\r\n]+(.*?)(?=\n\s*###|\Z)"
    metadata_match = re.search(metadata_pattern, text, re.DOTALL | re.IGNORECASE)
    if not metadata_match:
        raise ValueError("No metadata found")
    metadata = metadata_match.group(1).strip()
    return parse_json_from_text(metadata)


def remove_metadata_from_text(text: str) -> str:
    """
    Remove the metadata section from the markdown text.
    
    Args:
        text: The markdown text containing sections
        
    Returns:
        str: The text with metadata section removed
    """
    # Use same pattern as extract_metadata for consistency
    metadata_pattern = r"###\s*Metadata\s*[\r\n]+(.*?)(?=\n\s*###|\Z)"
    match = re.search(metadata_pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return text
    
    # Remove the entire metadata section
    start = match.start()
    end = match.end()
    return text[:start] + text[end:]


def extract_and_remove_metadata(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract metadata and remove it from text in a single pass.
    
    Args:
        text: The markdown text containing metadata section
        
    Returns:
        Tuple[Dict[str, Any], str]: Parsed metadata and cleaned text
        
    Raises:
        ValueError: If no metadata section found
    """
    # Single regex search for efficiency
    metadata_pattern = r"###\s*Metadata\s*[\r\n]+(.*?)(?=\n\s*###|\Z)"
    match = re.search(metadata_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not match:
        raise ValueError("No metadata found")
    
    # Extract metadata content
    metadata_content = match.group(1).strip()
    metadata = parse_json_from_text(metadata_content)
    
    # Remove metadata section from text
    start = match.start()
    end = match.end()
    cleaned_text = text[:start] + text[end:]
    
    return metadata, cleaned_text