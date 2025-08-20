"""
Utility functions for loading prompts from files.
"""
import os
from pathlib import Path


def load_prompt(prompt_name: str, subfolder: str = None, file_extension: str = None) -> str:
    """
    Load a prompt from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        subfolder: Optional subfolder within prompts directory
        file_extension: File extension to use (.md, .txt). If None, tries .md first, then .txt
        
    Returns:
        Content of the prompt file
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    # Get the project root directory (parent of chatbot directory)
    project_root = Path(__file__).parent.parent
    prompts_dir = project_root / "prompts"
    
    # If no extension specified, try .md first, then .txt
    if file_extension is None:
        extensions_to_try = ['.md', '.txt']
    else:
        extensions_to_try = [file_extension if file_extension.startswith('.') else f'.{file_extension}']
    
    for ext in extensions_to_try:
        if subfolder:
            prompt_path = prompts_dir / subfolder / f"{prompt_name}{ext}"
        else:
            prompt_path = prompts_dir / f"{prompt_name}{ext}"
        
        if prompt_path.exists():
            with open(prompt_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
    
    # If we get here, no file was found
    if subfolder:
        search_path = prompts_dir / subfolder / f"{prompt_name}.*"
    else:
        search_path = prompts_dir / f"{prompt_name}.*"
    
    raise FileNotFoundError(f"Prompt file not found: {search_path} (tried extensions: {extensions_to_try})")


def get_chatbot_system_prompt() -> str:
    """
    Get the system prompt for the chatbot.
    
    Returns:
        The chatbot system prompt content
    """
    return load_prompt("system_prompt", "chatbot")
