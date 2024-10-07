import streamlit as st

def truncate_string(input_string, length=10):
    input_string = str(input_string)  # Ensure input_string is a string
    if len(input_string) > length:
        return input_string[:10] + '.' * 10 + input_string[-10:]
    else:
        return input_string
    
def see_the_tx_onchain(message, network, txid):
    if network == 'BSV':
        # get rid of the trailing :1
        txid = txid[:-2]
        st.markdown(f"{message}[{txid}](https://test.whatsonchain.com/tx/{txid})", unsafe_allow_html=True)
    elif network == "ETH":
        st.markdown(f"{message}[{txid}](https://sepolia.etherscan.io/tx/0x{txid})", unsafe_allow_html=True)

