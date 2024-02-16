import logging

from common import util
from common.resource_base_os import ResourceBaseOS


log = logging.getLogger("uvicorn")


class Image(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="image", svc_name="image")
        self.svc_url = f"{self.svc_url}/v2"
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        # For getting the correct json format response from glance, need to
        # add the request header: Accept: application/json
        self.headers['Accept'] = "application/json"
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def patch(self, id, data):
        url = f"{self.res_url}/{id}"
        self.headers["content-type"] = \
                "application/openstack-images-v2.1-json-patch"
        resp = await util.send_req("patch", url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

