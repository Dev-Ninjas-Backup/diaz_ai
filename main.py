from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.chat_db import engine, ChatBase
import os


from app.api.v1.endpoints import jupiter_chat, jupiter_filter_search, florida_search, florida_chat
# from app.api.v1.endpoints import jupiter_search
# from app.api.v1.endpoints.jupiter_search import initialize_jupiter_agent
from app.api.v1.endpoints.florida_search import initialize_florida_agent
from app.api.v1.endpoints.jupiter_leads import router as leads_router
from app.api.v1.endpoints.jupiter_ai_search import initialize_jupiter_sqlite_agent, router as jupiter_sqlite_router
from app.api.v1.endpoints.florida_ai_search import initialize_florida_sqlite_agent, router as florida_sqlite_router 
from app.utils.openapi import custom_openapi
from app.utils.user_guide_setup import router as user_guide_router
from contextlib import asynccontextmanager

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    async with engine.begin() as conn:
        await conn.run_sync(ChatBase.metadata.create_all)

    # Initialize SQLite agents
    db_path = "boats.db"
    initialize_jupiter_sqlite_agent(db_path=db_path, table_name="jupiter_boats")
    initialize_florida_sqlite_agent(db_path=db_path, table_name="florida_boats")

    # Initialize CSV agent if needed
    # try:
    #     initialize_florida_agent("database/process_csv_data_florida/process_data.csv")
    # except Exception as e:
    #     print(f"Failed to initialize CSV agent: {e}")

    yield  # Everything after this would be shutdown logic if needed

# Create app with lifespan
app = FastAPI(lifespan=lifespan)

app.openapi = lambda: custom_openapi(app)


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
# app.include_router(jupiter_search.router, prefix="/api/v1", tags=["Jupiter Search"])
app.include_router(jupiter_sqlite_router, prefix="/api/v1", tags=["Jupiter AI Search"])
app.include_router(jupiter_filter_search.router, prefix="/api/v1", tags=["Jupiter Filter Search"])
app.include_router(leads_router, prefix="/api/v1", tags=["Jupiter Lead Generation"])

app.include_router(florida_chat.router, prefix="/api/v1", tags=[" Florida Chat"])
# app.include_router(florida_search.router, prefix="/api/v1", tags=["Florida Search"])
app.include_router(florida_sqlite_router, prefix="/api/v1", tags=["Florida AI Search"])

app.include_router(user_guide_router, prefix="/api/v1/utils", tags=["User Guide Setup upload to vector db"])


@app.get("/")
async def read_root():
    return {"message": "Diaz AI API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
