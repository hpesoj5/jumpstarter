from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.session import Base, engine
from routers import creation, auth, dashboard, goals

app = FastAPI(title="Goal Tracker API")
app.include_router(creation.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(goals.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://jumpstarter-five.vercel.app"],  # frontend address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Goal Tracker API is running!"}
