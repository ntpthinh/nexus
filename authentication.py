
import os
import time
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
LOGIN_URL = os.getenv("LOGIN_URL")
APPLICATION_URL = os.getenv("APPLICATION_URL")
app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID, client_credential=CLIENT_SECRET, authority=AUTHORITY)
try:
    localS = LocalStorage()
except Exception as e:
    print(e)


def get_auth_url():
    auth_url = app.get_authorization_request_url(
        SCOPES, redirect_uri=REDIRECT_URI)
    return auth_url


def get_token_from_code(auth_code):
    result = app.acquire_token_by_authorization_code(
        auth_code, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    return result['access_token']


def get_user_info_from_access_token(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://graph.microsoft.com/v1.0/me', headers=headers)
    return response.json()


def handle_redirect():
    try:
        code = st.query_params['code']
        st.markdown('Wait a minute...')
        access_token = get_token_from_code(code)

        # st.session_state['access_token'] = access_token
        user_info = get_user_info_from_access_token(access_token)
        set_user_info_in_local_storage(user_info)
        while True:
            time.sleep(0.5)
            user_info = get_user_info(redirect_login=False)
            if user_info:
                break
        nav_to(APPLICATION_URL)
    except Exception as e:
        nav_to(LOGIN_URL)


def get_user_info(redirect_login=True):
    user_info = get_user_info_from_local_storage()
    if not user_info:
        if redirect_login:
            nav_to(LOGIN_URL)
        return
    return user_info


def get_user_info_from_local_storage():
    user_info = localS.getItem("user_info")
    print(user_info)
    return user_info


def set_user_info_in_local_storage(user_info):
    localS.setItem("user_info", user_info)
    print('In gere')
    st.session_state['user_info'] = user_info
    print(st.session_state['user_info'])


def nav_to(url):
    nav_script = """
        <meta http-equiv="refresh" content="0; url='%s'">
    """ % (url)
    st.write(nav_script, unsafe_allow_html=True)
