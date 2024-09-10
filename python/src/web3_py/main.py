import toml
import uvicorn


def main():

    # Load the configuration from the TOML file
    config = toml.load('./data/ethereum.toml')

    # check the port
    if 'port' not in config['ethereum']:
        raise ValueError("Missing required field 'port' in configuration.")
    port = config['ethereum']['port']
    uvicorn.run("api:app", host="0.0.0.0", port=port)
    return 0


# Entry point
if __name__ == "__main__":
    main()
