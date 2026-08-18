"""FastAPI backend for Qanwas"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Qanwas", description="AI Coding Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Qanwas API", "version": "6.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}