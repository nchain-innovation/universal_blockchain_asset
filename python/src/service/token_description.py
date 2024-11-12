from pydantic import BaseModel, validator
from typing import Dict, List, Optional
from config import ConfigType
import json
import os

from service.file_storage import FileStorage

from service.util import is_unit_test


class token_descriptor(BaseModel):
    ipfs_cid: str
    name: str
    description: str
    file_hash: str
    filename: str
    cpid: None | str

    @validator('cpid', pre=True)
    def replace_null_with_none(cls, v):
        return v if isinstance(v, str) else None

    def to_string(self) -> str:
        return f'{self.description} {self.ipfs_cid}  {self.cpid}'

    def is_availabe(self) -> bool:
        if self.cpid is None:
            return True
        return False


class TokenStore:
    def __init__(self):
        self.tokens: Dict = {}
        self.assigned_tokens: Dict[str, List[token_descriptor]] = {}
        self.filepath: str = ""

        # Initialise FileStorage with the allowed exensions
        self.file_storage = FileStorage(allowed_extensions={"png", "jpg", "jpeg"})

    def set_config(self, config: ConfigType):
        self.filepath = config["token_info"]["token_file_store"]
        for token in config["token"]:
            token_desc: token_descriptor = token_descriptor(
                ipfs_cid=token["ipfs_cid"],
                name=token["description"],
                description=token["description"] + " data",
                file_hash="file_hash",
                filename="filename",
                cpid="")
            self.tokens[token["ipfs_cid"]] = token_desc

    def save(self) -> bool:
        if len(self.assigned_tokens) > 0:
            json_data = json.dumps(self.assigned_tokens, default=lambda o: o.model_dump())
            with open(self.filepath, 'w') as f:
                json.dump(json_data, f, indent=4)
        return True

    def load(self) -> bool:
        try:
            if os.path.getsize(self.filepath) != 0:
                with open(self.filepath, 'r') as f:
                    serial_data = json.load(f)
                    loaded_data = json.loads(serial_data)
                    # Load JSON data into a dictionary
                    for key, value in loaded_data.items():
                        tokens_per_actor: List[token_descriptor] = []
                        for items in value:
                            tokens_per_actor.append(token_descriptor(
                                ipfs_cid=items["ipfs_cid"],
                                name=items["name"],
                                description=items["description"],
                                file_hash=items["file_hash"],
                                filename=items["filename"],
                                cpid=items["cpid"]))

                            # remove from the tokens list
                            if items["ipfs_cid"] in self.tokens:
                                self.tokens.pop(items["ipfs_cid"])

                        self.assigned_tokens[key] = tokens_per_actor

        except FileNotFoundError as e:
            if not is_unit_test():
                print(e)
            return False

        # sort out the tokens list.
        # if an entry is in the assigned tokens list, remove from the tokens list
        for key in self.assigned_tokens.keys():
            if key in self.tokens:
                del self.tokens[key]

        return True

    # ----------------------------------------------------------------
    def add_token(self, file_content: bytes, filename: str, actor: str, name: str, description: str) -> dict:
        """Add a new token to the token store.
        """
        ret = self.file_storage.save_file(file_content, filename)

        # Check if there was an error saving the file
        if "error" in ret:
            print(f"Error saving file: {ret['error']}")
            return ret

        # else add to the token list
        else:
            asset_id = ret["asset_id"]
            file_hash = ret["file_hash"]
            filename = ret["filename"]
            token = token_descriptor(
                ipfs_cid=asset_id,
                name=name,
                description=description,
                file_hash=file_hash,
                filename=filename,
                cpid=None)
            self.tokens[asset_id] = token
            return ret

    # ----------------------------------------------------------------
    def get_token_by_ipfs_cid(self, asset_id: str) -> Optional[token_descriptor]:
        """Extract the token_descriptor that matches the given ipfs_cid."""
        for actor, tokens in self.assigned_tokens.items():
            for token in tokens:
                if token.ipfs_cid == asset_id:
                    return token
        return None

    # ----------------------------------------------------------------
    def get_token_filepath(self, asset_id: str, actor: str) -> dict:
        """Retrieve the file path and original filename for a given asset ID and actor.

        Args:
            asset_id (str): The unique identifier for the asset.
            actor (str): The username of the actor.
        Returns:
            dict: A dictionary containing the file path and filename.
        Raises:
            ValueError: If the file is not found, or Username does not Match
        """

        # first check if the username is correct to retrieve the file
        if self.check_token_id_actor(actor, asset_id) is False:
            raise ValueError("Username does not match")

        # get the file_descriptor
        asset = self.get_token_by_ipfs_cid(asset_id)

        filename = ""
        if asset:
            filename = asset.filename
        file_path = self.file_storage.get_file_path(filename)
        return {"file_path": file_path, "filename": filename}

    def __repr__(self) -> str:
        token_list: str = json.dumps(self.tokens, default=lambda o: o.model_dump())
        return token_list

    def assign_to_actor(self, actor: str, token_id: str, cpid: str) -> bool:
        if token_id not in self.tokens:
            print(f'{token_id} not listed')
            return False

        token_to_assign: token_descriptor = self.tokens.pop(token_id)
        # set the cpid in the token.
        token_to_assign.cpid = cpid

        # add to the assigned list, keyed by actor
        if actor in self.assigned_tokens:
            self.assigned_tokens[actor].append(token_to_assign)
        else:
            actor_token_list: List = [token_to_assign]
            self.assigned_tokens[actor] = actor_token_list

        # save the file
        self.save()
        return True

    def get_all_assigned_tokens(self) -> Dict[str, List[token_descriptor]]:
        """Return all assigned tokens."""
        return self.assigned_tokens

    def assign_to_new_actor(self, prev_actor: str, new_actor: str, token_id: str, cpid: str) -> bool:
        if prev_actor not in self.assigned_tokens:
            print(f'("error":"actor {prev_actor} does not have any tokens")')
            return False

        if token_id in self.tokens:
            print(f'token with id = {token_id} is already in the available list')
            return False

        matching_tokens = [obj for obj in self.assigned_tokens[prev_actor] if obj.ipfs_cid == token_id]
        if not matching_tokens:
            raise ValueError(f"No token found with ipfs_cid {token_id} for actor {prev_actor}")
        token_to_move: token_descriptor = matching_tokens.pop()
        # remove from the list
        self.assigned_tokens[prev_actor].remove(token_to_move)
        token_to_move.cpid = cpid

        if new_actor in self.assigned_tokens:
            self.assigned_tokens[new_actor].append(token_to_move)
        else:
            token_list: List = [token_to_move]
            self.assigned_tokens[new_actor] = token_list

        # save the file
        self.save()
        return True

    def return_to_pool(self, actor: str, token_id: str) -> bool:
        if actor not in self.assigned_tokens:
            print(f'{actor} does not have assigned tokens')
            return False

        if token_id in self.tokens:
            print(f'token with id = {token_id} is already in the available list')
            return False

        # find the id in the list
        token_to_return: token_descriptor = [obj for obj in self.assigned_tokens[actor] if obj.ipfs_cid == token_id].pop()
        # remove from the list
        self.assigned_tokens[actor].remove(token_to_return)
        self.tokens[token_to_return.ipfs_cid] = token_to_return

        # save the file
        self.save()
        return True

    def tokens_by_actor(self, actor: str) -> str:
        if actor not in self.assigned_tokens:
            return f'("error":"actor {actor} does not have any tokens")'
        json_str: str = json.dumps([obj.model_dump() for obj in self.assigned_tokens[actor]])
        return json_str

    def token_list_by_actor(self, actor: str) -> List[token_descriptor]:
        if actor not in self.assigned_tokens:
            return []
        return self.assigned_tokens[actor]

    def check_token_id(self, token_id: str) -> bool:
        if token_id not in self.tokens:
            print(f'{token_id} not listed')
            return False
        return True

    def check_token_id_actor(self, actor: str, token_id: str) -> bool:

        if actor not in self.assigned_tokens:
            print(f'Actor {actor} does not own token_id {token_id}')
            return False

        matching_tokens = [obj for obj in self.assigned_tokens[actor] if obj.ipfs_cid == token_id]
        if not matching_tokens:
            raise ValueError(f"No token found with ipfs_cid {token_id} for actor {actor}")
        token_to_check: token_descriptor = matching_tokens.pop()

        if token_to_check is None:
            raise ValueError(f'Actor {actor} does not own token_id {token_id}')

        print(f'Actor {actor} owns token_id {token_id}')
        return True


token_store = TokenStore()
