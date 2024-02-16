import asyncio
import logging
from enum import Enum
from pydantic import BaseModel
from common import util
from common import validator
from db import db
from plan import PlanBase
from openstack.cinder import Snapshot as VolumeSnapshot

log = logging.getLogger("uvicorn")


class ResourceType(str, Enum):
    instance = "instance"
    volume = "volume"


class SnapshotPlanObject(BaseModel):
    name: str
    resource_type: ResourceType
    schedule: str
    retention: int
    credential_name: str
    credential_secret: str


class SnapshotPlanPost(BaseModel):
    snapshot_plan: SnapshotPlanObject


class SnapshotPlan(PlanBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="snapshot_plan")

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
                "project_id": self.project_id,
                "resource_type": req["resource_type"],
                "schedule": req["schedule"],
                "retention": req["retention"],
                "status": "active"}
        await db.add(self.res_name, row)
        task = asyncio.create_task(self.task_add_plan(row, req))
        task.add_done_callback(util.task_done_cb)
        return {"status": 201, "data": {self.res_name: {"id": row["id"]}}}

    async def task_execute_plan(self, plan):
        rt = plan["resource_type"]
        log.info(f"Task execute {rt} snapshot plan {plan['id']}.")
        ress = await self.get_ress(plan)
        if not ress:
            return
        if rt == "instance":
            params = {"name": f"plan-{plan['id']}",
                    "plan_id": plan["id"],
                    "retention": plan["retention"]}
            for res in ress:
                params["instance_id"] = res["id"]
                await self.add_instance_snapshot(params)
        elif rt == "volume":
            res_ins = VolumeSnapshot(self.token_pack)
            params = {"name": f"plan-{plan['id']}",
                    "force": True,
                    "plan_id": plan["id"],
                    "retention": plan["retention"]}
            for res in ress:
                log.info(f"Create snapshot on volume {res['id']}")
                params["volume_id"] = res["id"]
                resp = await res_ins.post({"snapshot": params})
        else:
            return
        log.info(f"Task execute snapshot plan is done.")

    async def add_instance_snapshot(self, params):
        log.info(f"Create snapshot on instance {params['instance_id']}.")
        svc_url = util.get_svc_url(self.token_pack["catalog"], "cms-backup")
        url = f"{svc_url}/instance/snapshot"
        headers = {"content-type": "application/json",
                "x-auth-token": self.token}
        resp = await util.send_req("post", url, headers, {"snapshot": params})

