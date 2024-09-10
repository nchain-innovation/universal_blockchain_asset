import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
from state import set_page_view
from utils import truncate_string
from restful_calls import get_commitment_metadata
import pandas as pd

# Define constants
GRID_HEIGHT_MULTIPLIER = 25
GRID_HEIGHT_OFFSET = 100

# Helper function: create an AgGrid
def create_aggrid(df, grid_options, fit_columns_on_grid_load=True, height=None):
    return AgGrid(
        df, 
        gridOptions=grid_options, 
        fit_columns_on_grid_load=fit_columns_on_grid_load,
        theme="balham",
        height=height 
    )


# Helper function: draw the previous asset
def draw_previous_asset(previous_cpid):
    try:
        metadata = get_commitment_metadata(previous_cpid)
    except Exception as e:
        st.error(f"Failed to fetch metadata: {e}")
        return

    previous_cpid = metadata['commitment_packet']['previous_packet']

    # Convert metadata to DataFrame
    metadata_df = pd.DataFrame(list(metadata['commitment_packet'].items()), columns=['Attribute', 'Value'])

    metadata_df, metadata_grid_options, grid_height = configure_grid(metadata_df)

    st.write("Asset's previous packet details:")
    st.code(f"uba_id = {st.session_state['previous_cpid']}", language='markdown')

    create_aggrid(metadata_df, metadata_grid_options, height=grid_height)

    st.session_state['previous_cpid'] = previous_cpid
    

# Helper function: configure the sub-grid
def configure_grid(data_df):
    # Truncate the 'signature' and 'public_key' fields
    for field in ['signature', 'public_key']:
        if field in data_df['Attribute'].values:
            data_df.loc[data_df['Attribute'] == field, 'Value'] = data_df.loc[data_df['Attribute'] == field, 'Value'].apply(lambda x: truncate_string(x, 15))

    # Configure grid options
    gob = GridOptionsBuilder.from_dataframe(data_df)
    gob.configure_auto_height(True)
    grid_options = gob.build()

    # Calculate grid height
    grid_height =  GRID_HEIGHT_MULTIPLIER * max(1, data_df.shape[0]) + GRID_HEIGHT_OFFSET

    return data_df, grid_options, grid_height


# Helper function: get the sub grid
def get_sub_grid(commitments_table):
    """
    Get a sub grid from the selected row in the commitments_table.

    Parameters:
    commitments_table (dict): A dictionary containing selected rows.

    Returns:
    DataFrame: A DataFrame representing the sub grid.
    """
    if len(commitments_table['selected_rows']) > 0:
        # Get the selected row
        selected_row = commitments_table['selected_rows'].iloc[0]
        
        # Create a copy of the selected row
        selected_row_copy = selected_row.copy()

        # Convert the selected row to a DataFrame and reset the index
        selected_row_df = selected_row_copy.to_frame().reset_index()
        selected_row_df.columns = ['Attribute', 'Value']

        selected_row_df, selected_grid_options, grid_height = configure_grid(selected_row_df)

        st.markdown(f"Selected asset's details: ")
        st.code(f"uba_id = {st.session_state['cpid']}", language='markdown')

        # Display the grid
        sub_table = create_aggrid(selected_row_df, selected_grid_options, height=grid_height)

        return sub_table
    

# Helper function: get the main table grid
def get_table_grid(df):

    # Define grid options
    gridOptions = {
        'rowSelection': 'single',
        'columnDefs' : [
            { 'headerName': 'Asset ID', 'field': 'asset_id', "checkboxSelection": True },
            { 'headerName': 'Blockchain ID', 'field': 'blockchain_id' },
            { 'headerName': 'Data', 'field': 'data' }
        ],
        'enableSorting': True,
        'enableFilter': True,
        'enableColResize': True,
        'pagination': 'true',
        'paginationAutoPageSize': 'true',
        'domLayout': 'autoHeight',
    }

    # Work out height for grid based on number of rows in df
    grid_height =  GRID_HEIGHT_MULTIPLIER * max(1, len(df.index)) + GRID_HEIGHT_OFFSET

    table = create_aggrid(df, gridOptions, height=grid_height)

    return table



# Main function: draw the commitment grid
def draw_commitment_grid(df, cpid_lookup):

    # Draw main grid
    table = get_table_grid(df)

    # Create two columns
    cols = st.columns([4, 1])

    # If a row is selected, get the cpid by looking up the asset_id
    if table['selected_rows'] is not None:
        
        st.session_state['cpid'] = cpid_lookup.get(table['selected_rows']['asset_id'].iloc[0])
 
        get_sub_grid(table)
        # I want to show the previous assets linked by the previous_packet cpid
        previous_cpid = (table['selected_rows']['previous_packet'].iloc[0])
        st.session_state['previous_cpid'] = previous_cpid

        while previous_cpid is not None:
            draw_previous_asset(previous_cpid)
            previous_cpid = st.session_state['previous_cpid']

        cols = st.columns(4)
        cols[3].button('Select this Asset', on_click=set_page_view, args=['Form'], type='primary')

    


