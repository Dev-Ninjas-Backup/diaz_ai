from fastapi import FastAPI

from app.api.v1.endpoints import chat_endpoint


app = FastAPI()

app.include_router(chat_endpoint.router)


@app.get("/")
async def read_root():
    return {"message": "Diaz AI API documentation."}


