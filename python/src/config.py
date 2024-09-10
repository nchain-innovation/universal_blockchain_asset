import toml
import logging
from typing import Any, MutableMapping

LOGGER = logging.getLogger(__name__)


ConfigType = MutableMapping[str, Any]


def load_config(filename: str) -> ConfigType:
    """ Load config from provided toml file
    """
    try:
        with open(filename, "r") as f:
            config = toml.load(f)
        return config
    except FileNotFoundError as e:
        print(f"load_config - File not found error {e}")
        LOGGER.warning(f"load_config - File not found error {e}")
        return {}
