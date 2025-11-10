from fastapi import FastAPI
from backend.db.session import Base, engine
from backend.routers import goals, auth

app = FastAPI(title="Goal Tracker API")
app.include_router(goals.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Goal Tracker API is running!"}
