import os
from typing import List, Dict, Any, Generator
from openai import OpenAI

# Initialize the OpenAI client pointing to Moonshot AI
# It will automatically pick up the MOONSHOT_API_KEY environment variable if api_key is omitted,
# but to be safe and explicit, we fetch it here.
def get_client() -> OpenAI:
    api_key = os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        raise ValueError("MOONSHOT_API_KEY environment variable is not set")
        
    return OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1",
    )

def generate_chat_response(messages: List[Dict[str, str]], stream: bool = False) -> Any:
    """
    Generates a response from Kimi K3 based on the provided messages.
    Supports both streaming and non-streaming responses.
    """
    client = get_client()
    
    # We use kimi-k3 as the flagship model, with reasoning effort set to low as requested
    response = client.chat.completions.create(
        model="kimi-k3",
        messages=messages,
        reasoning_effort="low", 
        stream=stream
    )
    
    return response

def stream_chat_response(messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """
    Yields chunks of text from Kimi K3's streaming response.
    It yields reasoning_content first (if any), then the actual content.
    """
    stream = generate_chat_response(messages, stream=True)
    
    thinking = False
    for chunk in stream:
        if not chunk.choices:
            continue
            
        choice = chunk.choices[0]
        
        # Handle reasoning tokens (thinking)
        if choice.delta and hasattr(choice.delta, "reasoning_content") and getattr(choice.delta, "reasoning_content") is not None:
            if not thinking:
                thinking = True
                yield "\n<thinking>\n"
            yield getattr(choice.delta, "reasoning_content")
            
        # Handle actual content tokens
        if choice.delta and choice.delta.content is not None:
            if thinking:
                thinking = False
                yield "\n</thinking>\n\n"
            yield choice.delta.content
