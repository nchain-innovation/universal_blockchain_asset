import streamlit as st
from restful_calls import get_commitment_metadata, create_transfer_template, get_commitments_available_for_purchase
from state import set_page_view, get_page_view
from grid import draw_commitment_grid
from utils import see_the_tx_onchain



def transfer_template_grid():

    selected_actor = st.selectbox('Select Actor', st.session_state['actors'])

    # use Murphy's new function to get the tokens 
    #  owned by selected actor that are available for purchase by others
    commitments, cpid_lookup = get_commitments_available_for_purchase(selected_actor)

    # create a grid with the commitment data
    draw_commitment_grid(commitments, cpid_lookup)
    



def transfer_template_form():
    st.markdown('##### Transfer Request')
    st.write("Select the destination blockchain network and create an outpoint")

    print('transfer_template_form')
    

   # create a streamlit form to capture the user's input: Digital Artefact Name, Actor, Source Blockchain
    with st.form(key='create_template_form'):
        metadata = get_commitment_metadata(st.session_state['cpid'])
        # print(metadata)
        asset_id = metadata['commitment_packet']['asset_id']
        st.write('Asset ID:')
        st.code(asset_id, language='markdown')
        st.write('UBA ID:')
        st.code(st.session_state['cpid'], language='markdown')

        # create 2 columns with the left column containing the source information and the right column containing the destination information
        cols = st.columns(2)
        cols[0].text_input( 'Source Actor', metadata['owner'], disabled=True)
        cols[0].text_input('Source Network', metadata['commitment_packet']['blockchain_id'], disabled=True)
        actor = cols[1].text_input('Destination Actor:', st.session_state['username'], disabled=True)
        network = cols[1].selectbox('Select Destination Network',st.session_state['networks'], index=1)

        cols = st.columns(5)
        submitted = cols[4].form_submit_button('Create Outpoint')

        if submitted:
            with st.spinner('Processing...'):
                try: 
                    result = create_transfer_template(st.session_state['cpid'], actor, network)
                    if result:
                        # Get the first (and only) item in the second level dictionary
                        cpid_data = list(result['message'].values())[0]
                        txid = cpid_data['blockchain_outpoint']
                        
                        # See the Ownership Outpoint on the destination network
                        see_the_tx_onchain("See the outpoint on chain: ", network, txid)
                    else:
                        st.error('Failed to create transfer template')
                except Exception as e:
                    st.error(f'Failed to create transfer template: {str(e)}')
    
    st.button('Back', on_click=set_page_view, args=['Grid'], type='primary')


# show the grid or the form based on the user's selection
def render_page():
    if get_page_view() == 'Form':
        transfer_template_form()
    else:
        transfer_template_grid()




 