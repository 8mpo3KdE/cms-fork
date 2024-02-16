import asyncio
import uuid
import logging
from typing import Union
from pydantic import BaseModel, RootModel
from common import util, config, validator, quota, lock
from common.resource_base import ResourceBase
from common.rbd import RBD
from db import db
from volume_backup import VolumeBackup
from openstack.keystone import Auth, Project
from openstack.nova import Instance, Hypervisor
from openstack.cinder import Volume
from openstack import os_util

log = logging.getLogger("uvicorn")


class InstanceBackupObject(BaseModel):
    name: str
    size: int = 0
    project_id: str = ""
    plan_id: str = ""
    retention: int = 0
    instance_id: str = ""
    instance_name: str = ""
    source_zone: str = ""
    property: str = ""
    incremental: bool = False
    copy_zone: str = ""
    copy_project: str = ""
    volume_backup_ids: list = []


class InstanceBackupPost(BaseModel):
    backup: InstanceBackupObject


class ActionRestoreArgs(BaseModel):
    volume_backups: list


class ActionRestore(BaseModel):
    restore: ActionRestoreArgs


class ActionUpdate(BaseModel):
    update: dict


class InstanceBackupAction(RootModel):
    root: Union[ActionRestore, ActionUpdate]


class InstanceBackupPutObject(BaseModel):
    name: str = None
    status: str = None
    snapshot_id: str = None
    retention: int = 0
    incremental: bool = False
    project_id: str = None


class InstanceBackupPut(BaseModel):
    backup: InstanceBackupPutObject


class InstanceBackup(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="backup",
                table_name="instance_backup")
        self.action_map = {"restore": self.action_restore,
                "update": self.action_update}
        self.quota = quota.Quota(self.project_id, config, db, self.token_pack)

    async def rh_get(self, id):
        obj = await self.get_obj(id)
        if obj:
            obj["volume_backups"] = await db.get("instance_volume_backup",
                    {"instance_backup_id": id})
            return {"status": 200, "data": {self.res_name: obj}}
        else:
            return {"status": 404}

    async def rh_post(self, req_data):
        req = req_data[self.res_name]
        ins_id = req["instance_id"]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        if req["source_zone"]:
            resp = await self.import_instance_backup(req)
            return resp
        ins = await Instance(self.token_pack).get_obj(ins_id)
        if not ins:
            log.error(f"Get instance {ins_id} error!")
            msg = f"Instance ID {ins_id} is invalid!"
            return {"status": 400, "data": {"message": msg}}
        allowed_status = ["ACTIVE", "SHUTOFF", "SUSPENDED", "PAUSED"]
        if ins["status"] not in allowed_status:
            msg = "Instance {} status {} not in {}!".format(
                    ins_id, ins["status"], allowed_status)
            return {"status": 400, "data": {"message": msg}}
        if not ins["os-extended-volumes:volumes_attached"]:
            msg = f"Instance ID {ins_id} has no volumes attached!"
            return {"status": 400, "data": {"message": msg}}
        if await self.quota.check_quota_limits("cms-backup",
                "instance_backup_total",
                await self.quota.get_resource_usage("instance_backup")):
            log.error("Instance backup reach the limit")
            return {"status": 400, "data": "Instance backup reach the limit"}
        id = await self.add_instance_backup(req, ins)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def add_instance_backup(self, req, ins):
        backup = {"name": req["name"],
                "project_id": self.project_id,
                "plan_id": req["plan_id"],
                "instance_id": ins["id"],
                "instance_name": ins["name"],
                "incremental": req["incremental"],
                "copy_zone": req["copy_zone"],
                "copy_project": req["copy_project"],
                "status": "building"}
        await db.add(self.table_name, backup)
        backup["retention"] = req["retention"]
        task = asyncio.create_task(
                self.task_add_instance_backup(backup, ins["id"]))
        task.add_done_callback(util.task_done_cb)
        return backup["id"]

    async def rh_put(self, id, req_data):
        req = req_data[self.res_name]
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        update = {}
        if req["retention"] and not req["incremental"]:
            backup["retention"] = req["retention"]
            await self.apply_retention(backup)
        if req["status"]:
            update["status"] = req["status"]
        if req["snapshot_id"]:
            update["snapshot_id"] = req["snapshot_id"]
        if update:
            await db.update(self.table_name, id, update)
        return {"status": 200, "data": {self.res_name: {"id": id}}}

    async def apply_retention(self, backup):
        plan_id = backup["plan_id"]
        res_id = backup["instance_id"]
        log.info(f"Apply retention to instance backup with plan {plan_id}.")
        query = {"plan_id": plan_id, "instance_id": res_id}
        self.project_id = backup["project_id"]
        objs = await self.get_obj_list(query)
        if not objs:
            log.info(f"No instance backup from plan {plan_id}.")
            return
        #log.debug(f"Backup list {objs}.")
        objs_sorted = sorted(objs, key=lambda x: x["time_create"],
                reverse=True)
        while len(objs_sorted) > backup["retention"]:
            obj = objs_sorted[-1]
            log.info(f"Delete expired instance backup {obj['id']}.")
            await self.rh_delete(obj["id"])
            objs_sorted.pop()

    async def rh_delete(self, id):
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        update = {"status": "deleting"}
        await db.update(self.table_name, id, update)
        task = asyncio.create_task(self.task_delete_instance_backup(backup))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def import_instance_backup(self, req):
        log.info(f"Import instance backup.")
        backup = {"name": req["name"],
                "project_id": req["project_id"],
                "instance_name": req["instance_name"],
                "plan_id": req["plan_id"],
                "source_zone": req["source_zone"],
                "incremental": req["incremental"],
                "status": "importing"}
        await db.add(self.table_name, backup)
        for vol_backup_id in req["volume_backup_ids"]:
            row = {"id": vol_backup_id,
                    "instance_backup_id": backup["id"]}
            await db.add("instance_volume_backup", row)
        return {"status": 202, "data": {self.res_name: {"id": backup['id']}}}

    async def action_restore(self, id, args):
        log.info(f"Action restore instance backup {id}.")
        task = asyncio.create_task(self.task_restore_instance(id, args))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def action_copy(self, id, args):
        log.info("Action copy backup {} to project {} in zone {}".format(
                id, args["project"], args["zone"]))
        if f"zone.{args['zone']}" not in config.config:
            msg = f"Zone {args['zone']} is not supported."
            log.error(msg)
            return {"status": 400, "data": {"message": msg}}
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        task = asyncio.create_task(self.task_copy_volume(backup, args))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def action_update(self, id, args):
        log.info(f"Action update instance backup {id}.")
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        if backup["source_zone"]:
            return {"status": 400, "data": {
                    "message": "Can not update copied backup!"}}
        if not backup["incremental"]:
            return {"status": 400, "data": {
                    "message": "Backup is not incremental!"}}
        await self.update_instance_backup(backup)
        return {"status": 202}

    async def update_instance_backup(self, backup):
        update = {"status": "updating"}
        await db.update(self.table_name, backup["id"], update)
        task = asyncio.create_task(self.task_update_instance_backup(backup))
        task.add_done_callback(util.task_done_cb)

    async def create_rbd_snapshot(self, ins_id, vol_ids=None):
        rbd = RBD()
        admin_token_pack = await Auth().get_admin_token(self.project_id)
        if not admin_token_pack:
            log.error(f"Get admin token failed!")
            return
        ins = await Instance(admin_token_pack).get_obj(id=ins_id)
        dom_name = ins["OS-EXT-SRV-ATTR:instance_name"]
        hv_name = ins["OS-EXT-SRV-ATTR:hypervisor_hostname"]
        hvs = await Hypervisor(admin_token_pack).get_obj_list()
        if not hvs:
            log.error(f"Get the list of hypervisors failed!")
            return
        for hv in hvs:
            if hv["hypervisor_hostname"] == hv_name:
                hv_ip = hv["host_ip"]
                break
        else:
            log.error(f"Hypervisor {hv_name} is not found!")
            return
        vol_ins = Volume(self.token_pack)
        vols = []
        if vol_ids:
            for id in vol_ids:
                vol = await vol_ins.get_obj(id)
                vols.append(vol)
        else:
            for vol_attach in ins["os-extended-volumes:volumes_attached"]:
                vol = await vol_ins.get_obj(vol_attach["id"])
                vols.append(vol)
        await lock.acquire({"type": "instance", "id": ins_id})
        log.info(f"Freeze instance {ins_id}.")
        cmd = f"ssh root@{hv_ip}" \
                f" docker exec nova_libvirt virsh domfsfreeze {dom_name}"
        await util.exec_cmd(cmd)
        for vol in vols:
            ss_id = str(uuid.uuid4())
            pool = await os_util.get_pool_by_volume_type(vol["volume_type"])
            await rbd.create_snapshot(pool, f"volume-{vol['id']}", ss_id)
            vol["ss_id_rbd"] = ss_id
        log.info(f"Thaw instance {ins_id}.")
        cmd = f"ssh root@{hv_ip}" \
                f" docker exec nova_libvirt virsh domfsthaw {dom_name}"
        await util.exec_cmd(cmd)
        await lock.release({"type": "instance", "id": ins_id})
        return vols

    async def task_add_instance_backup(self, backup, ins_id):
        backup_id = backup["id"]
        update_error = {"status": "error"}
        rbd = RBD()
        log.info(f"Task add instance backup {backup_id}.")
        vols = await self.create_rbd_snapshot(ins_id)
        if not vols:
            await db.update(self.table_name, backup_id, update_error)
            return
        params = {"name": backup_id,
                "project_id": self.project_id,
                "plan_id": backup["plan_id"],
                "property": None,
                "snapshot_id": None,
                "incremental": backup["incremental"],
                "retention": backup["retention"],
                "copy_zone": backup["copy_zone"],
                "copy_project": backup["copy_project"]}
        backup_ins = VolumeBackup(self.token_pack)
        for vol in vols:
            vol_backup_id, task = await backup_ins.add_volume_backup(
                    params, vol, vol["ss_id_rbd"])
            if vol_backup_id:
                row = {"id": vol_backup_id,
                        "volume_id": vol["id"],
                        "instance_backup_id": backup_id}
                await db.add("instance_volume_backup", row)
                vol["backup_id"] = vol_backup_id
                vol["task"] = task
            else:
                log.error(f"Backup on {vol['id']} failed!")
                pool = await os_util.get_pool_by_volume_type(
                        vol["volume_type"])
                await rbd.delete_snapshot(pool, f"volume-{vol['id']}",
                        vol["ss_id_rbd"])
        err = False
        for vol in vols:
            if not vol["backup_id"]:
                continue
            log.info(f"Wait for add_volume_backup on {vol['id']}.")
            rc = await vol["task"]
            if rc:
                log.error(f"add_volume_backup on {vol['id']} failed {rc}!")
                if rc == -1:
                    pool = await os_util.get_pool_by_volume_type(
                            vol["volume_type"])
                    await rbd.delete_snapshot(pool, f"volume-{vol['id']}",
                            vol["ss_id_rbd"])
                err = True
        if err:
            await db.update(self.table_name, backup_id, update_error)
            return
        if backup["copy_zone"] and backup["copy_project"]:
            vol_backup_copy_ids = []
            for vol in vols:
                vol_backup = await backup_ins.get_obj(vol["backup_id"])
                vol_backup_copy_ids.append(vol_backup["copy_id"])
            if await self.copy_instance_backup(backup, vol_backup_copy_ids):
                await db.update(self.table_name, backup_id, update_error)
                return
        update = {"status": "active"}
        await db.update(self.table_name, backup_id, update)
        if backup["retention"] and not backup["incremental"]:
            await self.apply_retention(backup)
        log.info(f"Task add instance backup {backup_id} is done.")

    async def get_auth_and_svc_url(self, zone_name):
        log.info(f"Auth from remote zone {zone_name}.")
        zone_conf = config.config[f"zone.{zone_name}"]
        token_pack = await Auth().get_svc_token(zone_conf)
        if not token_pack:
            log.error(f"Auth from zone {zone_name} failed!")
            return None, None
        for c in token_pack["catalog"]:
            if c["type"] == "cms-backup":
                break
        else:
            log.error(f"No CMS backup endpoint from zone {zone_name}!")
            return None, None
        svc_url = c["endpoints"][0]["url"] + "/instance/backup"
        return token_pack, svc_url

    async def copy_instance_backup(self, backup, vol_backup_ids):
        copy_zone = backup["copy_zone"]
        log.info(f"Create remote instance backup in {copy_zone}.")
        update_error = {"status": "copy error"}
        backup_id = backup["id"]
        token_pack, svc_url = await self.get_auth_and_svc_url(copy_zone)
        if not token_pack:
            return -1
        project_id = await Project(token_pack).get_id_by_name(
                backup["copy_project"])
        if not project_id:
            log.error(f"Get project {backup['copy_project']} failed!")
            return -1
        headers = {"x-auth-token": token_pack["token"],
                "content-type": "application/json"}
        params = {"name": backup["name"],
                "project_id": project_id,
                "plan_id": backup["plan_id"],
                "instance_name": backup["instance_name"],
                "source_zone": config.config["DEFAULT"]["zone"],
                "incremental": backup["incremental"],
                "volume_backup_ids": vol_backup_ids}
        resp = await util.send_req("post", svc_url, headers,
                data={self.res_name: params})
        if resp["status"] != 202:
            log.error(f"Create remote instance backup in {copy_zone} failed!")
            log.debug(f"status: {resp['status']}, data: {resp['data']}")
            return -1
        copy_id = resp["data"][self.res_name]["id"]
        log.info("Rename remote volume backup to instance backup ID.")
        params = {"name": copy_id}
        for vol_backup_id in vol_backup_ids:
            url = svc_url.replace("instance", "volume") + f"/{vol_backup_id}"
            await util.send_req("put", url, headers,
                    data={self.res_name: params})
        log.info("Update remote instance backup status.")
        params = {"status": "active"}
        if "retention" in backup:
            params["retention"] = backup["retention"]
            params["project_id"] = project_id
        url = f"{svc_url}/{copy_id}"
        await util.send_req("put", url, headers,
                data={self.res_name: params})
        update = {"copy_id": copy_id}
        await db.update(self.table_name, backup_id, update)
        return 0

    async def task_delete_instance_backup(self, backup):
        backup_id = backup["id"]
        res_id = backup["instance_id"]
        log.info(f"Task delete instance backup {backup_id}.")
        backup_ins = VolumeBackup(self.token_pack)
        query = {"instance_backup_id": backup_id}
        objs = await db.get("instance_volume_backup", query)
        tasks = []
        for obj in objs:
            log.debug(f"Delete volume backup {obj['id']} from"
                    f" instance backup {obj['instance_backup_id']}")
            vol_backup = await backup_ins.get_obj(obj["id"])
            if vol_backup:
                task = await backup_ins.delete_volume_backup(vol_backup)
                tasks.append(task)
            else:
                log.info(f"Volume backup {obj['id']} is already deleted.")
            await db.delete("instance_volume_backup", obj["id"])
        for task in tasks:
            await task
        update = {"deleted": True, "status": "deleted"}
        await db.update(self.table_name, backup_id, update)
        log.info(f"Task delete instance backup {backup_id} is done.")

    async def task_update_instance_backup(self, backup):
        backup_id = backup["id"]
        log.info(f"Task update instance backup {backup_id}.")
        update_error = {"status": "error"}
        remote = False
        copy_id = backup["copy_id"]
        copy_zone = backup["copy_zone"]
        if copy_zone and copy_id and backup["copy_project"]:
            remote = True
        if remote:
            token_pack, svc_url = await self.get_auth_and_svc_url(copy_zone)
            if not token_pack:
                await db.update(self.table_name, backup_id, update_error)
                return -1
            log.info(f"Set remote instance backup updating.")
            headers = {"x-auth-token": token_pack["token"],
                    "content-type": "application/json"}
            res_url = f"{svc_url}/{copy_id}"
            params = {"status": "updating"}
            resp = await util.send_req("put", res_url, headers,
                    data={self.res_name: params})
            if resp["status"] != 200:
                log.error(f"Set remote instance backup updating failed!")
                await db.update(self.table_name, backup_id, update_error)
                return -1
        ins = VolumeBackup(self.token_pack)
        objs = await db.get("instance_volume_backup",
                {"instance_backup_id": backup_id})
        vol_ids = [obj["volume_id"] for obj in objs]
        vols = await self.create_rbd_snapshot(backup["instance_id"], vol_ids)
        if not vols:
            await db.update(self.table_name, backup_id, update_error)
            return -1
        tasks = []
        for vol in vols:
            query = {"instance_backup_id": backup_id,
                    "volume_id": vol["id"]}
            objs = await db.get("instance_volume_backup", query)
            backup = await ins.get_obj(objs[0]["id"])
            task = await ins.update_volume_backup(backup, vol["ss_id_rbd"])
            tasks.append(task)
        log.info("Wait for all update_volume_backup tasks done.")
        err = False
        for task in tasks:
            if await task:
                err = True
        if err:
            log.error("add_volume_backup task failed!")
            await db.update(self.table_name, backup_id, update_error)
            return -1
        update = {"status": "active"}
        await db.update(self.table_name, backup_id, update)
        if remote:
            log.info(f"Set remote instance backup active.")
            params = {"status": "active"}
            resp = await util.send_req("put", res_url, headers,
                    data={self.res_name: params})
            if resp["status"] != 200:
                log.error(f"Set remote instance backup active failed!")
                await db.update(self.table_name, backup_id, update_error)
                return -1
        log.info(f"Task update instance backup {backup_id} is done.")

    async def task_restore_instance(self, id, args):
        log.info(f"Task restore instance backup {id}.")
        ins = VolumeBackup(self.token_pack)
        for vb in args["volume_backups"]:
            restore_args = {}
            if "volume_name" in vb:
                restore_args["volume_name"] = vb["volume_name"]
            resp = await ins.action_restore(vb["id"], restore_args)
        log.info(f"Task restore instance backup is done.")

