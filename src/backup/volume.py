import asyncio
import logging
import uuid
import json
from common import util, config
from common.resource_base import ResourceBase
from common.rbd import RBD
from db import db
from volume_backup import VolumeBackup
from openstack.keystone import Auth
from openstack.cinder import Volume as OSVolume
from openstack.cinder import Snapshot as OSVolumeSnapshot
from openstack.cinder import ManageableVolume as OSManageableVolume
from openstack.cinder import ManageableSnapshot as OSManageableSnapshot
from openstack.cinder import Host as OSHost
from openstack.cinder import VolumeType as OSVolumeType
from openstack.cinder import VolumeTransfer as OSVolumeTransfer
from openstack.nova import Instance
from openstack import os_util

log = logging.getLogger("uvicorn")


class Volume(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="volume")

    async def rh_post(self, c_req):
        body = await c_req.json()
        req = body[self.res_name]
        log.info(f"Create volume from backup {req['backup_id']}.")
        backup = await VolumeBackup(self.token_pack).get_obj(req["backup_id"])
        if not backup:
            return {"status": 404}
        vol_types = await OSVolumeType(config.svc_token_pack).get_obj_list()
        if not vol_types:
            msg = "Get the list of volume types failed!"
            return {"status": 500, "data": {"message": msg}}
        if "volume_type" not in req:
            req["volume_type"] = backup["volume_type"]
        for vol_type in vol_types:
            if vol_type["name"] == req["volume_type"]:
                break
        else:
            msg = f"Volume type {req['volume_type']} is not found!"
            return {"status": 500, "data": {"message": msg}}
        req["backend"] = vol_type["extra_specs"]["volume_backend_name"]
        hosts = await OSHost(config.svc_token_pack).get_obj_list()
        if not hosts:
            msg = "Get the list of hosts failed!"
            return {"status": 500, "data": {"message": msg}}
        for host in hosts:
            if (host["service"] == "cinder-volume") \
                    and (req["backend"] == host["host_name"].split("@")[1]):
                break
        else:
            msg = f"Volume host for backend {req['backend']} is not found!"
            return {"status": 500, "data": {"message": msg}}
        req["host"] = host
        task = asyncio.create_task(
                self.task_create_from_backup(backup, req))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def rh_post_action(self, id, c_req):
        body = await c_req.json()
        action = list(body.keys())[0]
        if action == "rollback":
            return await self.action_rollback(id, body[action])
        msg = f"Invalid action {action}!"
        return {"status": 400, "data": {"message": msg}}

    async def action_rollback(self, id, args):
        ss_id = args["snapshot_id"]
        log.info(f"Action rollback volume {id} to snapshot {ss_id}.")
        vol = await OSVolume(self.token_pack).get_obj(id)
        if not vol:
            msg = f"Volume {id} is not found!"
            return {"status": 404, "data": {"message": msg}}
        if (vol["status"] != "available") and (vol["status"] != "in-use"):
            msg = f"Volume {id} is not available or in-use!"
            return {"status": 409, "data": {"message": msg}}
        ins_ins = Instance(self.token_pack)
        for attach in vol["attachments"]:
            ins = await ins_ins.get_obj(attach["server_id"])
            if not ins:
                msg = f"Instance {attach['server_id']} is not found!"
                return {"status": 404, "data": {"message": msg}}
            if ins["status"] != "SHUTOFF":
                msg = f"Instance {ins['id']} is not SHUTOFF!"
                return {"status": 409, "data": {"message": msg}}
        vol_ss = await OSVolumeSnapshot(self.token_pack).get_obj(ss_id)
        if not vol_ss:
            msg = f"Volume snapshot {ss_id} is not found!"
            return {"status": 404, "data": {"message": msg}}
        pool = await os_util.get_pool_by_volume_type(vol["volume_type"])
        spec = f"{pool}/volume-{id}@snapshot-{ss_id}"
        log.info(f"Rollback to snapshot {spec}.")
        await RBD().rollback_snapshot(pool, f"volume-{id}",
                f"snapshot-{ss_id}")
        return {"status": 200}

    async def task_create_from_backup(self, backup, req):
        backup_id = backup["id"]
        log.info(f"Task create volume from backup {backup_id}.")
        pool = await os_util.get_pool_by_volume_type(req["volume_type"])
        # Image name will be updated with the correct UUID
        # after imported by Cinder.
        tmp_id = str(uuid.uuid4())
        await RBD().deep_copy("backup", backup_id, pool, f"volume-{tmp_id}")
        log.info(f"Import volume {pool}/volume-{tmp_id}")
        if "name" in req:
            params = {"name": req["name"]}
        elif backup["volume_name"] == backup["volume_id"]:
            params = {}
        else:
            params = {"name": backup["volume_name"]}
        if backup["property"] and ("bootable=true" in backup["property"]):
            params["bootable"] = True
        params["volume_type"] = req["volume_type"]
        params["host"] = req["host"]["host_name"] + f"#{req['backend']}"
        params["ref"] = {"source-name": f"volume-{tmp_id}"}
        admin_token_pack = await Auth().get_admin_token(self.project_id)
        if not admin_token_pack:
            log.error(f"Get admin token failed!")
            return
        resp = await OSManageableVolume(admin_token_pack).post(
                {"volume": params})
        if resp["status"] != 202:
            log.error(f"Import image failed!")
            return
        vol_id = resp["data"]["volume"]["id"]
        if await self.wait_for_ready(OSVolume(self.token_pack),
                [vol_id], "available"):
            log.error(f"Import volume {vol_id} timeout!")
            return
        query = {"volume_backup_id": backup_id}
        objs = await db.get("volume_snapshot", query)
        ins = OSManageableSnapshot(admin_token_pack)
        ss_ids = []
        for obj in objs:
            log.info(f"Import snapshot {obj['snapshot_name']}")
            params = {"volume_id": vol_id,
                    "name": obj["snapshot_name"],
                    "ref": {"source-name": f"snapshot-{obj['snapshot_id']}"},
                    "metadata": {"timestamp": obj["snapshot_timestamp"]}}
            resp = await ins.post({"snapshot": params})
            if resp["status"] != 202:
                log.error(f"Import snapshot {ss_name} failed!")
                return
            ss_ids.append(resp["data"]["snapshot"]["id"])
        if await self.wait_for_ready(OSVolumeSnapshot(self.token_pack),
                ss_ids, "available"):
            log.error(f"Import volume snapshot timeout!")
            return
        '''
        log.info(f"Transfer volume {vol_id}.")
        params = {"transfer": {"volume_id": vol_id}}
        resp = await OSVolumeTransfer(config.svc_token_pack).post(params)
        if resp["status"] != 202:
            log.error(f"Transfer volume {vol_id} failed!")
            return
        params = {"accept": {"auth_key": resp["data"]["transfer"]["auth_key"]}}
        log.info(f"Accept volume {vol_id}.")
        resp = await OSVolumeTransfer(self.token_pack).post_accept(
                resp["data"]["transfer"]["id"], params)
        if resp["status"] != 202:
            log.error(f"Accept volume {vol_id} failed!")
            return
        '''

