import asyncio
import logging
from fastapi import FastAPI, Header

from common import util, config
from common.route_wrapper import route_wrapper
from openstack.keystone import Auth
from db import db
from plan import PostAction, PlanResourcePost
from backup_plan import BackupPlan, BackupPlanPost
from snapshot_plan import SnapshotPlan, SnapshotPlanPost

log = logging.getLogger("uvicorn")
app = FastAPI()


@app.on_event("startup")
async def api_start():
    log.info("Start server.")
    await db.create_engine()
    rc = -1
    while rc:
        rc = await db.check_table()
        if rc:
            log.error(f"Failed to check DB! Retry.")
            await asyncio.sleep(10)
    log.info("Checked DB.")
    auth_ins = Auth()
    while not config.svc_token_pack:
        config.svc_token_pack = await auth_ins.get_svc_token(config.zone_conf)
        if not config.svc_token_pack:
            log.error(f"Failed to service token! Retry.")
            await asyncio.sleep(10)
    log.info("Got service token.")


@app.on_event("shutdown")
async def api_shutdown():
    log.info("Shutdown server.")


@app.get("/")
async def get_root():
    return {"message": util.msg_root}


'''
Backup Plan
'''


@app.get("/v1/backup-plan")
@route_wrapper
async def get_backup_plans(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await BackupPlan(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/backup-plan/{id}")
@route_wrapper
async def get_backup_plan(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_get(id)


@app.post("/v1/backup-plan")
@route_wrapper
async def post_backup_plan(req: BackupPlanPost,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_post(req.model_dump())


@app.post("/v1/backup-plan/{id}/action")
@route_wrapper
async def post_backup_plan_action(id: str,
        req: PostAction,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_post_action(id, req.model_dump())


@app.delete("/v1/backup-plan/{id}")
@route_wrapper
async def delete_backup_plan(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_delete(id)


@app.get("/v1/backup-plan/{id}/resource")
@route_wrapper
async def get_backup_plan_resources(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_get_res_list(id)


@app.post("/v1/backup-plan/{id}/resource")
@route_wrapper
async def post_backup_plan_resource(id: str,
        req: PlanResourcePost,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_post_res(id, req.model_dump())


@app.delete("/v1/backup-plan/{id}/resource/{res_id}")
@route_wrapper
async def delete_backup_plan_resource(id: str, res_id: str,
        x_auth_token=Header(None), token_pack=None):
    return await BackupPlan(token_pack).rh_delete_res(id, res_id)


'''
Snapshot Plan
'''


@app.get("/v1/snapshot-plan")
@route_wrapper
async def get_snapshot_plans(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await SnapshotPlan(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/snapshot-plan/{id}")
@route_wrapper
async def get_snapshot_plan(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_get(id)


@app.post("/v1/snapshot-plan")
@route_wrapper
async def post_snapshot_plan(req: SnapshotPlanPost,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_post(req.model_dump())


@app.post("/v1/snapshot-plan/{id}/action")
@route_wrapper
async def post_snapshot_plan_action(id: str,
        req: PostAction,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_post_action(id, req.model_dump())


@app.delete("/v1/snapshot-plan/{id}")
@route_wrapper
async def delete_snapshot_plan(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_delete(id)


@app.get("/v1/snapshot-plan/{id}/resource")
@route_wrapper
async def get_snapshot_plan_resources(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_get_res_list(id)


@app.post("/v1/snapshot-plan/{id}/resource")
@route_wrapper
async def post_snapshot_plan_resource(id: str,
        req: PlanResourcePost,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_post_res(id, req.model_dump())


@app.delete("/v1/snapshot-plan/{id}/resource/{res_id}")
@route_wrapper
async def delete_snapshot_plan_resource(id: str, res_id: str,
        x_auth_token=Header(None), token_pack=None):
    return await SnapshotPlan(token_pack).rh_delete_res(id, res_id)

