import os
from pathlib import Path
from typing import List, Optional

MEMORY_DIR = Path(__file__).parent.parent / "memory"

def ensure_memory_dir():
    """Ensure the memory directory exists."""
    os.makedirs(MEMORY_DIR, exist_ok=True)

def save_memory(topic: str, content: str) -> str:
    """
    Saves a markdown memory file.
    Args:
        topic: The topic/filename (e.g., 'user_preferences')
        content: The markdown content to save.
    Returns:
        The path to the saved file.
    """
    ensure_memory_dir()
    
    # Sanitize the topic name for safe filesystem usage
    safe_topic = "".join(c for c in topic if c.isalnum() or c in ("_", "-")).strip()
    if not safe_topic:
        raise ValueError("Invalid topic name")
        
    file_path = MEMORY_DIR / f"{safe_topic}.md"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return str(file_path)

def read_memory(topic: str) -> Optional[str]:
    """Reads a memory file by topic."""
    safe_topic = "".join(c for c in topic if c.isalnum() or c in ("_", "-")).strip()
    file_path = MEMORY_DIR / f"{safe_topic}.md"
    
    if not file_path.exists():
        return None
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def list_memories() -> List[str]:
    """Lists all available memory topics."""
    ensure_memory_dir()
    
    memories = []
    for file in MEMORY_DIR.glob("*.md"):
        memories.append(file.stem) # stem removes the .md extension
    
    return memories
