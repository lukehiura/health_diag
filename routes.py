# routes.py
from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from database import session
from auth import authenticate_with_fitbit, callback_handler, token_handler



router = APIRouter()

state_code_verifier_mapping = {}

@router.get("/")
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
async def token(request: Request):
    return token_handler(request)
    

@router.get('/success')
async def success(request: Request):
    token = request.session.get('token')
    reset_link = '<a href="/reset">Reset OAuth Authentication</a>'
    return HTMLResponse(content=f'Token: {token}<br>{reset_link}')


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

# Close the database connection when the application shuts down
@router.on_event("shutdown")
async def close_connection():
    session.close()