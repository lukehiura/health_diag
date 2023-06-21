# auth.py
from authlib.integrations.starlette_client import OAuth
from secrets import token_urlsafe
import secrets
import logging
import base64
import hashlib
from urllib.parse import urlencode
import requests
from fastapi.responses import RedirectResponse
from fastapi import HTTPException, Request
from models import User
from database import session
import os
from dotenv import load_dotenv

load_dotenv()
oauth = OAuth()
state_code_verifier_mapping = {}
print(os.getenv('CLIENT_ID'),"auth.py")

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = os.environ['REDIRECT_URI']


# Fitbit OAuth configuration
oauth.register(
    name='fitbit',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    access_token_url='https://api.fitbit.com/oauth2/token',
    authorize_url='https://www.fitbit.com/oauth2/authorize',
    api_base_url='https://api.fitbit.com/',
    client_kwargs={
        'scope': 'profile',
        'redirect_uri': 'https://0.0.0.0:8000/callback',
    },
)

def authenticate_with_fitbit():
    code_verifier = secrets.token_urlsafe(96)  # 96*8/6 is in the range [43, 128]

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


def callback_handler(request: Request):
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

    token_url = f"https://0.0.0.0:8000/token?code={code}&state={state}&code_verifier={code_verifier}"
    return RedirectResponse(url=token_url)

def token_handler(request):
    # Retrieve the authorization code and state from the request parameters
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    code_verifier = request.query_params.get('code_verifier')


    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    }
    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
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

            # Create a User object and populate its attributes
            first_name = user_data.get('user').get('firstName')
            last_name = user_data.get('user').get('lastName')

            # Create a User object and populate its attributes
            user = User(data=user_data, first_name=first_name, last_name=last_name)

            # Add the User object to the session and commit the changes to the database
            session.add(user)
            session.commit()

            return RedirectResponse(url="/")
        else:
            return {"message": "Failed to retrieve user data"}
    else:
        return {"message": "Failed to retrieve access token"}