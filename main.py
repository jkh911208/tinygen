import os
import openai
import difflib
import json
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
                    "content": """You are a silent, automated code modification engine. Your sole purpose is to output modified code based on a user request. You will be given a codebase and a prompt, and you must return the new state of the changed files.\n\nFollow these rules strictly:\n1. Your entire response MUST be a single JSON object.\n2. The keys of the JSON object are the file paths (e.g., `src/app.js`).\n3. The values of the JSON object are the complete, new content of the file, from the first line to the last. Do not use code blocks (```) or any other formatting within the content.\n4. For **deleted** files, the value should be an empty string (`""`).\n5. You MUST NOT include any other text, explanations, apologies, or comments outside the JSON object. Your response must be ONLY the JSON object.\n6. Only change the code that is absolutely necessary to complete the user's request. Do not reformat, refactor, or make any other unnecessary changes to the code.\n7. Do not trim or truncate the last newline character if the original file had one. Maintain the exact newline status of the original file.\n\n**Example of a valid response:**\n\n```json\n{\n  "src/app.js": "// new content for app.js\n// ... all lines of the file ...\nconsole.log(\"This is the new app.js\");\n",\n  "src/styles.css": "/* new styles.css file content */\nbody {\n  color: blue;\n}\n",\n  "old/component.js": ""\n}\n```\n\nIn this example, `src/app.js` was modified, `src/styles.css` was created, and `old/component.js` was deleted."""
                },
                {
                    "role": "user",
                    "content": f"Based on the following codebase:\n\n{codebase}\n\nPlease apply this change: {request.prompt}"
                }
            ]
        )
        modified_content_str = response.choices[0].message.content
        # print("###start modified content")
        # print(modified_content_str)
        # print("###finish modified content")

        # Attempt to parse the JSON response
        try:
            modified_files_dict = json.loads(modified_content_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse AI response as JSON: {e}")

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
