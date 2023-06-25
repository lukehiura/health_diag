from fastapi import FastAPI
import requests


app = FastAPI()

FITBIT_API_BASE_URL = 'https://api.fitbit.com'

def get_azm_intraday(user_id: str, date: str, detail_level: str, start_time: str = None, end_time: str = None, access_token: str = None):
    url = f'{FITBIT_API_BASE_URL}/1/user/{user_id}/activities/active-zone-minutes/date/{date}/1d/{detail_level}.json'
    if start_time and end_time:
        url = f'{url}/time/{start_time}/{end_time}.json'

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_activities_intraday(user_id: str, resource: str, date: str, detail_level: str, start_time: str = None, end_time: str = None, access_token: str = None):
    url = f'{FITBIT_API_BASE_URL}/1/user/{user_id}/activities/{resource}/date/{date}/1d/{detail_level}.json'
    if start_time and end_time:
        url = f'{url}/time/{start_time}/{end_time}.json'

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

