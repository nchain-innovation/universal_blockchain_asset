import streamlit as st 
from wizard import render_wizard_view
import os
from restful_calls import get_actors, get_networks

# Get environment variables
if os.environ.get('USER_NAME') is not None:
    USER_NAME = os.environ['USER_NAME']
if os.environ.get('UBA_SERVICE_URL') is not None:
    UBA_SERVICE_URL = os.environ['UBA_SERVICE_URL']

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state['current_step'] = 1

if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Grid'

if 'username' not in st.session_state:
    if USER_NAME is None:
        print("USER_NAME environment variable not set")
        exit(1)
    st.session_state['username'] = USER_NAME

if 'cpid' not in st.session_state:
    st.session_state['cpid'] = None

if 'previous_cpid' not in st.session_state:
    st.session_state['previous_cpid'] = None

if 'commitment_service_url' not in st.session_state:
    if UBA_SERVICE_URL is None:
        print("COMMITMENT_SERVICE_URL environment variable not set")
        exit(1)
    st.session_state['commitment_service_url'] = UBA_SERVICE_URL

if 'actors' not in st.session_state:
    st.session_state['actors'] = get_actors()
if 'networks' not in st.session_state:  
    st.session_state['networks'] = get_networks()


# Set up the webpage
st.set_page_config(page_title=f"{st.session_state['username']}'s Commitment Token Wallet ",
                    page_icon="🤝",
)

# main entry point
if __name__ == "__main__":

    render_wizard_view()
