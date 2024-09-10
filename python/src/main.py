#!/usr/bin/python3

import uvicorn
import os
from config import load_config, ConfigType

from fastapi.middleware.cors import CORSMiddleware

from rest_api import app, CONFIG_FILE


from service.commitment_service import commitment_service
from service.token_description import token_store

# Configure CORS for app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_webserver_config(app_name: str, config: ConfigType):
    host = config["host"]
    port = config["port"]

    if os.environ.get("APP_ENV") == "docker":
        print("Running in Docker")
        # Allow all access in docker
        # (required as otherwise the localmachine can not access the webserver)
        # host = "0.0.0.0"
    else:
        print("Running in native OS")
        # Only allow access from localmachine
        # host = '127.0.0.1'

    print(f"Running webserver on {host}:{port}")

    server_config = uvicorn.Config(
        app=app_name,
        host=host,
        port=port,
        log_level=config["log_level"],
        reload=config["reload"],
        workers=1)
    return server_config


def run_webserver(config: ConfigType):
    server_config = create_webserver_config("rest_api:app", config['web_interface'])
    server = uvicorn.Server(server_config)
    server.run()


def main():
    config = load_config(CONFIG_FILE)
    commitment_service.set_config(config)
    token_store.set_config(config)
    token_store.load()
    is_financing_service_present = commitment_service.test_financing_service()
    if not is_financing_service_present:
        print(f"is_financing_service_present = {is_financing_service_present}")
        # Only stop if blockchain enabled
        if commitment_service.blockchain_enabled:
            return

    run_webserver(config)


if __name__ == "__main__":
    main()
