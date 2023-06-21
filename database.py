# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USERNAME = os.environ.get('POSTGRES_USERNAME')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_DATABASE = os.environ.get('POSTGRES_DATABASE')

engine = create_engine(
    f'postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}',
    echo=True
)

Session = sessionmaker(bind=engine)
session = Session()

# Create tables in the database if they don't exist
Base.metadata.create_all(bind=engine)
