import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL" )
    SQLALCHEMY_TRACK_MODIFICATIONS = False