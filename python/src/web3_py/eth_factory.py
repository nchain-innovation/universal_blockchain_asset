import sys
sys.path.append("..")


from web3_py.erc20 import ERC20
from web3_py.raw_transaction import RawTransaction
from web3_py.smart_contract import SmartContract


"""
Factory function to create an instance of the appropriate Ethereum interface derived class.

Args:
    interface_type (str): The type of Ethereum interface to create. Must be 'RawTransaction', 'SmartContract', or 'ERC20'.
    ethNodeUrl (str): The URL of the Ethereum node to connect to.
    apiKey (str): The API key to use for the Ethereum node.
    privateKey (str): The private key for the Ethereum account.
    config (dict): The configuration dictionary loaded from the TOML file.

Returns:
    An instance of the appropriate Ethereum interface derived class.

Raises:
    ValueError: If `interface_type` is not 'RawTransaction', 'SmartContract', or 'ERC20', or if `interface_type` is 'SmartContract' or 'ERC20' and `contractAddress` is not provided.
"""


def ethereum_interface_factory(interface_type, ethNodeUrl, apiKey, privateKey, gas, gasPrice, config):

    # Raw transactions (no smart stuff)
    if interface_type == 'RawTransaction':
        return RawTransaction(ethNodeUrl, apiKey, privateKey, gas, gasPrice, config)

    # Smart contract - uses events for signalling state changes
    elif interface_type == 'SmartContract':
        return SmartContract(ethNodeUrl, apiKey, privateKey, gas, gasPrice, config)

    # ERC20 token - conforms to the ERC20 standard
    elif interface_type == 'ERC20':
        print("ERC20")
        return ERC20(ethNodeUrl, apiKey, privateKey, gas, gasPrice, config)
    else:
        raise ValueError("Invalid interface_type. Expected 'RawTransaction', 'SmartContract', or 'ERC20'")


def isERC20(eth):
    return isinstance(eth, ERC20)


def isRawTransaction(eth):
    return isinstance(eth, RawTransaction)


def isSmartContract(eth):
    return isinstance(eth, SmartContract)
