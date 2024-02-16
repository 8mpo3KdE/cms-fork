import asyncio
import logging

from common import util
from db import db
from common.config import zone_conf
from openstack.keystone import Auth, ApplicationCredential
from openstack.nova import Instance

log = logging.getLogger("uvicorn")


class ResourceBase(object):
    def __init__(self, token_pack, res_name, table_name=None):
        self.res_name = res_name
        self.table_name = res_name
        if table_name:
            self.table_name = table_name
        self.token_pack = token_pack
        self.token = token_pack["token"]
        self.project_id = token_pack["project"]["id"]
        self.role_admin = False
        self.action_map = None
        for role in token_pack["roles"]:
            if role["name"] == "admin":
                self.role_admin = True
                break

    async def get_obj_list(self, query=None):
        if query is None:
            query = {}
        util.pop_none(query)
        query["deleted"] = False
        query["project_id"] = self.project_id
        if "all_projects" in query:
            query.pop("all_projects")
            if self.role_admin:
                query.pop("project_id")
        objs = await db.get(self.table_name, query)
        return objs

    async def get_obj(self, id):
        q = {"id": id}
        if self.role_admin:
            q["all_projects"] = True
        objs = await self.get_obj_list(query=q)
        if objs:
            return objs[0]

    async def rh_get_list(self, query=None):
        objs = await self.get_obj_list(query)
        return {"status": 200, "data": {self.res_name + "s": objs}}

    async def rh_get(self, id):
        obj = await self.get_obj(id)
        if obj:
            return {"status": 200, "data": {self.res_name: obj}}
        else:
            return {"status": 404}

    async def rh_post_action(self, id, req):
        action = list(req)[0]
        if action not in self.action_map:
            msg = f"Invalid action {action}!"
            return {"status": 405, "data": msg}
        return await self.action_map[action](id, req[action])

    async def validate_credential(self, name, secret):
        res_ins = ApplicationCredential(self.token_pack)
        objs = await res_ins.get_obj_list({"name": name})
        if not objs:
            return {"msg": "Invalid credential name.", "id": None}
        for obj in objs:
            log.debug(f"Check credential {obj}")
            if obj["project_id"] == self.project_id:
                break
        else:
            return {"msg": "Invalid credential name.", "id": None}
        auth_data = {"type": "application_credential",
                     "credential_name": name,
                     "credential_secret": secret,
                     "user": self.token_pack["user"]["id"],
                     "auth_url": zone_conf["auth-url"]}
        token_pack = await Auth().get_user_token(auth_data)
        if not token_pack:
            return {"msg": "Invalid credential secret.", "id": None}
        return {"msg": None, "id": obj["id"]}

    async def wait_for_batch_ready(self, res_ins, query, status, count=10):
        while count > 0:
            await asyncio.sleep(3)
            objs = await res_ins.get_obj_list(query=query)
            res_ready = 0
            for obj in objs:
                if obj["status"] == status:
                    res_ready = res_ready + 1
            if res_ready == len(objs):
                return {"status": 200, "data": objs}
            count -= 1
        else:
            log.error(f"Wait for batch {res_ins} {status} timeout!")

    async def wait_for_ready(self, res_ins, res_ids, status, count=10,
            interval=3):
        if not res_ids:
            return
        await asyncio.sleep(interval)
        for id in res_ids:
            c = count
            while c:
                obj = await res_ins.get_obj(id)
                if obj:
                    log.debug(f"Wait {id} status is {obj['status']}.")
                    if obj["status"] == status:
                        break
                else:
                    if status == "DELETED":
                        log.debug(f"Wait {id} status is {status}.")
                        break
                    else:
                        log.error(f"Wait {id} is not found!")
                        return -1
                c -= 1
                await asyncio.sleep(interval)
            else:
                log.error(f"Wait {id} {status} timeout!")
                return -1

    async def wait_for_login(self, res_ids, count=40, interval=3):
        if not res_ids:
            return
        await asyncio.sleep(interval)
        res_ins = Instance(self.token_pack)
        for id in res_ids:
            c = count
            while c:
                params = {"os-getConsoleOutput": {"length": 1}}
                resp = await res_ins.action(id, params)
                log.debug(f"Wait {id} output: {resp['data']}")
                if "login" in resp["data"]["output"]:
                    break
                c -= 1
                await asyncio.sleep(interval)
            else:
                log.error(f"Wait {id} login timeout!")
                return -1

