import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from fastapi_sessions import SessionManager
from fastapi_sessions.backends import InMemoryBackend
from fastapi_sessions.frontends import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier
from routes import router
import os

load_dotenv()

# Create session frontend
cookie_params = CookieParameters()
session_frontend = SessionCookie(
    cookie_name="session_cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key=os.environ['COOKIE_KEY'],
    cookie_params=cookie_params,
)

# Create session backend
session_backend = InMemoryBackend()

# Create session verifier
class BasicVerifier(SessionVerifier):
    async def verify_session(self, session_id: str) -> bool:
        # Verify if the session exists in the backend
        return await session_backend.exists(session_id)

session_verifier = BasicVerifier()

app = FastAPI()
app.add_middleware(SessionManager, secret_key=os.environ['SECRET_KEY'])

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
