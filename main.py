from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from endpoints import gen

app = FastAPI(default_response_class=ORJSONResponse)

# POST /gen endpoint
app.include_router(gen.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000,
                log_level="debug", reload=True)
