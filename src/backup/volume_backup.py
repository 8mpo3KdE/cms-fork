import asyncio
import logging
import json
from datetime import datetime
from typing import Union
from pydantic import BaseModel, RootModel

from common import util, config, validator, quota, lock
from common.resource_base import ResourceBase
from common.rbd import RBD
from db import db
from openstack.keystone import Auth, Project
from openstack.cinder import Volume, ManageableSnapshot
from openstack.cinder import Snapshot as VolumeSnapshot
from openstack import os_util

log = logging.getLogger("uvicorn")


class VolumeBackupObject(BaseModel):
    name: str
    size: int = 0
    project_id: str = ""
    plan_id: str = ""
    retention: int = 0
    volume_id: str
    volume_name: str = ""
    volume_type: str = ""
    source_zone: str = ""
    property: str = ""
    incremental: bool = False
    snapshot_id: str = ""
    copy_zone: str = ""
    copy_project: str = ""
    usage: int = 0
    snapshots: list = []


class VolumeBackupPost(BaseModel):
    backup: VolumeBackupObject


class ActionUpdate(BaseModel):
    update: dict


class VolumeBackupAction(RootModel):
    root: Union[ActionUpdate]


class VolumeBackupPutObject(BaseModel):
    name: str = None
    status: str = None
    snapshot_id: str = None
    retention: int = 0
    incremental: bool = False
    project_id: str = None
    source_zone: str = ""


class VolumeBackupPut(BaseModel):
    backup: VolumeBackupPutObject


class VolumeBackupSnapshotObject(BaseModel):
    id: str
    name: str
    timestamp: str


class VolumeBackupSnapshotPost(BaseModel):
    snapshot: VolumeBackupSnapshotObject


class VolumeBackup(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="backup",
                table_name="volume_backup")
        self.action_map = {"update": self.action_update}
        self.quota = quota.Quota(self.project_id, config, db, self.token_pack)

    async def rh_get_snapshot_list(self, id):
        query = {"volume_backup_id": id}
        objs = await db.get("volume_snapshot", query)
        return {"status": 200, "data": {"snapshots": objs}}

    async def rh_post_snapshot(self, id, c_req_data):
        req = c_req_data["snapshot"]
        row = {"snapshot_id": req["id"],
                "snapshot_name": req["name"],
                "snapshot_timestamp": req["timestamp"],
                "volume_backup_id": id}
        await db.add("volume_snapshot", row)
        return {"status": 200, "data": {"snapshot": {"id": row['id']}}}

    async def rh_delete_snapshot(self, id, ss_id):
        query = {"snapshot_id": ss_id, "volume_backup_id": id}
        rows = await db.get("volume_snapshot", query)
        for row in rows:
            await db.delete("volume_snapshot", row["id"])
        return {"status": 200, "data": {"snapshot": {"id": ss_id}}}

    async def rh_post(self, c_req_data):
        req = c_req_data[self.res_name]
        res_id = req["volume_id"]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        if req["source_zone"]:
            resp = await self.import_volume_backup(req)
            return resp
        vol = await Volume(self.token_pack).get_obj(res_id)
        if not vol:
            log.error(f"Get volume {res_id} error!")
            return {"status": 404}
        if req["incremental"]:
            backups = await self.get_obj_list()
            for backup in backups:
                if backup["incremental"] and (backup["volume_id"] == res_id):
                    msg = "Incremental backup {} is on this volume.".format(
                            backup["name"])
                    return {"status": 409, "data": {"message": msg}}
        id, msg = await self.add_volume_backup(req, vol)
        if not id:
            return {"status": 400, "data": {"message": msg}}
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def add_volume_backup(self, req, vol, ss_id_rbd=None):
        usage = await self.quota.get_resource_usage("volume_backup")
        if await self.quota.check_quota_limits("cms-backup",
                "volume_backup_total", usage):
            msg = f"Volume backup {usage} reach the limit!"
            log.error(msg)
            return None, msg
        backup = {"name": req["name"],
                "project_id": self.project_id,
                "plan_id": req["plan_id"],
                "property": req["property"],
                "volume_id": vol["id"],
                "volume_name": vol["name"],
                "volume_type": vol["volume_type"],
                "incremental": req["incremental"],
                "snapshot_id": req["snapshot_id"],
                "copy_zone": req["copy_zone"],
                "copy_project": req["copy_project"],
                "status": "building"}
        await db.add(self.table_name, backup)
        backup["retention"] = req["retention"]
        task = asyncio.create_task(
                self.task_add_volume_backup(backup, vol, ss_id_rbd))
        task.add_done_callback(util.task_done_cb)
        return backup["id"], task

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
        if req["name"]:
            update["name"] = req["name"]
        if req["source_zone"]:
            for task in asyncio.all_tasks():
                if task.get_name() == id:
                    log.info(f"Cancel task {id}")
                    task.cancel()
                    break
        if update:
            await db.update(self.table_name, id, update)
        return {"status": 200, "data": {self.res_name: {"id": id}}}

    async def apply_retention(self, backup):
        plan_id = backup["plan_id"]
        res_id = backup["volume_id"]
        log.info(f"Apply retention to volume backup with plan {plan_id}.")
        query = {"plan_id": plan_id, "volume_id": res_id}
        self.project_id = backup["project_id"]
        objs = await self.get_obj_list(query)
        if not objs:
            log.info(f"No volume backup from plan {plan_id}.")
            return
        #log.debug(f"Backup list {objs}.")
        objs_sorted = sorted(objs, key=lambda x: x["time_create"],
                reverse=True)
        tasks = []
        while len(objs_sorted) > backup["retention"]:
            obj = objs_sorted[-1]
            log.info(f"Delete expired volume backup {obj['id']}.")
            task = await self.delete_volume_backup(obj)
            tasks.append(task)
            objs_sorted.pop()
        for task in tasks:
           await task

    async def rh_delete(self, id):
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        task = await self.delete_volume_backup(backup)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def delete_volume_backup(self, backup):
        log.info(f"Delete volume backup {backup['id']}.")
        update = {"status": "deleting"}
        await db.update(self.table_name, backup["id"], update)
        task = asyncio.create_task(self.task_delete_volume_backup(backup))
        task.add_done_callback(util.task_done_cb)
        return task

    async def import_volume_backup(self, req):
        log.info(f"Import backup.")
        backup = {"name": req["name"],
                "size": req["size"],
                "project_id": req["project_id"],
                "plan_id": req["plan_id"],
                "property": req["property"],
                "volume_id": req["volume_id"],
                "volume_name": req["volume_name"],
                "volume_type": req["volume_type"],
                "source_zone": req["source_zone"],
                "incremental": req["incremental"],
                "snapshot_id": req["snapshot_id"],
                "status": "importing"}
        await db.add(self.table_name, backup)
        backup["usage"] = req["usage"]
        task = asyncio.create_task(self.task_import_progress(backup),
                name=backup["id"])
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": backup['id']}}}

    async def action_copy(self, id, args):
        log.info("Action copy backup {} to project {} in zone {}".format(
                id, args["project"], args["zone"]))
        if not f"zone.{args['zone']}" in config.config:
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
        log.info(f"Action update backup {id}.")
        backup = await self.get_obj(id)
        if not backup:
            return {"status": 404}
        if backup["source_zone"]:
            return {"status": 400, "data": {
                    "message": "Can not update copied backup!"}}
        if not backup["incremental"]:
            return {"status": 400, "data": {
                    "message": "Backup is not incremental!"}}
        if not backup["snapshot_id"]:
            return {"status": 400, "data": {
                    "message": "Last snapshot does not exist!"}}
        await self.update_volume_backup(backup)
        return {"status": 202}

    async def update_volume_backup(self, backup, cur_ss_id=None):
        update = {"status": "updating"}
        await db.update(self.table_name, backup["id"], update)
        task = asyncio.create_task(
                self.task_update_volume_backup(backup, cur_ss_id))
        task.add_done_callback(util.task_done_cb)
        return task

    async def create_snapshot_for_backup(self, name, vol_id):
        log.info(f"Create a snapshot on volume {vol_id}.")
        vol_ins = VolumeSnapshot(self.token_pack)
        req = {"name": name, "volume_id": vol_id, "force": True}
        resp = await vol_ins.post({"snapshot": req})
        if resp["status"] != 202:
            log.error(f"Snapshot on {vol_id} failed! {resp}")
            return
        ss_id = resp["data"]["snapshot"]["id"]
        if await self.wait_for_ready(vol_ins, [ss_id], "available"):
            log.error(f"Create volume snapshot timeout!")
            return
        log.info(f"Snapshot {ss_id} is created on volume {vol_id}.")
        return ss_id

    async def import_rbd_snapshot(self, name, vol_id, ss_id):
        log.info(f"Import snapshot {ss_id} on volume {vol_id}.")
        admin_token_pack = await Auth().get_admin_token(self.project_id)
        if not admin_token_pack:
            log.error(f"Get admin token failed!")
            return
        params = {"volume_id": vol_id,
                "name": name,
                "ref": {"source-name": ss_id},
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()[:-7]}}
        resp = await ManageableSnapshot(admin_token_pack).post(
                {"snapshot": params})
        if resp["status"] != 202:
            log.error(f"Import volume snapshot {ss_id} failed!")
            return
        ss_id = resp["data"]["snapshot"]["id"]
        if await self.wait_for_ready(VolumeSnapshot(self.token_pack),
                [ss_id], "available"):
            log.error(f"Import volume snapshot timeout!")
            return
        log.info(f"Snapshot {ss_id} is imported on volume {vol_id}.")
        return ss_id

    async def import_snapshot_to_backup(self, backup_id, inc):
        log.info(f"Import snapshot to backup {backup_id}.")
        ss_ins = VolumeSnapshot(self.token_pack)
        rbd = RBD()
        snapshots = await rbd.get_snapshot("backup", backup_id)
        if not snapshots:
            log.error(f"Get snapshots from backup/{backup_id} failed!")
            return
        for rbd_ss in snapshots:
            ss_id = rbd_ss["name"].replace("snapshot-", "")
            ss = await ss_ins.get_obj(ss_id)
            if not ss:
                log.error(f"Get snapshot {ss_id} failed!")
                continue
            if "backup" in ss["name"]:
                if not inc or (ss["name"] != f"backup-{backup_id}"):
                    log.info(f"Clean up snapshot {ss_id} on backup.")
                    await rbd.delete_snapshot("backup", backup_id,
                            f"snapshot-{ss_id}")
            else:
                row = {"snapshot_id": ss["id"],
                       "snapshot_name": ss["name"],
                       "snapshot_timestamp": ss["created_at"][:-7],
                       "volume_id": ss["volume_id"],
                       "volume_backup_id": backup_id}
                await db.add("volume_snapshot", row)

    async def task_add_volume_backup(self, backup, vol, ss_id_rbd):
        backup_id = backup["id"]
        update_error = {"status": "error"}
        inc = backup["incremental"]
        vol_id = backup["volume_id"]
        rbd = RBD()
        log.info(f"Task add volume backup {backup_id}.")
        if ss_id_rbd:
            ss_id = await self.import_rbd_snapshot(
                    f"backup-{backup_id}", vol_id, ss_id_rbd)
        else:
            ss_id = await self.create_snapshot_for_backup(
                    f"backup-{backup_id}", vol_id)
        if not ss_id:
            await db.update(self.table_name, backup_id, update_error)
            return -1
        image_prop = ""
        pool = await os_util.get_pool_by_volume_type(backup["volume_type"])
        if vol["bootable"] == "true":
            image_prop = "bootable=true"
        ss_ins = VolumeSnapshot(self.token_pack)
        await rbd.deep_copy(pool, f"volume-{vol_id}@snapshot-{ss_id}",
                "backup", backup_id)
        parent = await rbd.get_parent("backup", backup_id)
        if parent:
            await rbd.flatten("backup", backup_id)
        if not inc:
            log.info(f"Not incremental, remove snapshot {ss_id} on volume.")
            await ss_ins.delete(ss_id)
            log.info(f"Not incredmental, remove snapshot {ss_id} on backup.")
            await rbd.delete_snapshot("backup", backup_id,
                    f"snapshot-{ss_id}")
            ss_id = ""
        await self.import_snapshot_to_backup(backup_id, inc)
        if backup["retention"] and not backup["incremental"]:
            await self.apply_retention(backup)
        size_byte = await rbd.get_size("backup", backup_id)
        size_gib = int(size_byte / 1024 / 1024 / 1024)
        if backup["copy_zone"] and backup["copy_project"]:
            backup["size"] = size_gib
            backup["property"] = image_prop
            backup["snapshot_id"] = ss_id
            if await self.copy_volume_backup(backup):
                await db.update(self.table_name, backup_id, update_error)
                return -2
        update = {"status": "active", "size": size_gib,
                "property": image_prop, "snapshot_id": ss_id}
        await db.update(self.table_name, backup_id, update)
        log.info(f"Task add volume backup {backup_id} is done.")

    async def task_delete_volume_backup(self, backup):
        backup_id = backup["id"]
        log.info(f"Task delete volume backup {backup_id}.")
        rbd = RBD()
        snapshots = await rbd.get_snapshot("backup", backup_id)
        if snapshots:
            for ss in snapshots:
                await rbd.delete_snapshot("backup", backup_id, ss["name"])
        await rbd.delete("backup", backup_id)
        ss_id = backup["snapshot_id"]
        if ss_id:
            await VolumeSnapshot(self.token_pack).delete(ss_id)
        query = {"volume_backup_id": backup_id}
        rows = await db.get("volume_snapshot", query)
        for row in rows:
            await db.delete("volume_snapshot", row["id"])
        update = {"deleted": True, "status": "deleted"}
        await db.update(self.table_name, backup_id, update)
        log.info(f"Task delete volume backup {backup_id} is done.")

    async def get_remote_auth(self, zone_name):
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
        svc_url = c["endpoints"][0]["url"] + "/volume/backup"
        return token_pack, svc_url

    async def task_update_volume_backup(self, backup, cur_ss_id):
        backup_id = backup["id"]
        rbd = RBD()
        log.info(f"Task update volume backup {backup_id}.")
        update_error = {"status": "copy error"}
        remote = False
        copy_id = backup["copy_id"]
        copy_zone = backup["copy_zone"]
        if copy_zone and copy_id and backup["copy_project"]:
            remote = True
        vol_id = backup["volume_id"]
        last_ss_id = backup["snapshot_id"]
        res_ins = VolumeSnapshot(self.token_pack)
        obj = await res_ins.get_obj(last_ss_id)
        if not obj:
            log.error(f"Snapshot {last_ss_id} does not exist on"
                    f" volume {vol_id}!")
            await db.update(self.table_name, backup_id, update_error)
            return -1
        if cur_ss_id:
            cur_ss_id = await self.import_rbd_snapshot(
                    f"backup-{backup_id}", vol_id, cur_ss_id)
        else:
            cur_ss_id = await self.create_snapshot_for_backup(
                    f"backup-{backup_id}", vol_id)
        if not cur_ss_id:
            await db.update(self.table_name, backup_id, update_error)
            return -1
        if remote:
            token_pack, svc_url = await self.get_remote_auth(copy_zone)
            if not token_pack:
                await db.update(self.table_name, backup_id, update_error)
                return -1
            log.info(f"Set remote volume backup updating.")
            headers = {"x-auth-token": token_pack["token"],
                    "content-type": "application/json"}
            res_url = f"{svc_url}/{copy_id}"
            params = {"status": "updating"}
            resp = await util.send_req("put", res_url, headers,
                    data = {self.res_name: params})
            if resp["status"] != 200:
                log.error(f"Set remote volume backup updating failed!")
                await db.update(self.table_name, backup_id, update_error)
                return -1
        await lock.acquire({"type": "volume", "id": vol_id})
        pool = await os_util.get_pool_by_volume_type(backup["volume_type"])
        snapshots = await rbd.get_snapshot(pool, f"volume-{vol_id}")
        ss_names = [ss["name"] for ss in snapshots]
        backup_spec = f"backup/{backup_id}"
        idx = ss_names.index("snapshot-" + last_ss_id)
        idx_end = ss_names.index("snapshot-" + cur_ss_id)
        while idx < idx_end:
            ss_spec = f"{pool}/volume-{vol_id}@{ss_names[idx + 1]}"
            cmd = f"rbd export-diff --from-snap {ss_names[idx]}" \
                    f" {ss_spec} - | rbd import-diff - {backup_spec}"
            rc = await util.exec_cmd(cmd)
            if rc:
                await db.update(self.table_name, backup_id, update_error)
                return -1
            if (idx + 1) < idx_end:
                ss_id = ss_names[idx + 1].replace("snapshot-", "")
                ss = await res_ins.get_obj(ss_id)
                row = {"snapshot_id": ss["id"],
                       "snapshot_name": ss["name"],
                       "snapshot_timestamp": ss["created_at"][:-7],
                       "volume_id": ss["volume_id"],
                       "volume_backup_id": backup_id}
                await db.add("volume_snapshot", row)
            idx += 1
        await lock.release({"type": "volume", "id": vol_id})
        if remote:
            idx = ss_names.index("snapshot-" + last_ss_id)
            while idx < idx_end:
                ss_spec = f"backup/{backup_id}@{ss_names[idx + 1]}"
                cmd = f"rbd export-diff --from-snap {ss_names[idx]}" \
                        f" {ss_spec} -" \
                        f" | rbd --cluster {copy_zone} --id infra" \
                        f" import-diff - backup/{copy_id}"
                rc = await util.exec_cmd(cmd)
                if rc:
                    await db.update(self.table_name, backup_id, update_error)
                    return -1
                if (idx + 1) < idx_end:
                    ss_id = ss_names[idx + 1].replace("snapshot-", "")
                    ss = await res_ins.get_obj(ss_id)
                    params = {"id": ss["id"],
                            "name": ss["name"],
                            "timestamp": ss["created_at"][:-7]}
                    res_url = f"{svc_url}/{copy_id}/snapshot"
                    await util.send_req("post", res_url, headers,
                            data={"snapshot": params})
                idx += 1
        log.info(f"Remove snapshot {last_ss_id} from volume.")
        await res_ins.delete(last_ss_id)
        log.info(f"Remove snapshot {last_ss_id} from backup.")
        await rbd.delete_snapshot("backup", backup_id,
                f"snapshot-{last_ss_id}")
        if remote:
            log.info(f"Remove snapshot {last_ss_id} from remote backup.")
            await rbd.delete_snapshot("backup", copy_id,
                    f"snapshot-{last_ss_id}", cluster=copy_zone, id="infra")
        log.info(f"Clean up snapshot on backup {backup_id}.")

        snapshots = await rbd.get_snapshot(pool, f"volume-{vol_id}")
        vol_ss_names = [ss["name"] for ss in snapshots]
        snapshots = await rbd.get_snapshot("backup", backup_id)
        backup_ss_names = [ss["name"] for ss in snapshots]
        for name in backup_ss_names:
            if name not in vol_ss_names:
                await rbd.delete_snapshot("backup", backup_id, name)
                ss_id = name.replace("snapshot-", "")
                query = {"volume_backup_id": backup_id, "snapshot_id": ss_id}
                objs = await db.get("volume_snapshot", query)
                for obj in objs:
                    await db.delete("volume_snapshot", obj["id"])
        if remote:
            log.info(f"Clean up snapshot on remote backup.")
            for name in backup_ss_names:
                if name not in vol_ss_names:
                    await rbd.delete_snapshot("backup", copy_id, name,
                            cluster=copy_zone, id="infra")
                    ss_id = name.replace("snapshot-", "")
                    res_url = f"{svc_url}/{copy_id}/snapshot/{ss_id}"
                    await util.send_req("delete", res_url, headers)
        update = {"status": "active", "snapshot_id": cur_ss_id}
        await db.update(self.table_name, backup_id, update)
        if remote:
            log.info(f"Set remote volume backup active.")
            params = {"status": "active"}
            res_url = f"{svc_url}/{copy_id}"
            resp = await util.send_req("put", res_url, headers,
                    data = {self.res_name: params})
            if resp["status"] != 200:
                log.error(f"Set remote volume backup active failed!")
                await db.update(self.table_name, backup_id, update_error)
                return -1
        log.info(f"Task update backup {backup_id} is done.")

    async def copy_volume_backup(self, backup):
        backup_id = backup["id"]
        copy_zone = backup["copy_zone"]
        rbd = RBD()
        log.info(f"Task copy volume backup {backup_id}.")
        update = {"status": "copying"}
        await db.update(self.table_name, backup_id, update)
        token_pack, svc_url = await self.get_remote_auth(copy_zone)
        if not token_pack:
            return -1
        project_id = await Project(token_pack).get_id_by_name(
                backup["copy_project"])
        if not project_id:
            log.error(f"Get project {backup['copy_project']} failed!")
            return -1
        log.info(f"Create remote volume backup in {copy_zone}.")
        usage = await rbd.get_usage("backup", backup_id)
        headers = {"x-auth-token": token_pack["token"],
                "content-type": "application/json"}
        params = {"name": backup["name"],
                "size": backup["size"],
                "project_id": project_id,
                "plan_id": backup["plan_id"],
                "volume_id": backup["volume_id"],
                "volume_name": backup["volume_name"],
                "volume_type": backup["volume_type"],
                "source_zone": config.config["DEFAULT"]["zone"],
                "incremental": backup["incremental"],
                "snapshot_id": backup["snapshot_id"],
                "property": backup["property"],
                "usage": usage}
        resp = await util.send_req("post", svc_url, headers,
                data={self.res_name: params})
        if resp["status"] != 202:
            log.error(f"Create remote volume backup in {copy_zone} failed!")
            log.debug(f"status: {resp['status']}, data: {resp['data']}")
            return -1
        copy_id = resp["data"][self.res_name]["id"]
        log.info(f"Copy backup to remote backup {copy_id}.")
        args = "--export-format 2 --no-progress"
        cmd = f"rbd export {args} backup/{backup_id} -" \
                f" | rbd --cluster {copy_zone} --id infra" \
                f" import {args} - backup/{copy_id}"
        rc = await util.exec_cmd(cmd)
        if rc:
            log.error(f"Copy backup failed {rc}!")
            return -1
        log.info(f"Update remote backup {copy_id} snapshot.")
        token_pack, svc_url = await self.get_remote_auth(copy_zone)
        if not token_pack:
            return -1
        headers = {"x-auth-token": token_pack["token"],
                    "content-type": "application/json"}
        res_url = f"{svc_url}/{copy_id}/snapshot"
        query = {"volume_backup_id": backup_id}
        objs = await db.get("volume_snapshot", query)
        for obj in objs:
            params = {"id": obj["snapshot_id"],
                    "name": obj["snapshot_name"],
                    "timestamp": obj["snapshot_timestamp"]}
            await util.send_req("post", res_url, headers,
                    data={"snapshot": params})
        log.info(f"Update remote backup {copy_id} active.")
        params = {"status": "active",
                "source_zone": config.config["DEFAULT"]["zone"]}
        if "retention" in backup:
            params["retention"] = backup["retention"]
            params["project_id"] = project_id
        res_url = f"{svc_url}/{copy_id}"
        resp = await util.send_req("put", res_url, headers,
                data={self.res_name: params})
        if resp["status"] != 200:
            log.error(f"Set remote backup status error!")
            return -1
        update = {"copy_id": copy_id}
        await db.update(self.table_name, backup_id, update)
        log.info(f"Task copy backup {backup_id} is done.")
        return 0

    async def task_import_progress(self, backup):
        rbd = RBD()
        backup_id = backup["id"]
        src_usage = backup["usage"]
        usage = 0
        while usage < src_usage:
            await asyncio.sleep(5)
            usage = await rbd.get_usage("backup", backup_id)
            update = {"status": "importing {:.2%}".format(usage/src_usage)}
            await db.update(self.table_name, backup_id, update)

