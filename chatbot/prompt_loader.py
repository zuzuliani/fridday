"""
Utility functions for loading prompts from files using LangChain PromptTemplates.
"""
import os
from pathlib import Path
from langchain.prompts import PromptTemplate
from typing import Dict, Any, Optional


def load_prompt_template(prompt_name: str, subfolder: str = None, file_extension: str = None) -> PromptTemplate:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        subfolder: Optional subfolder within prompts directory
        file_extension: File extension to use (.md, .txt). If None, tries .md first, then .txt
        
    Returns:
        LangChain PromptTemplate object
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    template_content = _load_prompt_file(prompt_name, subfolder, file_extension)
    return PromptTemplate.from_template(template_content)


def load_prompt(prompt_name: str, subfolder: str = None, file_extension: str = None, 
                variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Load and format a prompt from the prompts directory.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        subfolder: Optional subfolder within prompts directory
        file_extension: File extension to use (.md, .txt). If None, tries .md first, then .txt
        variables: Optional dictionary of variables to format the template
        
    Returns:
        Formatted prompt content
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    template = load_prompt_template(prompt_name, subfolder, file_extension)
    
    if variables:
        result = template.format(**variables)
        return result
    else:
        # Return the template as-is if no variables provided
        return template.template


def _load_prompt_file(prompt_name: str, subfolder: str = None, file_extension: str = None) -> str:
    """
    Internal function to load prompt file content.
    
    Args:
        prompt_name: Name of the prompt file (without extension)
        subfolder: Optional subfolder within prompts directory
        file_extension: File extension to use (.md, .txt). If None, tries .md first, then .txt
        
    Returns:
        Raw content of the prompt file
        
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


def get_chatbot_system_prompt(variables: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the system prompt for the chatbot.
    
    Args:
        variables: Optional dictionary of variables to customize the prompt
    
    Returns:
        The chatbot system prompt content (formatted if variables provided)
    """
    if variables:
        return load_prompt("system_prompt", "chatbot", variables=variables)
    else:
        # When no variables provided, load template and use default values
        default_variables = {
            "username": "Usuário",
            "companyName": "sua empresa",
            "userRole": "Profissional",
            "userFunction": "cargo atual",
            "communication_tone": "",
            "additional_guidelines": ""
        }
        return load_prompt("system_prompt", "chatbot", variables=default_variables)


def get_chatbot_system_prompt_template() -> PromptTemplate:
    """
    Get the system prompt template for the chatbot.
    
    Returns:
        LangChain PromptTemplate object for the chatbot system prompt
    """
    return load_prompt_template("system_prompt", "chatbot")


# React Reasoning Prompt Functions
def get_react_generate_prompt(variables: Dict[str, Any]) -> str:
    """
    Get the generate prompt for react reasoning.
    
    Args:
        variables: Dictionary containing system_prompt, context, and user_input
    
    Returns:
        Formatted generate prompt content
    """
    return load_prompt("generate_prompt", "react_reasoning", variables=variables)


def get_react_reflection_prompt(variables: Dict[str, Any]) -> str:
    """
    Get the reflection prompt for react reasoning.
    
    Args:
        variables: Dictionary containing user_input and draft_response
    
    Returns:
        Formatted reflection prompt content
    """
    return load_prompt("reflection_prompt", "react_reasoning", variables=variables)


def get_react_revision_prompt(variables: Dict[str, Any]) -> str:
    """
    Get the revision prompt for react reasoning.
    
    Args:
        variables: Dictionary containing system_prompt, user_input, draft_response, and reflection
    
    Returns:
        Formatted revision prompt content
    """
    return load_prompt("revision_prompt", "react_reasoning", variables=variables)
