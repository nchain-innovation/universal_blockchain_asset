## Test REST API for Ethereum Interface

A test API is provided to exercise and troubleshot the Ethereum interface. 

### Requirements: 

An API key is required to connect to the Ethereum network - create one here:
[https://docs.infura.io/api/getting-started](https://docs.infura.io/api/getting-started)

 
An Ethereum account with funds is required.  

Create an Ethereum Key using either a library such as the Web3.py python library, or via a wallet like Metamask.


Funds can be added by using a faucet, for example, the Google ETH Sepolia faucet at [https://cloud.google.com/application/web3/faucet/ethereum/sepolia](https://cloud.google.com/application/web3/faucet/ethereum/sepolia)

### Configuration

Edit the **web3_py/data/ethereum.toml** file to add your API key and ETH privateKey

```
[ethereum]
privateKey = "" # the private key of the ETH account that will be used to send transactions (required)

[ethereum_service]
ethNodeUrl = "https://sepolia.infura.io/v3/"
apiKey = ""             # Insert your Infura API key here
```

## Run the API

From **python/src/Web3_py** run:

`python3 main.py`

The Rest API is available at: http://localhost:8575/docs#/


