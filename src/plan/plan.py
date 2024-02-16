import os
import asyncio
import logging
from typing import Union
from pydantic import BaseModel, RootModel
from common.config import config
from common import util
from common.resource_base import ResourceBase
from db import db
from openstack.nova import Instance
from openstack.cinder import Volume

log = logging.getLogger("uvicorn")


class PlanResourceVolume(BaseModel):
    volume_ids: list


class PlanResourceInstance(BaseModel):
    instance_ids: list


class PlanResourcePost(BaseModel):
    resource: Union[PlanResourceVolume, PlanResourceInstance]


class ActionExecute(BaseModel):
    execute: dict


class ActionStop(BaseModel):
    stop: dict


class ActionStart(BaseModel):
    start: dict


class PostAction(RootModel):
    root: Union[ActionExecute, ActionStop, ActionStart]


class PlanBase(ResourceBase):
    def __init__(self, token_pack, res_name):
        super().__init__(token_pack, res_name=res_name)
        self.action_map = {"execute": self.action_execute,
                "stop": self.action_stop,
                "start": self.action_start}

    async def rh_delete(self, id):
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        update = {"status": "deleting"}
        await db.update(self.table_name, plan["id"], update)
        task = asyncio.create_task(self.task_delete_plan(plan))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def action_execute(self, id, args):
        log.info(f"Action execute plan {id}.")
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        task = asyncio.create_task(self.task_execute_plan(plan))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def action_stop(self, id, args):
        log.info(f"Action stop plan {id}.")
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        if plan["status"] == "stopped":
            return {"status": 200, "data": {self.res_name: {"id": id}}}
        with open("/var/spool/cron/root", "r") as src:
            with open("/tmp/cron.file", "w") as dst:
                for line in src:
                    if id in line:
                        line = "#" + line
                    dst.write(line)
        await util.exec_cmd(f"crontab /tmp/cron.file")
        await db.update(self.table_name, id, {"status": "stopped"})
        return {"status": 200, "data": {self.res_name: {"id": id}}}

    async def action_start(self, id, args):
        log.info(f"Action start plan {id}.")
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        if plan["status"] == "active":
            return {"status": 200, "data": {self.res_name: {"id": id}}}
        with open("/var/spool/cron/root", "r") as src:
            with open("/tmp/cron.file", "w") as dst:
                for line in src:
                    if id in line:
                        line = line.strip("#")
                    dst.write(line)
        await util.exec_cmd(f"crontab /tmp/cron.file")
        await db.update(self.table_name, id, {"status": "active"})
        return {"status": 200, "data": {self.res_name: {"id": id}}}

    async def rh_get_res_list(self, id):
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        objs = await self.get_ress(plan)
        data = {"resource": {plan["resource_type"] + "s": objs}}
        return {"status": 200, "data": data}

    async def get_ress(self, plan):
        rt = plan["resource_type"]
        log.info(f"Get {rt} list for plan {plan['id']}.")
        query = {}
        if self.role_admin:
            query = {"all_tenants": "true", "project_id": plan["project_id"]}
        if rt == "volume":
            objs = await Volume(self.token_pack).get_obj_list(query)
        elif rt == "instance":
            objs = await Instance(self.token_pack).get_obj_list(query)
        else:
            return
        ress = []
        for obj in objs:
            if f"plan-{plan['id']}" in obj["metadata"]:
                ress.append(obj)
        return ress

    async def rh_post_res(self, id, req_data):
        req = req_data["resource"]
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        data = {"metadata": {f"plan-{id}": "true"}}
        if "volume_ids" in req:
            vol_ins = Volume(self.token_pack)
            for res_id in req["volume_ids"]:
                log.info(f"Add volume {res_id} to plan {id}.")
                resp = await vol_ins.add_metadata(res_id, data)
                if resp["status"] != 200:
                    log.error(f"resp: {resp['status']} {resp['data']}")
        if "instance_ids" in req:
            ins_ins = Instance(self.token_pack)
            for res_id in req["instance_ids"]:
                log.info(f"Add instance {res_id} to plan {id}.")
                resp = await ins_ins.add_metadata(res_id, data)
                if resp["status"] != 200:
                    log.error(f"resp: {resp['status']} {resp['data']}")
        return {"status": 200}

    async def rh_delete_res(self, id, res_id):
        log.info(f"Remove tag plan-{id} from resource {res_id}.")
        plan = await self.get_obj(id)
        if not plan:
            return {"status": 404}
        await self.remove_res(plan, res_id)
        return {"status": 200}

    async def remove_res(self, plan, res_id):
        tag = f"plan-{plan['id']}"
        if plan["resource_type"] == "instance":
            log.info(f"Untag {tag} from instance {res_id}.")
            await Instance(self.token_pack).remove_metadata(res_id, tag)
        elif plan["resource_type"] == "volume":
            log.info(f"Untag {tag} from volume {res_id}.")
            await Volume(self.token_pack).remove_metadata(res_id, tag)

    async def task_add_plan(self, plan, req):
        log.info(f"Task add_plan.")
        plan_type = self.res_name.replace("_", "-")
        if os.path.exists("/var/spool/cron/root"):
            await util.exec_cmd(f"cp /var/spool/cron/root /tmp/cron.file")
        zone_conf = config["zone." + config["DEFAULT"]["zone"]]
        cms_path = os.getcwd().replace("/plan", "")
        with open("/tmp/cron.file", "a") as f:
            args = f"--cms-username {self.token_pack['user']['name']}" \
                    f" --cms-credential-name {req['credential_name']}" \
                    f" --cms-credential-secret {req['credential_secret']}" \
                    f" --cms-auth-method credential" \
                    f" --cms-auth-url \"{zone_conf['auth-url']}\""
            line = f"{plan['schedule']}  export PYTHONPATH={cms_path};" \
                    f" {cms_path}/client/cms {args}" \
                    f" {plan_type} execute {plan['id']}\n"
            f.write(line)
        await util.exec_cmd(f"crontab /tmp/cron.file")
        log.info(f"Task add_plan is done.")

    async def task_delete_plan(self, plan):
        id = plan["id"]
        log.info(f"Task delete_plan {id}.")
        log.info(f"Remove resources from plan {id}.")
        ress = await self.get_ress(plan)
        for res in ress:
            await self.remove_res(plan, res["id"])
        log.info(f"Remove plan {id} from crontab.")
        if os.path.exists("/var/spool/cron/root"):
            await util.exec_cmd(f"cp /var/spool/cron/root /tmp/cron.file")
        await util.exec_cmd(f"sed -i \"/{id}/d\" /tmp/cron.file")
        await util.exec_cmd(f"crontab /tmp/cron.file")
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, id, update)
        log.info(f"Task delete_plan is done.")

