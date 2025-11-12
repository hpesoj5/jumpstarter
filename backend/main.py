from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.session import Base, engine
from backend.routers import goals, auth

app = FastAPI(title="Goal Tracker API")
app.include_router(goals.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Goal Tracker API is running!"}
