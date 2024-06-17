
import dotenv
dotenv.load_dotenv()  # noqa

import llm
import authentication
import streamlit as st
import sys
import logging


logging.basicConfig(
    stream=sys.stdout, level=logging.INFO
)  # logging.DEBUG for more verbose output
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))



def app():
    setup_authentication()

    files = st.file_uploader("Upload a file", type=[
        "pdf"], accept_multiple_files=True)
    if files is not None:
        from pypdf import PdfReader

        for file in files:
            pdf_reader = PdfReader(file)
            full_text = '\n'.join([page.extract_text()
                                   for page in pdf_reader.pages])
            st.write(full_text)
            metadata = {'filename': file.name,
                        'user': st.session_state['user_info']['mail']}
            llm.insert_index(full_text, metadata_fields=metadata)

    query = st.text_input("Enter your search query")
    search_button = st.button("Search")
    if search_button:
        response = llm.full_text_search(query)
        st.write(response)


def setup_authentication():
    if 'code' in st.query_params:
        authentication.handle_redirect()

    access_token = st.session_state.get('access_token')
    if not access_token:
        auth_url = authentication.get_auth_url()
        st.link_button("Log in with Microsoft", auth_url)
        st.stop()
    else:
        user_info = authentication.get_user_info(access_token)
        st.session_state['user_info'] = user_info
    st.write(st.session_state)


app()
