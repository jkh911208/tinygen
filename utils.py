import difflib
import os
import openai
import functools

# Get the OpenAI API key from an environment variable
key = ""

# Use AsyncOpenAI for non-blocking API calls
client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", key))

if not client.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

def log_function_call_async(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"Calling function: {func.__name__}")
        print(f"  Arguments: args={args}, kwargs={kwargs}")
        result = await func(*args, **kwargs)
        print(f"  Function {func.__name__} returned: {result}")
        return result
    return wrapper



@log_function_call_async
async def call_openai_async(messages: list, model="gpt-4o-mini") -> str:
    """Calls the OpenAI API asynchronously."""
    response = await client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content


def call_openai(messages: list, model="gpt-4o-mini") -> str:
    """Calls the OpenAI API synchronously.
    Note: This is for legacy purposes and new implementations should use call_openai_async.
    """
    # Re-initialize a synchronous client for this specific call if needed elsewhere,
    # or refactor existing synchronous calls to be async.
    sync_client = openai.OpenAI(api_key=client.api_key)
    response = sync_client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def calculate_diffs(modified_files_dict, codebase):
    diffs = {}
    for path, new_code in modified_files_dict.items():
        original_code = codebase.get(path, '')
        diff = difflib.unified_diff(
            original_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f'a/{path}',
            tofile=f'b/{path}',
        )
        diffs[path] = ''.join(diff)
    return diffs


SYSTEM_PROMPT = """You are a silent, automated code modification engine. Your sole purpose is to output modified code based on a user request. You will be given a codebase and a prompt, and you must return the new state of the changed files.

Follow these rules strictly:
1. Your entire response MUST be a single JSON object.
2. The keys of the JSON object are the file paths (e.g., `src/app.js`).
3. The values of the JSON object are the complete, new content of the file, from the first line to the last. All special characters within the content (e.g., backslashes `\`, double quotes `"`) MUST be properly JSON-escaped. For example, a literal backslash `\` should be `\\`, and a literal double quote `"` should be `\"`. Do not over-escape. Do not use code blocks (```) or any other formatting within the content.
4. For **deleted** files, the value should be an empty string (`""`).
5. You MUST NOT include any other text, explanations, apologies, or comments outside the JSON object. Your response must be ONLY the JSON object.
6. Only change the code that is absolutely necessary to complete the user's request. Do not reformat, refactor, or make any other unnecessary changes to the code.
7. Do not trim or truncate the last newline character if the original file had one. Maintain the exact newline status of the original file.

**Example of a valid response:**

```json
{
  "src/app.js": "// new content for app.js\n// ... all lines of the file ...\nconst path = \"C:\\Users\\\";\nconsole.log(\"This is the new app.js\");\n",
  "src/styles.css": "/* new styles.css file content */\nbody {\n  color: blue;\n}\n",
  "old/component.js": ""
}
```

In this example, `src/app.js` was modified, `src/styles.css` was created, and `old/component.js` was deleted."""
