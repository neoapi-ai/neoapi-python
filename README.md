# NeoAPI SDK

The official Python SDK for integrating neoapi.ai LLM Analytics with your LLM pipelines. Track, analyze, and optimize your Language Model outputs with real-time analytics.

## Installation

```bash
pip install neoapi-sdk
```

## Quick Start Guide

First, set your API key as an environment variable:
```bash
export NEOAPI_API_KEY="your-api-key"
```

### Basic Usage
```python
from neoapi import NeoApiClientSync, track_llm_output

# The context manager handles client lifecycle automatically
with NeoApiClientSync() as client:
    # Decorate your LLM function to track its outputs
    @track_llm_output(client=client)
    def get_llm_response(prompt: str) -> str:
        # Your LLM logic here
        return "AI generated response"
    
    # Use your function normally
    response = get_llm_response("What is machine learning?")
```

### Async Support
```python
import asyncio
from neoapi import NeoApiClientAsync, track_llm_output

async def main():
    async with NeoApiClientAsync() as client:
        @track_llm_output(
            client=client,
            project="chatbot",
            need_analysis_response=True  # Get analytics feedback
        )
        async def get_llm_response(prompt: str) -> str:
            # Your async LLM logic here
            await asyncio.sleep(0.1)  # Simulated API call
            return "Async AI response"
        
        response = await get_llm_response("Explain async programming")

# Run your async code
asyncio.run(main())
```

### OpenAI Integration Example
```python
from openai import OpenAI
from neoapi import NeoApiClientSync, track_llm_output

def chat_with_gpt():
    openai_client = OpenAI()  # Uses OPENAI_API_KEY env variable
    
    with NeoApiClientSync() as neo_client:
        @track_llm_output(
            client=neo_client,
            project="gpt4_chat",
            need_analysis_response=True,  # Get quality metrics
            format_json_output=True       # Pretty-print analytics
        )
        def ask_gpt(prompt: str) -> str:
            response = openai_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini"
            )
            return response.choices[0].message.content

        # Use the tracked function
        response = ask_gpt("What are the key principles of clean code?")
        print(response)  # Analytics will be logged automatically
```

## Key Features

- 🔄 **Automatic Tracking**: Decorator-based output monitoring
- ⚡ **Async Support**: Built for high-performance async applications
- 🔍 **Real-time Analytics**: Get immediate feedback on output quality
- 🛠 **Flexible Integration**: Works with any LLM provider
- 🔧 **Configurable**: Extensive customization options
- 🔐 **Secure**: Environment-based configuration

## Configuration Options

### Environment Variables

```bash
# Required
export NEOAPI_API_KEY="your-api-key"


### Client Configuration
```python
client = NeoApiClientSync(
    # Basic settings
    api_key="your-api-key",      # Optional if env var is set
    check_frequency=1,           # Process every Nth output
    
    # Performance tuning
    batch_size=10,               # Outputs per batch
    flush_interval=5.0,          # Seconds between flushes
    max_retries=3,              # Retry attempts on failure
    
    # Advanced options
    api_url="custom-url",        # Optional API endpoint
    max_batch_size=100,         # Maximum batch size
)
```

### Decorator Options
```python
@track_llm_output(
    client=client,
    
    # Organization
    project="my_project",        # Project identifier
    group="experiment_a",        # Subgroup within project
    analysis_slug="v1.2",        # Version or analysis identifier
    
    # Analytics
    need_analysis_response=True, # Get quality metrics
    format_json_output=True,     # Pretty-print analytics
    
    # Custom data
    metadata={                   # Additional tracking info
        "model": "gpt-4",
        "temperature": 0.7,
        "user_id": "user123"
    },
    save_text=True              # Store output text
)
```

## Best Practices

1. **Use Context Managers**: They handle client lifecycle automatically
   ```python
   with NeoApiClientSync() as client:
       # Your code here
   ```

2. **Group Related Outputs**: Use project and group parameters
   ```python
   @track_llm_output(client=client, project="chatbot", group="user_support")
   ```

3. **Add Relevant Metadata**: Include context for better analysis
   ```python
   @track_llm_output(
       client=client,
       metadata={"user_type": "premium", "session_id": "abc123"}
   )
   ```

## Resources

- 📚 [Full Documentation](https://www.neoapi.ai/docs)
- 💻 [GitHub Repository](https://github.com/neoapi-ai/neoapi-python)
- 🤝 [Support](mailto:hello@neoapi.ai)
- 📝 [API Reference](https://www.neoapi.ai/docs/api)

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details
