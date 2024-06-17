import streamlit as st
from authentication import get_user_info_from_local_storage
import llm
from menu import authenticated_menu

authenticated_menu()

files = st.file_uploader("Upload file", type=[
    "pdf"], accept_multiple_files=True)
if files is not None:
    from pypdf import PdfReader

    for file in files:
        pdf_reader = PdfReader(file)
        full_text = '\n'.join([page.extract_text()
                               for page in pdf_reader.pages])
        metadata = {'filename': file.name,
                    'user_id': get_user_info_from_local_storage()['mail']}
        llm.handle_graph_document(full_text, metadata_fields=metadata)
