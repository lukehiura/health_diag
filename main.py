from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import requests
import uvicorn

app = FastAPI()

@app.get("/dashboard")
def redirect_to_fitbit_service():
    return RedirectResponse(url="http://localhost:8000/auth")

@app.get("/")
def read_root():
    return {"message": "Welcome to the main microservice"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
