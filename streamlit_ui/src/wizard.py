import streamlit as st

import issuement_form as issue
import transfer_form as transfer
import commit_form as commit


# Draw the wizard view
def render_wizard_view(): 

    header_cols = st.columns([1,5])    
    header_cols[0].image('resources/collaboration.png')
    header_cols[1].header(f"{st.session_state['username']}'s UBA Wallet")
    
    # determines button colour which should be highlighted when user is on that given step
    wh_type = 'primary' if st.session_state['current_step'] == 1 else 'secondary'
    ff_type = 'primary' if st.session_state['current_step'] == 2 else 'secondary'
    lo_type = 'primary' if st.session_state['current_step'] == 3 else 'secondary'

    step_cols = st.columns([.25, 0.5, 0.5, 0.5, .25])    
    step_cols[1].button('Issue', on_click=set_form_step, args=['Jump', 1], type=wh_type)
    step_cols[2].button('Initiate Transfer', on_click=set_form_step, args=['Jump', 2], type=ff_type)        
    step_cols[3].button('Sign and Commit', on_click=set_form_step, args=['Jump', 3], type=lo_type)      
        
    st.markdown('---')

    if st.session_state['current_step'] == 1:
        issue.render_page()
    elif st.session_state['current_step'] == 2:
        transfer.render_page()
    elif st.session_state['current_step'] == 3:
        commit.render_page()


# keep track of the user's location within the wizard
def set_form_step(action,step=None):
   if action == 'Jump':
        st.session_state['current_step'] = step
        st.session_state['current_view'] = 'Grid'

