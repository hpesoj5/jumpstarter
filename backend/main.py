from fastapi import FastAPI
from backend.db.session import Base, engine
from backend.routers import goals

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Goal Tracker API")
app.include_router(goals.router)

@app.get("/")
def root():
    return {"message": "Goal Tracker API is running!"}
