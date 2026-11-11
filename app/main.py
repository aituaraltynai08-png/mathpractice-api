from fastapi import FastAPI

from app import database
from app.routers import problems, topics, users

app = FastAPI(title="MathPractice API")

database.add_demo_data()

app.include_router(users.router)
app.include_router(topics.router)
app.include_router(problems.router)


@app.get("/")
def root():
    return {"message": "MathPractice API is running. Open /docs"}
