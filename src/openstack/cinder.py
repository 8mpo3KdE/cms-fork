import logging

from common import util, lock
from common.resource_base_os import ResourceBaseOS

log = logging.getLogger("uvicorn")


class Host(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="os-host", svc_name="volumev3",
                res_key="host")


class VolumeType(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="type", svc_name="volumev3",
                res_key="volume_type")


class VolumeTransfer(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="volume-transfer",
                svc_name="volumev3", res_key="transfer")
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def post_accept(self, id, data):
        url = f"{self.res_url}/{id}/accept"
        resp = await util.send_req("post", url, self.headers, data)
        return resp


class Volume(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="volume", svc_name="volumev3")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.detail = True

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

    async def action(self, id, data):
        url = f"{self.res_url}/{id}/action"
        self.headers["openstack-api-version"] = "volume 3.42"
        resp = await util.send_req("post", url, self.headers, data)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
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


class ManageableVolume(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="manageable_volume",
                svc_name="volumev3", res_key="volume")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.headers["openstack-api-version"] = "volume 3.66"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp


class Snapshot(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="snapshot", svc_name="volumev3")
        self.res_url = f"{self.svc_url}/{self.res_name}s"

    async def post(self, data):
        req = data[self.res_name]
        params = {"name": req["name"],
                "force": req["force"],
                "volume_id": req["volume_id"]}
        resp = await util.send_req("post", self.res_url, self.headers,
                {self.res_name: params})
        if resp["status"] != 202:
            log.error(f"Create snapshot failed! resp: {resp['status']}" \
                    f" {resp['data']}")
            return resp
        retention = None
        if "retention" in req:
            retention = req["retention"]
        if "plan_id" in req:
            plan_id = req["plan_id"]
        if retention:
            vol_id = resp["data"][self.res_name]["volume_id"]
            await self.apply_retention(vol_id, retention, plan_id)
        return resp

    async def delete(self, id):
        url = f"{self.res_url}/{id}"
        resp = await util.send_req("delete", url, self.headers)
        return resp

    async def apply_retention(self, vol_id, retention, plan_id):
        log.info(f"Apply retention to volume snapshot with plan {plan_id}.")
        all_objs = await self.get_obj_list()
        objs = []
        for obj in all_objs:
            if (obj["volume_id"] == vol_id) \
                    and (obj["name"] == f"plan-{plan_id}"):
                objs.append(obj)
        if not objs:
            log.info(f"No volume snapshot from plan {plan_id}.")
            return
        #log.debug(f"Snapshot list {objs}.")
        objs_sorted = sorted(objs, key = lambda x:x["created_at"],
                reverse = True)
        while len(objs_sorted) > retention:
            obj = objs_sorted[-1]
            log.info(f"Delete expired volume snapshot {obj['id']}.")
            await lock.acquire({"type": "volume", "id": obj["volume_id"]})
            await self.delete(obj["id"])
            await lock.release({"type": "volume", "id": obj["volume_id"]})
            objs_sorted.pop()


class ManageableSnapshot(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="manageable_snapshot",
                svc_name="volumev3", res_key="snapshot")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.detail = True
        self.headers["openstack-api-version"] = "volume 3.66"

    async def post(self, data):
        resp = await util.send_req("post", self.res_url, self.headers, data)
        return resp

class SchedulerStats(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="scheduler-stat",
                svc_name="volumev3", res_key="pool")
        self.res_url = f"{self.svc_url}/{self.res_name}s"
        self.headers["openstack-api-version"] = "volume 3.66"

    async def get_pool(self):
        url = f"{self.res_url}/get_pools?detail=true"
        resp = await util.send_req("get", url, self.headers)
        return resp["data"]["pools"]

