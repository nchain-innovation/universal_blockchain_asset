# Getting Started


## System dependencies & components

You need the following to get started:

- [ ] Docker Desktop installed on your machine
- [ ] An apiKey for Infura Sepolia - see instructions at [https://docs.infura.io/api/getting-started](https://docs.infura.io/api/getting-started)
- [ ] Keys for each Actor (Alice, Bob, Ted) 

Keys are required for funding transactions on BSV, for gas on ETH, and for signing the UBA packets.  Either use your pre-existing keys, or create new for the project.  

NB: This demo may be run entirely on the BSV network.  If you do not wish to transfer UBA tokens to and from Ethereum, skip the Ethereum Key Export.  You will still need to add the Infura API key as it is required on startup. 

### Ethereum Configuration ###

Add your Infura Sepolia key to the config file `data\uba-server.toml`

```
[ethereum_service]
ethNodeUrl = "https://sepolia.infura.io/v3/"
apiKey = ""             # Insert your Infura API key here
```

### Create Keys and add to config files ###

The keys should be added to the toml configuration files in the `data directory`. 

*Ethereum Key Export*

Your ethereum private key can be exported from a metamak as follows:
> Log in to metamask: Click the three vertical dots next to the account you want to export; On the 'Account details' page, click 'show private key'; Enter your wallet password and click 'Confirm'; Click and hold on 'Hold to reveal Private Key' to display your private key

*BSV Key Export*

BSV key format is wif (wallet import format).  New keys may be easily generated and funded using WildBitTool - see [Wild-Bit-Tool](https://github.com/nchain-innovation/wild-bit-tool)

*Token Key*

The token key is used for signing the UBA packets.  The curve type follows the NIST naming convention, see [pypi ecdsa](https://pypi.org/project/ecdsa/).  For example, to use the secp256r1 curve, set to  

`token_key_curve = "NIST256p"`

**uba-server.toml**

- bitcoin_key (uses secp256k1) - with testnet funds for transactions
- ethereum_key, with testnet funds on the Sepolia testnet
- token_key with token_key_curve in NIST naming convention (using the OpenSSL standard)

Edit the configuration file: `data\uba-server.toml` to include the private kes for BSV transactions, Token signing and Ethereum transactions:

```[[actor]]
name = "Alice"
bitcoin_key = ""                # Insert Alices's BSV private key here
token_key = ""                  # Insert Alices's token private key here  
token_key_curve = ""            # Insert Alices's key curve here, for example, "NIST256p"
eth_key = ""                    # Insert Alices's ethereum account private key here 
```


**financing-service.toml**

The financing service is used to fund BSV transactions.  It provides an interface to the BSV Blockchain to create the funding transaction outpoints.  From a configuration perspective, you need a funded BSV account on Testnet.  Copy the private key in wif format into the configuration file:    `data\financing-service.toml` 

```
[[client]]
client_id = "uba"
wif_key = ""    # Insert the funding account's private key here
```

This will fund all BSV transactions in the demo, regardless of the "owner" of the UBA packet.

# Launch

From the top level directory run: 

```bash
docker compose up
```
This project launches the following containers:

- uba_service (python)
- financing_service (rust)
- Alice's UI (Streamlit)
- Bob's UI (Streamlit)
- Ted's UI (Streamlit)
## High level overview

### **Network**

Docker Compose creates a network if it doesn't already exist named **uba_network.**

Containers that wish to connect to each other need to be part of the same network.

Applications such as browsers and executables running on the host system can access exposed ports. For example,

- uba service is exposed on [http://localhost:8040/docs](http://localhost:8040/docs)
- Alice's UI is exposed on [http://localhost:8501/](http://localhost:8501/)
- Bob's UI is exposed on [http://localhost:8502/](http://localhost:8502/)
- Ted's UI is exposed on [http://localhost:8503/](http://localhost:8503/)



### Uba Service

Configuration:

Add various keys to the uba-server.toml file
Line 19: apiKey for sepolia.infura.io



### **Financing Service**

The financing service is responsible for providing a transaction ID and index to be used to fund a transaction.

The config data is found in:

`data/financing-service.toml`

The most significatant parts are:

`[client]` - this maps the client id to the wif (i.e. the client's funding key).  NB: you will need a BSV testnet key with funds to 