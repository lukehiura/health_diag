from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import secrets
from secrets import token_urlsafe
import logging
import base64
import hashlib
from urllib.parse import urlencode
import requests
import ssl


ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret-key", session_cookie="session")


CLIENT_ID = "23QYWY"
CLIENT_SECRET = "7f54c9654dded4659eab9898429e7471"
REDIRECT_URI = "https://localhost:8000/callback"


oauth = OAuth()
oauth.register(
    name='fitbit',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url='https://api.fitbit.com/oauth2/token',
    authorize_url='https://www.fitbit.com/oauth2/authorize',
    api_base_url='https://api.fitbit.com/',
    client_kwargs={
        'scope': 'profile',
        'redirect_uri': REDIRECT_URI,
    },
)


def generate_state_token():
    return secrets.token_urlsafe(16)


@app.get("/")
async def read_root(request: Request):
    home_link = '<a href="/">Home</a>'
    auth_link = '<a href="/auth">Authenticate with Fitbit</a>'
    success_link = '<a href="/success">Success Page</a>'
    reset_link = '<a href="/reset">Reset OAuth Authentication</a>'
    dashboard_link = '<a href="/dashboard">Dashboard</a>'
    html_content = f"""
    <html>
    <body>
        <h1>Welcome to the main microservice</h1>
        <ul>
            <li>{home_link}</li>
            <li>{auth_link}</li>
            <li>{success_link}</li>
            <li>{reset_link}</li>
            <li>{dashboard_link}</li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)



@app.get("/dashboard")
def redirect_to_fitbit_service():
    return RedirectResponse(url="/auth")


@app.get('/auth')
async def auth(request: Request):
    # Generate a code verifier - a random 128-byte string
    code_verifier = secrets.token_urlsafe(128)
    request.session['code_verifier'] = code_verifier

    # Generate a code challenge by hashing the verifier and base64 encoding it
    m = hashlib.sha256()
    m.update(code_verifier.encode('utf-8'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')

    # Store the state value in the session
    state = token_urlsafe(16)
    request.session['state'] = state

    # Build the authorization url and redirect user to Fitbit for authorization
    redirect_uri = "https://your-domain.com/callback"  # Replace with your desired callback URL
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "activity cardio_fitness electrocardiogram heartrate location nutrition oxygen_saturation profile respiratory_rate settings sleep social temperature weight",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = f"https://www.fitbit.com/oauth2/authorize?{urlencode(params)}"
    
    return RedirectResponse(url=authorize_url)




@app.get('/callback')
async def callback(request: Request):
    # Get the code verifier from the session
    code_verifier = request.session.get('code_verifier')

    # Get the authorization code from the query string
    code = request.query_params.get('code')
    logging.info(f'Full callback URL: {request.url}')
    received_state = request.query_params.get('state')
    logging.info(f'Received state: {received_state}')
    stored_state = request.session.get('state')
    logging.info(f'Stored state: {stored_state}')

    if received_state != stored_state:
        raise HTTPException(status_code=400, detail="CSRF Warning! State mismatch")

    # Prepare request for access token with code and verifier
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    }
    data = {
        'clientId': CLIENT_ID,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': code,
        'code_verifier': code_verifier
    }

    response = requests.post('https://api.fitbit.com/oauth2/token', headers=headers, data=data)

    # Check if the request was successful
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch access token")

    token_data = response.json()
    request.session['token'] = token_data

    # You can access the user data from the token_data here or perform additional actions
    # based on the received data.

    return JSONResponse(content=token_data)



@app.get('/success')
async def success(request: Request):
    token = request.session.get('token')
    reset_link = '<a href="/reset">Reset OAuth Authentication</a>'
    return HTMLResponse(content=f'Token: {token}<br>{reset_link}')


@app.get('/reset')
async def reset_oauth(request: Request):
    request.session.pop('token', None)
    response = RedirectResponse(url='/')
    response.delete_cookie(key="session", domain="localhost") # Make sure to set the correct domain
    return response


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl=ssl_context)
