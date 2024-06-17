import streamlit as st


def authenticated_menu():
    with st.sidebar:
        st.header("Nexus")
        st.page_link("main.py", label="Home")
        st.page_link("pages/search.py", label="Search")
        st.page_link("pages/chat.py", label="Chat")
        st.page_link("pages/build_library.py", label="Build Library")
