import requests
import streamlit as st
import pandas as pd
import json

# Get list of actors

def get_actors():
    if 'actors' not in st.session_state:
        response = requests.get(st.session_state.commitment_service_url + '/status')
        if response.status_code == 200:
            data = response.json()
            if 'actors' in data:
                return data.get('actors')
        else:
            print(f"Failed to get actors: {response.status_code}, {response.text}")
    return []


def get_networks():
    # Get list of blockchains
    if 'networks' not in st.session_state:
        response = requests.get(st.session_state.commitment_service_url + '/status')
        if response.status_code == 200:
            data = response.json()
            if 'networks' in data:
                return data.get('networks')
        else:
            print(f"Failed to get networks: {response.status_code}, {response.text}")
    
    return []


# Get the commitment data by actor, return in a DataFrame
def get_half_baked_commitments(actor):

    url = f"{st.session_state.commitment_service_url}/commitments/transfers?actor={actor}"
    print(f"Getting half-baked for {actor}")
    # url = f"{st.session_state.commitment_service_url}/commitments?actor={actor}"
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commitments = response.json()
        # Extract the list from the dictionary
        data_list = commitments['message']

        # Flatten the data and convert it to a DataFrame
        flattened_data = [list(item.values())[0] for item in data_list]
        df = pd.DataFrame(flattened_data)


        asset_id_dict = {list(item.values())[0]['asset_id']: list(item.keys())[0] for item in data_list}
        print(asset_id_dict)
        return df, asset_id_dict
    else:
        print(f"Failed to get commitments: {response.status_code}, {response.text}")
        return pd.DataFrame(), {}

# Get the commitment data by actor, return in a DataFrame
def get_commitments_available_for_purchase(actor):
    url = f"{st.session_state.commitment_service_url}/commitment_detail_by_actor?actor={actor}"
    print(f"Getting commitments available for purchase {actor}")
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commitments = response.json()
        # Extract the list from the dictionary
        data_list = commitments['message']

        # Flatten the data and convert it to a DataFrame
        flattened_data = [list(item.values())[0] for item in data_list]
        df = pd.DataFrame(flattened_data)

        asset_id_dict = {list(item.values())[0]['asset_id']: list(item.keys())[0] for item in data_list}
        print(asset_id_dict)
        return df, asset_id_dict
    else:
        print(f"Failed to get commitments: {response.status_code}, {response.text}")
        return pd.DataFrame(), {}
    


# Get the commitment metadata by CPID
def get_commitment_metadata(cpid):
    url = f"{st.session_state.commitment_service_url}/commitment?cpid={cpid}"
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commitment = response.json()
        # return the 'message' part of the response
        if 'message' in commitment:
            return commitment['message']
        else:
            print(f"Error: Can't find 'message' in response: {commitment}")
        return None
    else:
        print(f"Failed to get commitment: {response.status_code}, {response.text}")
        return None
    
# Create the Issuance
def create_issuance(actor, asset_id, asset_data, network):
    url = f"{st.session_state.commitment_service_url}/commitments/issuance"
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {
        'actor': actor,
        'asset_id': asset_id,
        'asset_data': asset_data,
        'network': network,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print(f"Issuance created: {response.json()}")
        return response.json()
    else:
        print(f"Failed to create issuance: {response.status_code}, {response.text}")
        return None


# Transfer the commitment to another network
def create_transfer_template(cpid, actor, network):
    url = f"{st.session_state.commitment_service_url}/commitments/template"
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    data = {
        'cpid': cpid,
        'actor': actor,
        'network': network
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print(response.status_code)
        print(response.text)
        print(f"Transfer template created: {response.json()}")
        return response.json()
    else:
        print(f"Failed to transfer commitment: {response.status_code}, {response.text}")
        raise Exception(f"Failed to transfer commitment: {response.status_code}, {response.text}")


def complete_transfer(cpid, actor):
    print(f"Completing transfer for {cpid}, {actor}")
    url = f"{st.session_state.commitment_service_url}/commitments/complete"
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {
        'cpid': cpid,
        'actor': actor,
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print(f"Transfer completed: {response.json()}")
        return response.json()
    else:
        print(f"Failed to complete transfer: {response.status_code}, {response.text}")
        return None
    

def get_commitment_tx_hash(cpid):
    print(f"Getting commitment tx_hash for {cpid}")
    url = f"{st.session_state.commitment_service_url}/commitment_transaction_hash?cpid={cpid}"
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commitment = response.json()
        # return the 'message' part of the response
        if 'message' in commitment:
            return  commitment['message']['Commitment_TX_Hash']
        else:
            print(f"Error: Can't find 'message' in response: {commitment}")
        return None
    else:
        print(f"Failed to get commitment: {response.status_code}, {response.text}")
        return None
    

def get_token_list():
    url = f"{st.session_state.commitment_service_url}/token_list"
    headers = {'accept': 'application/json'}
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        token_list_str = data['message']
        token_list = json.loads(token_list_str)
       
        print(token_list)
        return token_list
    else:
        print(f"Failed to get token list. Status code: {response.status_code}")
        return None
    

