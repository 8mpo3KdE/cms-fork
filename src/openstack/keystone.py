import logging

from common import util, config
from common.resource_base_os import ResourceBaseOS

log = logging.getLogger("uvicorn")


class Auth(ResourceBaseOS):
    def __init__(self, token_pack=None):
        if token_pack:
            super().__init__(token_pack, res_name="token",
                    svc_name="identity")
            self.svc_url = self.svc_url + "/v3"

    async def post(self, data, scope="project"):
        req_headers = {"Content-Type": "application/json"}
        try:
            auth_type = data["type"]
            url = f"{data['auth_url']}/auth/tokens"
            if auth_type == "password":
                identity = {
                    "methods": ["password"],
                    "password": {
                        "user": {
                            "name": data["username"],
                            "password": data["password"],
                            "domain": {"id": "default"}
                        }
                    }
                }
                if scope == "project":
                    if "project_id" in data:
                        scope = {
                            "project": {
                                "id": data["project_id"]
                            }
                        }
                    elif "project_name" in data:
                        scope = {
                            "project": {
                                "name": data["project_name"],
                                "domain": {
                                    "id": "default"
                                }
                            }
                        }
                    else:
                        scope = {}
                elif scope == "domain":
                    scope = {
                        "domain": {
                            "id": "default"
                        }
                    }
                elif scope == "system":
                    scope = {
                        "system": {
                            "all": True
                        }
                    }
                else:
                    scope = "unscoped"
                req_data = {
                    "auth": {"identity": identity, "scope": scope}
                }
            elif auth_type == "application_credential":
                identity = {
                    "methods": ["application_credential"],
                    "application_credential": {
                        "name": data["credential_name"],
                        "secret": data["credential_secret"],
                        "user": {"id": data["user"]}
                    }
                }
                req_data = {
                    "auth": {"identity": identity},
                }
            else:
                log.error(f"Invalid auth type {auth_type}!")
                return
        except KeyError as k:
            log.error(f"Argument {k} is missing!")
            return
        resp = await util.send_req("post", url, req_headers, req_data,
                secure_log=True)
        if resp["status"] == 201:
            log.info("Got token.")
            token_pack = resp["data"]["token"]
            token_pack["token"] = resp["headers"]["x-subject-token"]
            return token_pack
        else:
            log.error("Get token failed!")

    async def get_user_token(self, data):
        return await self.post(data)

    async def get_svc_token(self, config):
        data = {
            "auth_url": config["auth-url"],
            "type": "password",
            "username": config["os-username"],
            "password": config["os-password"],
            "project_name": "service"}
        return await self.post(data)

    async def get_admin_token(self, project_id):
        data = {
            "auth_url": config.zone_conf["auth-url"],
            "type": "password",
            "username": "admin",
            "password": config.config["admin"]["password"],
            "project_id": project_id}
        return await self.post(data)

    async def validate(self, token):
        url = f"{self.svc_url}/auth/tokens"
        req_headers = {"x-auth-token": self.token, "x-subject-token": token}
        resp = await util.send_req("get", url, req_headers)
        if resp["status"] == 200:
            #log.debug("User token is valid.")
            return resp["data"]["token"]
        elif resp["status"] == 404:
            log.error("User token is invalid.")
            return
        elif resp["status"] == 401:
            log.info("Re-get service token.")
            token_pack = await self.get_svc_token(config.zone_conf)
            if not token_pack:
                log.error("Re-get service token failed!")
                return
            config.svc_token_pack = token_pack
            req_headers = {"x-auth-token": token_pack["token"],
                    "x-subject-token": token}
            resp = await util.send_req("get", url, req_headers)
            if resp["status"] == 200:
                log.info("Valid user token with refreshed service token.")
                return resp["data"]["token"]
            else:
                log.error("Invalid user token with refreshed service token.")
                return
        else:
            log.error(f"Token validation failed! status {resp['status']}")
            return


class Project(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="project",
                svc_name="identity")
        self.svc_url = self.svc_url + "/v3"


class ApplicationCredential(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="application_credential",
                svc_name="identity")
        uid = self.token_pack['user']['id']
        self.svc_url = f"{self.svc_url}/v3/users/{uid}"


class RegisteredLimit(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="registered_limit",
                svc_name="identity")
        self.svc_url = self.svc_url + "/v3"
        self.res_url = f"{self.svc_url}/{self.res_name}s"


class Limit(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="limit",
                svc_name="identity")
        self.svc_url = self.svc_url + "/v3"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

