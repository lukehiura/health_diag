# main.py
import uvicorn
from fastapi import FastAPI
from routes import router
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import os

load_dotenv()

print(os.environ['SECRET_KEY'])
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ['SECRET_KEY'], session_cookie="session")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
    )

# uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
