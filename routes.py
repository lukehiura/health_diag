# routes.py
from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from database import session
from .auth import authenticate_with_fitbit, callback_handler, token_handler, get_current_username
from intraday import get_azm_intraday, get_activities_intraday
from datetime import date
from uuid import uuid4, UUID
from .models import SessionData
from typing import Optional




router = APIRouter()

state_code_verifier_mapping = {}

@router.get("/")
async def read_root(request: Request):
    home_link = '<a href="/">Home</a>'
    auth_link = '<a href="/auth">Authenticate with Fitbit</a>'
    success_link = '<a href="/success">Success Page</a>'
    reset_link = '<a href="/reset">Reset OAuth Authentication</a>'
    dashboard_link = '<a href="/dashboard">Dashboard</a>'
    azm_link = '<a href="/azm/intraday/user_id/date/detail_level">AZM Intraday</a>'
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
            <li>{azm_link}</li>
        </ul>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)



@router.get("/dashboard")
def redirect_to_fitbit_service():
    return RedirectResponse(url="/auth")


@router.get('/auth')
async def auth():
    return authenticate_with_fitbit()
    

@router.get('/callback')
async def callback(request: Request):
    return callback_handler(request)

@router.get('/token')
async def token(request: Request, session_id: Optional[str] = Depends(get_current_username)):
    return token_handler(request, session_id)
    

@router.get('/success')
async def success(request: Request):
    access_token = request.session.get('access_token')
    reset_link = '<a href="/reset">Reset OAuth Authentication</a>'

    if access_token:
        # Use the access token to make a GET request to the Fitbit user endpoint
        headers = {'Authorization': f'Bearer {access_token}'}
        response = request.get('https://api.fitbit.com/1/user/-/profile.json', headers=headers)

        # If the request was successful, the response should include the user data
        if response.status_code == 200:
            user_data = response.json()
            first_name = user_data.get('user').get('firstName')
            last_name = user_data.get('user').get('lastName')

            # Display the user data along with the token and reset link
            content = f'Token: {access_token}<br>'
            content += f'First Name: {first_name}<br>'
            content += f'Last Name: {last_name}<br>'
            content += reset_link

            return HTMLResponse(content=content)

    # If access token is not available, display a message with the reset link
    content = 'Authentication Successful, but user data could not be retrieved.<br>'
    content += reset_link
    return HTMLResponse(content=content)



@router.get('/reset')
async def reset_oauth(request: Request):
    request.session.pop('token', None)
    response = RedirectResponse(url='/')
    response.delete_cookie(key="session", domain="localhost") # Make sure to set the correct domain
    return response


@router.get("/refresh-cookie")
async def refresh_cookie(response: Response):
    # Set the 'Set-Cookie' header to refresh the cookie
    response.set_cookie(key="cookie_name", value="new_cookie_value", max_age=3600)
    return {"message": "Cookie refreshed"}


@router.get("/azm/intraday/{user_id}/{date}/{detail_level}")
def get_azm_intraday_route(request: Request, user_id: str, date: str, detail_level: str, start_time: str = None, end_time: str = None):
    access_token = request.session.get('token')  # Get the access token from the session
    print(access_token)
    azm_intraday = get_azm_intraday(user_id, date, detail_level, start_time, end_time, access_token)
    if azm_intraday is not None:
        return {"message": "AZM Intraday data retrieved", "azm_intraday": azm_intraday}
    else:
        return {"message": "Failed to retrieve AZM Intraday data"}
    

@router.get("/azm/intraday/{user_id}/{date}/{detail_level}")
def get_azm_intraday_route(request: Request, user_id: str, date: str, detail_level: str, start_time: str = None, end_time: str = None):
    access_token = request.session.get('token')  # Get the access token from the session
    azm_intraday = get_azm_intraday(user_id, date, detail_level, start_time, end_time, access_token)
    if azm_intraday is not None:
        return {"message": "AZM Intraday data retrieved", "azm_intraday": azm_intraday}
    else:
        return {"message": "Failed to retrieve AZM Intraday data"}


@router.get("/intraday/activities/{user_id}/{resource}/{date}/{detail_level}")
def get_intraday_activities_route(request: Request, user_id: str, resource: str, date: str, detail_level: str, start_time: str = None, end_time: str = None):
    access_token = request.session.get('token')  # Get the access token from the session
    intraday_activities = get_activities_intraday(user_id, resource, date, detail_level, start_time, end_time, access_token)
    if intraday_activities is not None:
        return {"message": "Intraday activities retrieved", "intraday_activities": intraday_activities}
    else:
        return {"message": "Failed to retrieve intraday activities"}




# Close the database connection when the application shuts down
@router.on_event("shutdown")
async def close_connection():
    session.close()


@router.post("/session")
async def create_session(session: SessionData):
    session_id = str(uuid4())
    sessions[session_id] = {"username": session.username}
    return {"session_id": session_id}

@router.get("/users/me")
async def read_users_me(username: str = Depends(get_current_username)):
    return {"username": username}