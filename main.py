from fastapi import FastAPI
from app.api.endpoints import insights

app = FastAPI(title="Shopify Store Insights-Fetcher")

app.include_router(insights.router, prefix="/api/v1", tags=["insights"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Shopify Insights-Fetcher API"}