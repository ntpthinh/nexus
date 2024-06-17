
import logging
import os
import sys
import streamlit as st
import dotenv

from authentication import get_auth_url, nav_to
from menu import authenticated_menu
sys.path.append(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir, os.pardir
))
dotenv_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir, os.pardir, '.env'
)
dotenv.load_dotenv()  # noqa


logging.basicConfig(
    stream=sys.stdout, level=logging.INFO
)  # logging.DEBUG for more verbose output
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


def app():

    from authentication import get_user_info, handle_redirect
    if 'code' in st.query_params:
        handle_redirect()
    user_info = get_user_info(redirect_login=False)
    if user_info:
        render_app(user_info)
    else:
        with st.sidebar:
            st.header("Login")
        st.markdown("# Welcome to Nexus!  \n Please login to continue.")
        if st.button("Login with Microsoft"):
            auth_url = get_auth_url()
            nav_to(auth_url)


def render_app(user_info):
    authenticated_menu()

    st.markdown(f'## Hi {user_info['displayName']}')
    st.markdown("Welcome to Nexus, the intelligent search platform that goes beyond keywords to unlock a world of interconnected knowledge.")
    st.markdown("To get started, upload PDF files to build your personal knowledge. You can search across all your uploaded files or chat with your personal library.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Upload PDF"):
            st.switch_page("pages/build_library.py")
    with col2:
        if st.button("Search"):
            st.switch_page("pages/search.py")


app()
