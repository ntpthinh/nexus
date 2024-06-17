
import os
import msal
import requests
import streamlit as st
from streamlit_local_storage import LocalStorage

# Configuration
CLIENT_ID = os.getenv("ENTRA_CLIENT_ID")
AUTHORITY = os.getenv("ENTRA_AUTHORITY")
SCOPES = os.getenv("ENTRA_SCOPES").split(',')
CLIENT_SECRET = os.getenv("ENTRA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ENTRA_REDIRECT_URI")
print(CLIENT_ID, AUTHORITY, SCOPES, CLIENT_SECRET, REDIRECT_URI)
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID, client_credential=CLIENT_SECRET, authority=AUTHORITY)

localStorage = LocalStorage()


def get_auth_url():
    auth_url = app.get_authorization_request_url(
        SCOPES, redirect_uri=REDIRECT_URI)
    return auth_url


def get_token_from_code(auth_code):
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    result = app.acquire_token_by_authorization_code(
        auth_code, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    return result['access_token']


def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me', headers=headers)
    return response.json()


def handle_redirect():
    if not st.session_state.get('access_token'):
        code = st.query_params['code']
        access_token = get_token_from_code(code)
        st.session_state['access_token'] = access_token
