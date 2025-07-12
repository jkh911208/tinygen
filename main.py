import os
import openai
import difflib
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from git import Git

# Get the OpenAI API key from an environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

app = FastAPI(default_response_class=ORJSONResponse)

class GenRequest(BaseModel):
    url: str
    prompt: str

@app.post("/gen")
async def generate(request: GenRequest):
    git = Git(request.url)

    if not git.verify_access():
        raise HTTPException(status_code=400, detail="Failed to verify access to the git repository.")

    if not git.is_cloned():
        git.clone()

    codebase = git.get_codebase()

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a silent, automated code modification engine. Your sole purpose is to output modified code based on a user request. You will be given a codebase and a prompt, and you must return the new state of the changed files.

Follow these rules strictly:
1. Your entire response will consist of one or more file blocks.
2. Each file block begins with a separator line: `--- FILE_PATH: [path/to/your/file.ext] ---`
3. For **modified** or **newly created** files, the separator line is followed by the complete, new content of the file, from the first line to the last. Do not use code blocks (```) or any other formatting.
4. For **deleted** files, the separator line is followed by absolutely nothing. The content is empty.
5. You MUST NOT include any other text, explanations, apologies, or comments. Your response must be only the file blocks.
6. Only change the code that is absolutely necessary to complete the user's request. Do not reformat, refactor, or make any other unnecessary changes to the code.
7. Do not trim or truncate the last newline character if the original file had one. Maintain the exact newline status of the original file.

**Example of a valid response:**

--- FILE_PATH: src/app.js ---
// new content for app.js
// ... all lines of the file ...
console.log("This is the new app.js");
--- FILE_PATH: src/styles.css ---
/* new styles.css file content */
body {
  color: blue;
}
--- FILE_PATH: old/component.js ---

In this example, `src/app.js` was modified, `src/styles.css` was created, and `old/component.js` was deleted."""
                },
                {
                    "role": "user",
                    "content": f"Based on the following codebase:\n\n{codebase}\n\nPlease apply this change: {request.prompt}"
                }
            ]
        )
        modified_content = response.choices[0].message.content
        print("###start modified content")
        print(modified_content)
        print("###finish modified content")
        diffs = {}
        file_separator = '--- FILE_PATH: '
        modified_files = modified_content.split(file_separator)

        for file_block in modified_files:
            if not file_block.strip():
                continue

            try:
                path, new_code = file_block.split(' ---', 1)
                path = path.strip()

                original_code = codebase.get(path, '')
                diff = difflib.unified_diff(
                    original_code.splitlines(keepends=True),
                    new_code.splitlines(keepends=True),
                    fromfile=f'a/{path}',
                    tofile=f'b/{path}',
                )
                diffs[path] = ''.join(diff)
            except ValueError:
                # Handle cases where the split doesn't work as expected
                print(f"Could not parse file block: {file_block}")
                continue

        for file, diff in diffs.items():
            print(f"###--- FILE_PATH: {file} ---###")
            print(diff)
            print("###--- END FILE_PATH ---###")

        return diffs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error from OpenAI API: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000,
                log_level="debug", reload=True)
