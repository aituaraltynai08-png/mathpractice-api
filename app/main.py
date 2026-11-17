from fastapi import FastAPI

from app.routers import assignments, problems, topics, users

app = FastAPI(title="MathPractice API")

app.include_router(users.router)
app.include_router(topics.router)
app.include_router(problems.router)
app.include_router(assignments.router)


@app.get("/")
def root():
    return {"message": "MathPractice API is running. Open /docs"}
