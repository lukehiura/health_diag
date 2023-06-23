import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
from dotenv import load_dotenv
from .routes import router
import redis  # Import the redis library


from .auth import authenticate_with_fitbit, callback_handler, token_handler

load_dotenv()

app = FastAPI()

r = redis.Redis(host='localhost', port=6379, db=0)

# Dependency
def get_current_username(session_id: str):
    session_data = r.get(session_id)  # Use r.get to fetch data from Redis
    if not session_data:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    return session_data.decode()  # Decode from bytes to string

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )
