import logging

from common import util

log = logging.getLogger("uvicorn")


class ResourceBaseOS(object):
    def __init__(self, token_pack, res_name, svc_name, res_key=None):
        self.res_name = res_name
        self.res_key = res_name.replace("-", "_")
        if res_key:
            self.res_key = res_key
        self.token_pack = token_pack
        self.token = token_pack["token"]
        self.project_id = token_pack["project"]["id"]
        self.svc_url = util.get_svc_url(token_pack["catalog"], svc_name)
        self.headers = {"x-auth-token": self.token,
                "content-type": "application/json"}

    async def get_list(self, query=None):
        if (hasattr(self, "detail")) and self.detail:
            url = f"{self.svc_url}/{self.res_name}s/detail"
        else:
            url = f"{self.svc_url}/{self.res_name}s"
        url += util.get_q_str(query)
        resp = await util.send_req("get", url, self.headers)
        return resp

    async def get_obj_list(self, query=None):
        resp = await self.get_list(query)
        if resp["status"] == 200:
            return resp["data"][self.res_key + "s"]
        else:
            log.error(f"Get list failed! Status: {resp['status']}")

    async def get(self, id):
        url = f"{self.svc_url}/{self.res_name}s/{id}"
        resp = await util.send_req("get", url, self.headers)
        return resp

    async def get_obj(self, id):
        resp = await self.get(id)
        if resp["status"] == 200:
            return resp["data"][self.res_key]

    async def get_id_by_name(self, name):
        objs = await self.get_obj_list(query={"name": name})
        if not objs:
            return
        # Filter again in case name query is not supported by backend API.
        ids = []
        for obj in objs:
            if obj["name"] == name:
                ids.append(obj["id"])
        if len(ids) == 1:
            return ids[0]
        elif len(ids) == 0:
            log.error(f"Resource {name} is not found!")
        else:
            log.error(f"Multiple resources with name {name}.")

