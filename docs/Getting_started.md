# Quick Start
```bash
docker compose up
```
This project launches the following containers:

- commitment_service (python)
- databases (mysql)
- db_admin (lightweight database admin tool)
- uaas_backend (UAAS - Utxo as a Service Rust)
- uaas_web (UAAS Fast API in Python)

## System dependencies & components

You need the following to get started:

- Access to the Bitbucket Repository: [commitment-tokens](https://bitbucket.stressedsharks.com/projects/SDL/repos/commitment-tokens)
- read-access to the nChain Dockerhub Repository: [dockerhub](https://hub.docker.com/?namespace=nchain)
- Docker Desktop installed on your machine

## High level overview

### **Network**

Docker Compose creates a network if it doesn't already exist named **commitment_network.**

Containers that wish to connect to each other need to be part of the same network.

Applications such as browsers and executables running on the host system can access exposed ports. For example,

- commitment service is exposed on [http://localhost:8040/](http://localhost:5003/)
- uaas_web is exposed on [http://localhost:5010/](http://localhost:5010/)
- db_admin is exposed on [http://localhost:8080/](http://localhost:8080/)

### **Volumes**

Docker Compose creates one named volume if it does not already exist:

- **commitment-tokens_db_data** contains database data (i.e. the uaas blockchain data)

The volume may be deleted either via Docker Desktop, or the command line.

Deleting the database data removes all tables, users, and block history created by the uaas_backend.

### **Database**

This uses the official Dockerhub **mysql** image.

The mysql root password is specified in the docker_compose.yml file, see `MYSQL_ROOT_PASSWORD`

The UTXO-as-a-service database is initialised via the script: `/db/init/01_init.sql` The script sets up the uaas user, creates the `uaas_db` table and grants appropriate privileges.

NB: when changing the database username/password in the initialisation script, ensure the change is reflected in toml files for services that require database access (e.g. utxo_as_service)

### **Database Admin**

The lightweight db_admin tool is found at [http://localhost:8080/](http://localhost:8080/)

Login to the db database using the root user and password (see docker-compose.yml `MYSQL_ROOT_PASSWORD`)

Select the uaas_db database from the drop down and use the `select` statements to explore the tables.

### Commitment Service

\<to fill in - blah blah>

### **Financing Service**

The financing service is responsible for providing a transaction ID and index to be used to fund a transaction.

The config data is found in:

`data/financing-service.toml`

The most significatant parts are:

`[client]` - this maps the client id to the wif (i.e. the client's funding key).

### **UTXO As A Service**

UTXO as a service has two containers:

- uaas_backend
- uaas_web

They share the common config file:

`data/uaasr.toml`

The Rusty Backend works out of the box (i.e. downloads the image and runs it).

The Python Web images is used as a base for a new image which has an "isItHealthy.py" script added. The health script allows Docker Compose to determine when the uaas_web is ready via a health-check.

The most significant parts of the config file are:

`start_block_hash` - use a recent block hash

`start_block_height` - use the matching block height

NB: if you change the db user and password in the database initialisation script, ensure the uaasr.toml file reflect the change.
