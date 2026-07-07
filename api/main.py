from fastapi import FastAPI
from api.routers.postgres import router as postgres_router
from api.routers.mongodb import router as mongodb_router

app = FastAPI(title="Electricity Demand Time Series API")

app.include_router(postgres_router)
app.include_router(mongodb_router)

@app.get("/")
async def root():
    return {"message": "Electricity Demand API is running "}