import streamlit as st
import llm
from menu import authenticated_menu

authenticated_menu()

query = st.text_input("Enter your search query")
search_button = st.button("Search")
if search_button:
    response = llm.search_graph(query)
    st.write(response)
