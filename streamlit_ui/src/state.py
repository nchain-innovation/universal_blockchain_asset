import streamlit as st


# current_view is for toggling between Grid and Form views
# current_step is for moving between Issuement, Transfer and Commitment steps


# used to toggle back and forth between different views
# i.e 'Grid', 'Form'
def set_page_view(target_view):
    st.session_state['current_view'] = target_view
    print('set_page_view:', target_view)
    if target_view == 'Form':
        st.session_state['button1'] = False
        st.session_state['button2'] = False
        st.session_state['sign_button'] = False
        st.session_state['commit_button'] = False


# returns the current view
def get_page_view():
    return st.session_state['current_view']

# returns the current step
def get_current_step():
    return st.session_state['current_step']