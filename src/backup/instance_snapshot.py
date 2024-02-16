import asyncio
import logging
from pydantic import BaseModel

from common import util, config, validator, quota, lock
from common.resource_base import ResourceBase
from db import db
from openstack.keystone import Auth
from openstack.nova import Instance, Hypervisor
from openstack.cinder import Snapshot as VolumeSnapshot

log = logging.getLogger("uvicorn")


class InstanceSnapshotObject(BaseModel):
    name: str
    plan_id: str = ""
    instance_id: str
    retention: int = 0


class InstanceSnapshotPost(BaseModel):
    snapshot: InstanceSnapshotObject


class InstanceSnapshot(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="snapshot",
                table_name="instance_snapshot")
        self.action_map = {}
        self.quota = quota.Quota(self.project_id, config, db, self.token_pack)

    async def rh_get(self, id):
        obj = await self.get_obj(id)
        if obj:
            obj["volume_snapshots"] = await db.get("instance_volume_snapshot",
                    {"instance_snapshot_id": id})
            return {"status": 200, "data": {self.res_name: obj}}
        else:
            return {"status": 404}

    async def rh_post(self, req_data):
        req = req_data[self.res_name]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        ins_id = req["instance_id"]
        res = await Instance(self.token_pack).get_obj(id=ins_id)
        if not res:
            log.error(f"Get instance {ins_id} failed!")
            msg = f"Instance ID {ins_id} is invalid!"
            return {"status": 400, "data": {"message": msg}}
        allowed_status = ["ACTIVE", "SHUTOFF", "SUSPENDED", "PAUSED"]
        if res["status"] not in allowed_status:
            msg = "Instance {} status {} not in {}!".format(
                    ins_id, res["status"], allowed_status)
            return {"status": 400, "data": {"message": msg}}
        if not res["os-extended-volumes:volumes_attached"]:
            msg = f"Instance {ins_id} has no volumes attached!"
            return {"status": 400, "data": {"message": msg}}
        if await self.quota.check_quota_limits("cms-backup",
                "instance_snapshot_total",
                await self.quota.get_resource_usage("instance_snapshot")):
            log.error("Instance snapshot reach the limit")
            return {"status": 400,
                    "data": "Instance snapshot reach the limit"}
        id = await self.add_instance_snapshot(req, res["id"])
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def add_instance_snapshot(self, req, ins_id):
        snapshot = {"name": req["name"],
                "project_id": self.project_id,
                "plan_id": req["plan_id"],
                "instance_id": ins_id,
                "status": "building"}
        await db.add(self.table_name, snapshot)
        snapshot["retention"] = req["retention"]
        task = asyncio.create_task(self.task_add_instance_snapshot(
                snapshot, ins_id))
        task.add_done_callback(util.task_done_cb)
        return snapshot["id"]

    async def rh_delete(self, id):
        snapshot = await self.get_obj(id)
        if not snapshot:
            return {"status": 404}
        update = {"status": "deleting"}
        await db.update(self.table_name, id, update)
        task = asyncio.create_task(
                self.task_delete_instance_snapshot(snapshot))
        task.add_done_callback(util.task_done_cb)
        resp = {"status": 202, "data": {self.res_name: {"id": id}}}
        return resp

    async def task_add_instance_snapshot(self, snapshot, ins_id):
        log.info(f"Task add instance snapshot {snapshot['id']}.")
        update_error = {"status": "error"}
        admin_token_pack = await Auth().get_admin_token(self.project_id)
        if not admin_token_pack:
            log.error(f"Get admin token failed!")
            await db.update(self.table_name, snapshot["id"], update_error)
            return
        ins = await Instance(admin_token_pack).get_obj(id=ins_id)
        dom_name = ins["OS-EXT-SRV-ATTR:instance_name"]
        hv_name = ins["OS-EXT-SRV-ATTR:hypervisor_hostname"]
        hvs = await Hypervisor(admin_token_pack).get_obj_list()
        for hv in hvs:
            if hv["hypervisor_hostname"] == hv_name:
                hv_ip = hv["host_ip"]
                break
        else:
            log.error(f"Not found hypervisor {hv_name}")
            await db.update(self.table_name, snapshot["id"], update_error)
            return

        await lock.acquire({"type": "instance", "id": ins_id})
        log.info(f"Freeze instance filesystem.")
        cmd = f"ssh root@{hv_ip}" \
                f" docker exec nova_libvirt virsh domfsfreeze {dom_name}"
        await util.exec_cmd(cmd)

        log.info(f"Snapshot all attached volumes on {ins_id}.")
        ss_ins = VolumeSnapshot(self.token_pack)
        objs = ins["os-extended-volumes:volumes_attached"]
        ss_ids = []
        for obj in objs:
            params = {"name": snapshot["id"],
                    "volume_id": obj["id"],
                    "force": True}
            log.info(f"Create a snapshot on volume {obj['id']}.")
            resp = await ss_ins.post({"snapshot": params})
            if resp["status"] == 202:
                vol_ss_id = resp["data"]["snapshot"]["id"]
                row = {"id": vol_ss_id,
                        "volume_id": obj["id"],
                        "instance_snapshot_id": snapshot["id"]}
                await db.add("instance_volume_snapshot", row)
                log.debug(f"Snapshot {vol_ss_id} is created on" \
                        f" volume {obj['id']}.")
                ss_ids.append(vol_ss_id)
            else:
                log.error(f"Snapshot on {obj['id']} failed! {resp['data']}")

        if await self.wait_for_ready(ss_ins, ss_ids, "available", interval=2):
            log.error(f"Create volume snapshot timeout!")
            await db.update(self.table_name, snapshot["id"], update_error)
            return

        log.info(f"Thaw instance filesystem.")
        cmd = f"ssh root@{hv_ip}" \
                f" docker exec nova_libvirt virsh domfsthaw {dom_name}"
        await util.exec_cmd(cmd)
        await lock.release({"type": "instance", "id": ins_id})

        update = {"status": "active"}
        await db.update(self.table_name, snapshot["id"], update)
        if snapshot["retention"]:
            await self.apply_retention(snapshot)
        log.info(f"Task add instance snapshot is done.")

    async def task_delete_instance_snapshot(self, snapshot):
        log.info(f"Task delete instance snapshot {snapshot['id']}.")
        ins = VolumeSnapshot(self.token_pack)
        query = {"instance_snapshot_id": snapshot["id"]}
        objs = await db.get("instance_volume_snapshot",query)
        for obj in objs:
            await lock.acquire({"type": "volume", "id": obj["volume_id"] })
            resp = await ins.delete(obj["id"])
            log.info("Delete volume snapshot {} from {}, status {}.".format(
                    obj["id"], obj["instance_snapshot_id"], resp["status"]))
            if resp["status"] == 202:
                await db.delete("instance_volume_snapshot", obj["id"])
            await lock.release({"type": "volume", "id": obj["volume_id"] })
        update = {"deleted": True, "status": "deleted"}
        await db.update(self.table_name, snapshot["id"], update)
        log.info(f"Task delete instance snapshot is done.")

    async def apply_retention(self, snapshot):
        plan_id = snapshot["plan_id"]
        ins_id = snapshot["instance_id"]
        log.info(f"Apply retention to instance snapshot with plan {plan_id}.")
        query = {"plan_id": plan_id, "instance_id": ins_id}
        objs = await self.get_obj_list(query)
        if not objs:
            log.info(f"No instance snapshot from plan {plan_id}.")
            return
        #log.debug(f"Snapshot list {objs}.")
        objs_sorted = sorted(objs, key=lambda x: x["time_create"],
                reverse=True)
        while len(objs_sorted) > snapshot["retention"]:
            obj = objs_sorted[-1]
            log.info(f"Delete expired instance snapshot {obj['id']}.")
            await self.rh_delete(obj["id"])
            objs_sorted.pop()

