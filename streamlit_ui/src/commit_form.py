import streamlit as st
from restful_calls import get_commitment_metadata, complete_transfer, get_half_baked_commitments, get_commitment_tx_hash
from grid import draw_commitment_grid
from utils import see_the_tx_onchain
from state import get_page_view, set_page_view
from grid import configure_grid, create_aggrid
import pandas as pd

def commit_grid():

    st.write("These are the UBAs that you own and have been requested by others")

    # Use Arthur's function to get the half-baked commitments 
    # that are owned by the user and have been requested by others
    commitments, cpid_lookup = get_half_baked_commitments(st.session_state['username'])

    # create a grid with the commitment data
    draw_commitment_grid(commitments, cpid_lookup)

def commit_form():

    if 'sign_button' not in st.session_state:
        st.session_state['sign_button'] = False

    if 'commit_button' not in st.session_state:
        st.session_state['commit_button'] = False

    if 'previous_packet' not in st.session_state:
        st.session_state['previous_packet'] = None

    if 'metadata' not in st.session_state:
        st.session_state['metadata'] = None



    st.markdown('Sign the UBA packet and submit commitment to the destination blockchain network.  This completes the transfer of ownership')
    st.markdown('---')
    # with st.form(key='sign_form'):


    metadata = get_commitment_metadata(st.session_state['cpid'])
    asset_id = metadata['commitment_packet']['asset_id']
    network = metadata['commitment_packet']['blockchain_id']
    st.write('Asset ID:')
    st.code(asset_id, language='markdown')
    st.write('UBA ID:')
    st.code(st.session_state['cpid'], language='markdown')
    
    cols = st.columns(2)
    cols[0].write('Destination Network:')
    cols[0].code(network)

    cols[1].write('Destination Owner:')
    cols[1].code(metadata['owner'])
    # print(metadata)

    st.markdown('---')

    # st.info('Please sign the commitment packet template to complete the transfer')
    cols = st.columns(4)
    # sign_clicked = cols[3].form_submit_button('Sign UBA Packet')
    sign_clicked = st.button('Sign UBA Packet')

  
    if sign_clicked:
        with st.spinner('Processing...'):
            st.session_state['sign_button'] = True

            # NB: This does the sign and spend in one step
            metadata = complete_transfer(st.session_state['cpid'], st.session_state['username'])
            if not metadata:
                st.error('Failed to sign the UBA packet')
                return
            else:
                st.session_state['metadata'] = metadata

    # If first button is clicked (Sign UBA Packet)
    if st.session_state['sign_button'] :

        st.success('UBA packet signed successfully')

        # Extract the nested dictionary
        nested_dict = list(st.session_state['metadata']['message'].values())[0]

        # Save the previous_packet as needed later
        st.session_state['previous_packet'] = nested_dict['previous_packet']

        # Convert the nested dictionary to a DataFrame
        metadata_df = pd.DataFrame.from_dict(nested_dict, orient='index').reset_index()

        # Rename the columns
        metadata_df.columns = ['Attribute', 'Value']
        metadata_df, selected_grid_options, grid_height = configure_grid(metadata_df)

        # st.markdown(f"Asset Issued, details as follows: ")
        st.code(f"uba_id = {st.session_state['cpid']}", language='markdown')

        # Display the grid
        create_aggrid(metadata_df, selected_grid_options, height=grid_height)

        commit_clicked = st.button('Commit to Blockchain')

        if commit_clicked:
            st.session_state['commit_button'] = True

            print("looking up commitment hash using current session cpid: ", st.session_state['cpid'])
            txid = get_commitment_tx_hash(st.session_state['cpid'])

            if txid is None:
                st.error('Failed to get the transaction hash')
                return

            # need to get the blockchain_id of the previous packet
            try:
                prev_metadata = get_commitment_metadata(st.session_state['previous_packet'])
            except Exception as e:
                st.error(f"Failed to fetch metadata from previous packet: {e}")
                return
            
            prev_network = prev_metadata['commitment_packet']['blockchain_id']

            message = 'See the outpoint on chain: '
            if prev_network == 'BSV':
                message = f"{message}[{txid}](https://test.whatsonchain.com/tx/{txid})"
            elif prev_network == "ETH":
                message = f"{message}[{txid}](https://sepolia.etherscan.io/tx/0x{txid})"

            st.markdown(message, unsafe_allow_html=True)
    
    # If the second button is clicked (Commit to Blockchain)
    if st.session_state['commit_button']:
        st.button('OK', on_click=set_page_view, args=['Grid'], type='primary')



# show the grid or the form based on the user's selection
def render_page():
    if get_page_view() == 'Form':
        commit_form()
    else:
        commit_grid()