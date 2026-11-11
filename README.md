# MathPractice API

Teachers create math topics and problems. Students solve them and get points.

Run:
    pip install -r requirements.txt
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000/docs

Demo users: 1, 2 = teachers; 3, 4 = students.

Structure:
- app/main.py: creates the app, connects routers
- app/database.py: in-memory dictionaries + demo data
- app/schemas.py: Pydantic models (validation)
- app/services.py: business logic
- app/routers/: endpoints

Workflows:
1. Teacher manages topics and problems
   - only teachers create topics; only the author can edit or delete
   - no two topics with the same title for one teacher
   - a topic with problems can't be deleted
   - a problem's answer can't be changed (and the problem can't be deleted) after students answered it
2. Student solves a problem
   - answer is checked: "5" = "5.0", text ignores case
   - limited attempts; hint is shown after a wrong answer
   - a solved problem can't be solved again
3. Student progress
   - solved problems and score for every topic
