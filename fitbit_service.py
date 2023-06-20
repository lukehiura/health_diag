from fastapi import FastAPI, Request, HTTPException, Response
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
app.add_middleware(SessionMiddleware, secret_key="6787d47b2154bae710e4ed2b629e0206b51049875a5c672cbe51f612968ec6dd", session_cookie="session")

state_code_verifier_mapping = {}


CLIENT_ID = "23QYWY"
CLIENT_SECRET = "7f54c9654dded4659eab9898429e7471"
REDIRECT_URI = "https://0.0.0.0:8000/callback"


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
async def auth():
    # Generate a code verifier - a random 128-byte string
    code_verifier = secrets.token_urlsafe(128)

    # Generate a code challenge by hashing the verifier and base64 encoding it
    m = hashlib.sha256()
    m.update(code_verifier.encode('utf-8'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace('=', '')

    # Store the state value in the session
    state = token_urlsafe(16)
    print(state, "before sending")
    state_code_verifier_mapping[state] = code_verifier  # Store the state and code_verifier in the 'database'

    # Build the authorization url and redirect user to Fitbit for authorization
    redirect_uri = "https://0.0.0.0:8000/callback"  # Replace with your desired callback URL
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




# @app.get('/callback')
# async def callback(request: Request):
#     # Simply print or log all the parameters received in the callback
#     logging.info(f'Full callback URL: {request.url}')
#     logging.info(f'Query parameters: {request.query_params}')

#     return {"message": "Callback received", "parameters": dict(request.query_params)}


@app.get('/callback')
async def callback(request: Request):
    # Simply print or log all the parameters received in the callback
    logging.info(f'Full callback URL: {request.url}')
    logging.info(f'Query parameters: {request.query_params}')

    # Verify state to prevent CSRF attacks
    state = request.query_params.get('state')
    print(state, "after sending")
    code_verifier = state_code_verifier_mapping.get(state)
    print(code_verifier)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Retrieve the authorization code
    code = request.query_params.get('code')

    token_url = f"https://0.0.0.0:8000/token?code={code}&state={state}"
    return RedirectResponse(url=token_url)



@app.get('/token')
async def token(request: Request):
    # Retrieve the authorization code and code_verifier from the request parameters
    code = request.query_params.get('code')
    state = request.query_params.get('state')

    # Make a POST request to the Fitbit token endpoint to exchange the code for an access token
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': "https://0.0.0.0:8000/callback",
        'code_verifier': code_verifier,  # This should be the same code_verifier that was used to create the code_challenge during the authorization request
    }
    response = requests.post('https://api.fitbit.com/oauth2/token', headers=headers, data=data)

    # If the request was successful, the response should include an access token
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')

        # Use the access token to make a GET request to the Fitbit user endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://api.fitbit.com/1/user/-/profile.json', headers=headers)

        # If the request was successful, the response should include the user data
        if response.status_code == 200:
            user_data = response.json()
            return {"message": "User data retrieved", "user_data": user_data}
        else:
            return {"message": "Failed to retrieve user data"}
    else:
        return {"message": "Failed to retrieve access token"}



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


@app.get("/refresh-cookie")
async def refresh_cookie(response: Response):
    # Set the 'Set-Cookie' header to refresh the cookie
    response.set_cookie(key="cookie_name", value="new_cookie_value", max_age=3600)
    return {"message": "Cookie refreshed"}


if __name__ == "__main__":
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl=ssl_context)
