from utils import calculate_diffs, call_openai,SYSTEM_PROMPT
import orjson
from fastapi import FastAPI, HTTPException
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from git import Git

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

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Based on the following codebase:\n\n{codebase}\n\nPlease apply this change: {request.prompt}"}
    ]

    try:
        # First attempt
        content_str = call_openai(messages)

        try:
            messages.extend([
                {"role": "assistant", "content": content_str},
                {"role": "user", "content": "Now, critically review your own work. Ensure that the code modifications are not only syntactically correct but also logically sound and align with the user's original request. Verify that the code is executable and free of new bugs."}
            ])
            modified_files_dict = orjson.loads(content_str)
            messages[-1]["content"] = "Your previous response was successfully parsed as a JSON object. " + messages[-1]["content"]
        except orjson.JSONDecodeError as e:
            print(f"First attempt JSON parsing failed: {e}. Attempting self-correction...")
            # Self-correction attempt
            messages[-1]["content"] = "The previous response was not a valid JSON object. Please provide the complete and correct JSON object as specified in the system prompt. Do not include any other text or explanations. " + messages[-1]["content"]

        content_str = call_openai(messages)
        # print("###start corrected content")
        # print(content_str)
        # print("###finish corrected content")

        try:
            modified_files_dict = orjson.loads(content_str)
        except orjson.JSONDecodeError as e_corrected:
            raise HTTPException(status_code=500, detail=f"Self-correction failed: Failed to parse AI response as JSON: {e_corrected}. Original error: {e}")

        diffs = calculate_diffs(modified_files_dict, codebase)

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
