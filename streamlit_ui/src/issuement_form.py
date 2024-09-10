import streamlit as st
from state import set_page_view
import pandas as pd
from st_aggrid import AgGrid
from restful_calls import get_token_list, create_issuance
from utils import see_the_tx_onchain
from restful_calls import get_commitment_metadata
from grid import get_table_grid, configure_grid, create_aggrid
from state import get_page_view

def draw_commitment_grid(df):
    # Define grid options
    gridOptions = {
        'rowSelection': 'single',
        'columnDefs' : [
            { 'headerName': 'IPFS CID', 'field': 'ipfs_cid', "checkboxSelection": True },
            { 'headerName': 'Description', 'field': 'description' },
            { 'headerName': 'CPID', 'field': 'cpid' }
        ],
        'enableSorting': True,
        'enableFilter': True,
        'enableColResize': True,
        'pagination': 'true',
        'paginationAutoPageSize': 'true',
        'domLayout': 'autoHeight',
    }

    grid_height =  25 * max(1, len(df.index)) + 100

    table = AgGrid(
        df,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        theme="balham",
        height=grid_height
    )
    return table


def issuement_grid():
    if 'selected_row' not in st.session_state:
        st.session_state['selected_row'] = None

    st.write('These are digital artefacts available to issue as UBA tokens.  Select one to issue')
    data = get_token_list()

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(data.values(), index=data.keys())
    table = draw_commitment_grid(df)

     # If a row is selected, get the asset_id
    if table['selected_rows'] is not None:

        selected_row = table['selected_rows'].iloc[0]
        st.session_state['selected_row'] = selected_row

        st.button("Click to Proceed", on_click=set_page_view, args=['Form'], type='primary')


def issuement_form():
    if 'button1' not in st.session_state:
        st.session_state['button1'] = False

    if 'button2' not in st.session_state:
        st.session_state['button2'] = False

    if 'blockchain_message' not in st.session_state:
        st.session_state['blockchain_message'] = None

    st.write("Click below to create the outpoint, then issue the selected asset")
    selected_row = st.session_state['selected_row']
    network = st.selectbox('Select Issuance Network', st.session_state['networks'])    


    # Create first button
    button1_clicked = st.button('Create Outpoint')

    if button1_clicked: # write to the blockchain
        with st.spinner('Processing...'):
            st.session_state['button1'] = True

            # NB: This does the issuance in one step
            result = create_issuance(st.session_state['username'], 
                                selected_row['description'], 
                                selected_row['ipfs_cid'],
                                network)
            if result:
                # Get the first (and only) item in the second level dictionary
                cpid_data = list(result['message'].values())[0]
                txid = cpid_data['blockchain_outpoint']
                st.session_state['cpid'] = list(result['message'])[0]
                # print('DEBUG: cpid = ', st.session_state['cpid'])
                message = 'See the outpoint on chain: '
                if network == 'BSV':
                    txid = txid[:-2]
                    st.session_state['blockchain_message'] = f"{message}[{txid}](https://test.whatsonchain.com/tx/{txid})"
                elif network == "ETH":
                    st.session_state['blockchain_message'] = f"{message}[{txid}](https://sepolia.etherscan.io/tx/{txid})"
                

    # If first button is clicked (Create Outpoint)
    if st.session_state['button1'] :
        
        st.markdown(st.session_state['blockchain_message'], unsafe_allow_html=True)
        button2_clicked = st.button('Issue Asset')
        
        if button2_clicked:
            st.session_state['button2'] = True
            try:
                metadata = get_commitment_metadata(st.session_state['cpid'])
            except Exception as e:
                st.error(f"Failed to fetch metadata: {e}")
                return
            metadata_df = pd.DataFrame(list(metadata['commitment_packet'].items()), columns=['Attribute', 'Value'])

            metadata_df, selected_grid_options, grid_height = configure_grid(metadata_df)

            st.markdown(f"Asset Issued, details as follows: ")
            st.code(f"uba_id = {st.session_state['cpid']}", language='markdown')

            # Display the grid
            create_aggrid(metadata_df, selected_grid_options, height=grid_height)

    # If second button is clicked (Issue Asset)
    if st.session_state['button2']:
        ok_clicked = st.button('OK', on_click=set_page_view, args=['Grid'], type='primary')


def render_page():
    if get_page_view() == 'Form':
        issuement_form()
    else:
        issuement_grid()

