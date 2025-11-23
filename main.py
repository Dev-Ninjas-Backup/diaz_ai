from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os


from app.api.v1.endpoints import chat_endpoint, search_endpoint, search
from app.api.v1.endpoints.search import initialize_agent
from app.utils.openapi import custom_openapi


app = FastAPI()

app.openapi = lambda: custom_openapi(app)

# Initialize CSV agent
try:
    initialize_agent("database/process_csv_data/process_data.csv")
except Exception as e:
    print(f"Failed to initialize CSV agent: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://development.jupitermarinesales.com",
        "https://jupitermarinesales.com",
        "https://development.floridayachttrader.com",
        "https://floridayachttrader.com",
        "https://admin.floridayachttrader.com",
        "https://diaz-florida-yacht-frontend.vercel.app",
        "https://florida-yacht-dashboard.pages.dev",
        "https://diaz-jupiter-marine-frontend.vercel.app",
        "http://16.171.46.71:3000",
        "http://16.171.46.71:4173",
        "http://13.50.239.13:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "HEAD", "PUT", "PATCH", "POST", "DELETE"],
    allow_headers=["*"],
)


app.include_router(chat_endpoint.router, prefix="/api/v1", tags=["Chat"])
app.include_router(search_endpoint.router, prefix="/api/v1", tags=["Elastic Search"])
app.include_router(search.router, prefix="/api/v1", tags=["CSV Search"])


@app.get("/")
async def read_root():
    return {"message": "Diaz AI API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
