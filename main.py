import os
import uuid
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import (Cookie, Depends, FastAPI, Form, HTTPException, Request,
                     Response, status)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import Base, engine, get_db

# Load environment variables from .env file
load_dotenv()

# Create all database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BabyLog API")

# CORS settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

templates = Jinja2Templates(directory="templates")

# --- Authentication ---
FAMILY_PASSCODE = os.getenv("FAMILY_PASSCODE", "1234")
AUTH_COOKIE_NAME = "babylog_auth"

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Allow access to login, auth, docs, and static files without auth
    if any(path in request.url.path for path in ["/login", "/auth", "/docs", "/openapi.json"]):
        response = await call_next(request)
        return response

    token = request.cookies.get(AUTH_COOKIE_NAME)
    if token != FAMILY_PASSCODE:
        return RedirectResponse(url="/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    response = await call_next(request)
    return response

# --- Frontend Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/auth")
async def handle_login(response: Response, passcode: str = Form(...)):
    if passcode == FAMILY_PASSCODE:
        response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key=AUTH_COOKIE_NAME, value=passcode, httponly=True)
        return response
    else:
        # Redirect back to login with an error message (optional)
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

# --- API Routes ---

@app.post("/api/events", response_model=schemas.Event, status_code=status.HTTP_201_CREATED)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db=db, event=event)

@app.get("/api/events", response_model=List[schemas.Event])
def read_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.get_events(db=db, start_date=start_date, end_date=end_date, skip=skip, limit=limit)

@app.get("/api/events/{event_id}", response_model=schemas.Event)
def read_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    db_event = crud.get_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@app.put("/api/events/{event_id}", response_model=schemas.Event)
def update_event(event_id: uuid.UUID, event: schemas.EventUpdate, db: Session = Depends(get_db)):
    db_event = crud.update_event(db, event_id=event_id, event_data=event)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@app.delete("/api/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    db_event = crud.delete_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/api/prediction", response_model=schemas.Prediction)
def get_prediction(db: Session = Depends(get_db)):
    return crud.get_next_milk_prediction(db=db)

# Example of how to run with uvicorn:
# uvicorn main:app --reload
