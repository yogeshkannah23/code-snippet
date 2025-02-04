from fastapi import FastAPI

import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers.code_generation import router

load_dotenv()

app = FastAPI()
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
