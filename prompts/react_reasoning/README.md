# React Reasoning Prompts

This folder contains the prompts used in the ReAct (Reasoning + Acting) pattern implemented in `utils/react_reasoning.py`.

## Files

### `generate_prompt.md`
The initial response generation prompt used to create a draft response to the user's query.

**Template Variables:**
- `{system_prompt}` - The main chatbot system prompt
- `{context}` - Formatted conversation history
- `{user_input}` - The user's current question/message

### `reflection_prompt.md`
The reflection prompt used to analyze and critique the initial draft response.

**Template Variables:**
- `{user_input}` - The user's original question
- `{draft_response}` - The initial response that needs evaluation

### `revision_prompt.md`
The revision prompt used to improve the response based on reflection feedback.

**Template Variables:**
- `{system_prompt}` - The main chatbot system prompt  
- `{user_input}` - The user's original question
- `{draft_response}` - The initial response that needs improvement
- `{reflection}` - The feedback from the reflection step

## Usage

These prompts are automatically loaded by the `chatbot.prompt_loader` module and used in the ReAct reasoning workflow. They can be accessed via:

```python
from chatbot.prompt_loader import (
    get_react_generate_prompt,
    get_react_reflection_prompt, 
    get_react_revision_prompt
)

# Example usage
generate_content = get_react_generate_prompt({
    "system_prompt": "Your system prompt...",
    "context": "Previous conversation...",
    "user_input": "User's question..."
})
```

## Workflow

1. **Generate** - Creates initial response using `generate_prompt.md`
2. **Reflect** - Analyzes response quality using `reflection_prompt.md`  
3. **Revise** (if needed) - Improves response using `revision_prompt.md`
4. **Finalize** - Returns final response (either revised or original)

## Language

All prompts are in Portuguese to maintain consistency with the fridday-edith-ai chatbot's target audience.
