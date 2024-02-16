import logging
import requests
import json

from client.common import ResourceBase

log = logging.getLogger("cms")


class Auth(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/identity/auth/token"
        else:
            self.url = f"{args.cms_auth_url}/auth/tokens"

    def create(self, no_output=False):
        headers = {"Content-Type": "application/json"}
        if not self.args.cms_auth_method:
            self.args.cms_auth_method = "password"
        if self.args.cms_auth_method == "password":
            data = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "name": self.args.cms_username,
                                "password": self.args.cms_password,
                                "domain": {"id": "default"}
                            }
                        }
                    }
                }
            }
            #if self.args.scope and self.args.scope == "project":
            #if self.args.cms_project:
            data["auth"]["scope"] = {
                "project": {
                    "name": self.args.cms_project,
                    "domain": {
                        "id": "default"
                    }
                }
            }
        elif self.args.cms_auth_method == "credential":
            data = {
                "auth": {
                    "identity": {
                        "methods": ["application_credential"],
                        "application_credential": {
                            "name": self.args.cms_credential_name,
                            "secret": self.args.cms_credential_secret,
                            "user": {
                                "name": self.args.cms_username,
                                "domain": {"name": "Default"}
                            }
                        }
                    }
                }
            }
        else:
            log.error(f"Invalid auth method {self.args.cms_auth_method}!")
            return
        token_pack = {}
        try:
            log.debug(f"Get Token: URL: {self.url}")
            log.debug(f"Get Token: Headers: {headers}")
            log.debug(f"Get Token: Data: {data}")
            resp = requests.post(self.url, headers=headers,
                    data=json.dumps(data))
        except Exception as e:
            log.error(e)
            return token_pack
        log.debug(f"Get Token: Response: {resp.text}")
        if resp.status_code == 201:
            token = resp.headers["X-Subject-Token"]
            token_pack = resp.json()["token"]
            token_pack["token"] = token
            log.debug(f"Got token: {token}")
            if not no_output:
                print(f"Token: {token}")
                print(f"Data: {resp.json()}")
        return token_pack


class Project(object):
    def __init__(self, args, token):
        self.args = args
        self.token = token

    def list(self):
        pass

    def show(self):
        pass

    def create(self):
        pass

    def delete(self):
        pass


arg_schema = {
    "auth": {
        "res-class": Auth,
        "create": [
            {
                "name": "--scope",
                "attr": {
                    "choices": ["project", "domain"]
                }
            }
        ]
    }
}

