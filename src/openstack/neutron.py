import logging

from common import util
from common.resource_base_os import ResourceBaseOS

log = logging.getLogger("uvicorn")


class Network(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="network", svc_name="network")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp


class Subnet(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="subnet", svc_name="network")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp


class Port(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="port", svc_name="network")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def put(self, id, data):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("put", url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp


class Router(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="router", svc_name="network")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def add_interface(self, id, data):
        url = f"{self.res_url}/{id}/add_router_interface"
        resp = await util.send_req("put", url, self.headers, data)
        return resp

    async def remove_interface(self, id, data):
        url = f"{self.res_url}/{id}/remove_router_interface"
        resp = await util.send_req("put", url, self.headers, data)
        return resp


class FloatingIP(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="floatingip",
                         svc_name="network")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def get_obj_by_fip(self, fip):
        objs = await self.get_obj_list()
        for obj in objs:
            if obj["floating_ip_address"] == fip:
                break
        else:
            return
        return obj

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def put(self, id, data):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("put", url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp


class SecurityGroup(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="security-group",
                svc_name="network", res_key="security_group")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp


class SecurityGroupRule(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="security-group-rule",
                svc_name="network", res_key="security_group_rule")
        self.svc_url = self.svc_url + "/v2.0"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

