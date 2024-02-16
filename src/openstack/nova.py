import logging

from common import util
from common.resource_base_os import ResourceBaseOS

log = logging.getLogger("uvicorn")


class Flavor(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="flavor", svc_name="compute")


class Hypervisor(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="os-hypervisor",
            res_key="hypervisor", svc_name="compute")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.detail = True


class Instance(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="server", svc_name="compute")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.detail = True

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def add_interface(self, id, data):
        url = f"{self.res_url}/{id}/os-interface"
        resp = await util.send_req("post", url, self.headers, data)
        return resp

    async def remove_interface(self, id, port_id):
        url = f"{self.res_url}/{id}/os-interface/{port_id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def add_volume(self, id, data):
        url = f"{self.res_url}/{id}/os-volume_attachments"
        self.headers["openstack-api-version"] = "compute 2.60"
        resp = await util.send_req("post", url, self.headers, data)
        return resp

    async def remove_volume(self, id, vol_id):
        url = f"{self.res_url}/{id}/os-volume_attachments/{vol_id}"
        self.headers["openstack-api-version"] = "compute 2.60"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def add_metadata(self, id, data):
        url = f"{self.res_url}/{id}/metadata"
        resp = await util.send_req("post", url, self.headers, data)
        return resp

    async def remove_metadata(self, id, key):
        url = f"{self.res_url}/{id}/metadata/{key}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def action(self, id, data):
        url = f"{self.res_url}/{id}/action"
        resp = await util.send_req("post", url, self.headers, data)
        return resp

