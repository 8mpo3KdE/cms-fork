import asyncio
import logging
from enum import Enum
from pydantic import BaseModel

from common import util
from common import validator
from db import db
from plan import PlanBase
from backup.volume_backup import VolumeBackup

log = logging.getLogger("uvicorn")


class ResourceType(str, Enum):
    instance = "instance"
    volume = "volume"


class BackupPlanObject(BaseModel):
    name: str
    resource_type: ResourceType
    schedule: str
    retention: int = 0
    incremental: bool = False
    copy_zone: str = ""
    copy_project: str = ""
    credential_name: str
    credential_secret: str


class BackupPlanPost(BaseModel):
    backup_plan: BackupPlanObject


class BackupPlan(PlanBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="backup_plan")

    async def rh_post(self, c_req_data):
        req = c_req_data[self.res_name]
        v = {"name": "name", "schedule": "cron-expr"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        result = await self.validate_credential(req["credential_name"],
                req["credential_secret"])
        if result["msg"]:
            return {"status": 400, "data": {"message": result["msg"]}}
        row = {"name": req["name"],
                "resource_type": req["resource_type"],
                "project_id": self.project_id,
                "incremental": req["incremental"],
                "schedule": req["schedule"],
                "retention": req["retention"],
                "copy_zone": req["copy_zone"],
                "copy_project": req["copy_project"],
                "status": "active"}
        await db.add(self.res_name, row)
        task = asyncio.create_task(self.task_add_plan(row, req))
        task.add_done_callback(util.task_done_cb)
        return {"status": 201, "data": {self.res_name: {"id": row["id"]}}}

    async def task_execute_plan(self, plan):
        rt = plan["resource_type"]
        log.info(f"Task execute {rt} backup plan {plan['id']}.")
        ress = await self.get_ress(plan)
        if not ress:
            return
        if plan["incremental"]:
            await self.do_inc_backup(plan, ress)
        else:
            await self.do_backup(plan, ress)
        log.info(f"Task execute backup plan is done.")

    async def do_backup(self, plan, ress):
        rt = plan["resource_type"]
        log.info(f"Backup {rt} by plan {plan['id']}.")
        if rt == "instance":
            params = {"name": f"plan-{plan['id']}",
                    "plan_id": plan["id"],
                    "incremental": plan["incremental"],
                    "copy_zone": plan["copy_zone"],
                    "copy_project": plan["copy_project"],
                    "retention": plan["retention"]}
            for res in ress:
                params["instance_id"] = res["id"]
                await self.add_instance_backup(params)
        elif rt == "volume":
            params = {"name": f"plan-{plan['id']}",
                    "plan_id": plan["id"],
                    "incremental": plan["incremental"],
                    "copy_zone": plan["copy_zone"],
                    "copy_project": plan["copy_project"],
                    "retention": plan["retention"]}
            for res in ress:
                params["volume_id"] = res["id"]
                await self.add_volume_backup(params)
        else:
            return

    async def do_inc_backup(self, plan, ress):
        rt = plan["resource_type"]
        log.info(f"Incremental backup {rt} by plan {plan['id']}.")
        if rt == "instance":
            backups = await self.get_instance_backup()
            params = {"name": f"plan-{plan['id']}",
                    "plan_id": plan["id"],
                    "incremental": plan["incremental"],
                    "copy_zone": plan["copy_zone"],
                    "copy_project": plan["copy_project"],
                    "retention": plan["retention"]}
            for res in ress:
                for backup in backups:
                    if (backup["name"] == f"plan-{plan['id']}") \
                            and (backup["instance_id"] == res["id"]):
                        log.info("Incremental backup for instance" \
                                f" {res['id']} by plan {plan['id']} exists.")
                        break
                else:
                    log.info("Create incremental backup for instance" \
                            f" {res['id']} by plan {plan['id']}.")
                    params["instance_id"] = res["id"]
                    await self.add_instance_backup(params)
                    continue
                log.info("Update incredmental backup for instance" \
                        f" {res['id']} by plan {plan['id']}.")
                await self.update_instance_backup(backup["id"])
        elif rt == "volume":
            backups = await self.get_volume_backup()
            params = {"name": f"plan-{plan['id']}",
                    "plan_id": plan["id"],
                    "incremental": plan["incremental"],
                    "copy_zone": plan["copy_zone"],
                    "copy_project": plan["copy_project"],
                    "retention": plan["retention"]}
            for res in ress:
                for backup in backups:
                    if (backup["name"] == f"plan-{plan['id']}") \
                            and (backup["volume_id"] == res["id"]):
                        log.info("Incremental backup for volume" \
                                f" {res['id']} by plan {plan['id']} exists.")
                        break
                else:
                    log.info("Create incremental backup for volume" \
                            f" {res['id']} by plan {plan['id']}.")
                    params["volume_id"] = res["id"]
                    await self.add_volume_backup(params)
                    continue
                log.info("Update incredmental backup for volume" \
                        f" {res['id']} by plan {plan['id']}.")
                await self.update_volume_backup(backup["id"])
        else:
            return

    async def get_instance_backup(self):
        log.info("Get instance backup.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/instance/backup"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("get", url, headers)
        if resp["status"] == 200:
            return resp["data"]["backups"]
        else:
            log.error("Get instance backup failed!")

    async def add_instance_backup(self, params):
        log.info(f"Create backup on instance {params['instance_id']}.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/instance/backup"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("post", url, headers, {"backup": params})

    async def update_instance_backup(self, id):
        log.info(f"Update instance backup {id}.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/instance/backup/{id}/action"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("post", url, headers, {"update": {}})

    async def get_volume_backup(self):
        log.info("Get volume backup.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/volume/backup"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("get", url, headers)
        if resp["status"] == 200:
            return resp["data"]["backups"]
        else:
            log.error("Get volume backup failed!")

    async def add_volume_backup(self, params):
        log.info(f"Create backup on volume {params['volume_id']}.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/volume/backup"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("post", url, headers, {"backup": params})
        log.debug(f"resp: {resp['status']} {resp['data']}")

    async def update_volume_backup(self, id):
        log.info(f"Update volume backup {id}.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/volume/backup/{id}/action"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("post", url, headers, {"update": {}})

