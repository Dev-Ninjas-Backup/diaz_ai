from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
import os


from app.api.v1.endpoints import jupiter_chat, search_endpoint, florida_search, florida_chat, jupiter_search
from app.api.v1.endpoints.jupiter_search import initialize_jupiter_agent
from app.api.v1.endpoints.florida_search import initialize_florida_agent
from app.api.v1.endpoints.leads import router as leads_router
from app.utils.openapi import custom_openapi


app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.openapi = lambda: custom_openapi(app)

# Initialize CSV agent
try:
    initialize_jupiter_agent("database/process_csv_data_jupiter/process_data.csv")
    initialize_florida_agent("database/process_csv_data_florida/process_data.csv")
except Exception as e:
    print(f"Failed to initialize CSV agent: {e}")

app.add_middleware( CORSMiddleware,
                   allow_origins=[
                       "https://diaz-florida-yacht-frontend.vercel.app",
                       "https://diaz-jupiter-marine-frontend.vercel.app",
                       "http://localhost:3000",
                       "http://localhost:3001",
                       "http://localhost:5173",
                       "http://localhost:5174",
                       "https://development.jupitermarinesales.com",
                       "https://development.floridayachttrader.com",
                       "https://floridayachttrader.com",
                       "https://jupitermarinesales.com",
                       "https://admin.floridayachttrader.com"
                       ],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"], 
                  )

app.include_router(jupiter_chat.router, prefix="/api/v1", tags=["Jupiter Chat"])
#app.include_router(search_endpoint.router, prefix="/api/v1", tags=["Elastic Search"])
app.include_router(jupiter_search.router, prefix="/api/v1", tags=["Jupiter Search"])
app.include_router(leads_router, prefix="/api/v1", tags=["Jupiter Lead Generation"])

app.include_router(florida_chat.router, prefix="/api/v1", tags=[" Florida Chat"])
app.include_router(florida_search.router, prefix="/api/v1", tags=["Florida Search"])
app.include_router(leads_router, prefix="/api/v1", tags=["Jupiter Lead Generation"])


@app.get("/")
async def read_root():
    return {"message": "Diaz AI API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
