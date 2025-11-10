from fastapi import FastAPI

from app.api.v1.endpoints import chat_endpoint


app = FastAPI()

app.include_router(chat_endpoint.router)


@app.get("/")
async def read_root():
    return {"message": "Diaz AI API documentation."}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)