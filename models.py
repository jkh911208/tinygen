from pydantic import BaseModel


class GenRequest(BaseModel):
    url: str
    prompt: str
