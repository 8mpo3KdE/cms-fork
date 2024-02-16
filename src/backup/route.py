import asyncio
import logging
from fastapi import FastAPI, Header
from fastapi.requests import Request

from common import util, config
from common.route_wrapper import route_wrapper
from openstack.keystone import Auth
from db import db
from volume import Volume
from volume_backup import VolumeBackup, VolumeBackupPost, \
        VolumeBackupAction, VolumeBackupPut, VolumeBackupSnapshotPost
from instance import Instance
from instance_snapshot import InstanceSnapshot, InstanceSnapshotPost
from instance_backup import InstanceBackup, InstanceBackupPost, \
        InstanceBackupAction, InstanceBackupPut

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
Volume
'''
@app.post("/v1/volume")
@route_wrapper
async def post_volume(req: Request,
        x_auth_token=Header(None), token_pack=None):
    return await Volume(token_pack).rh_post(req)


@app.post("/v1/volume/{id}/action")
@route_wrapper
async def post_volume_action(id: str, req: Request,
        x_auth_token=Header(None), token_pack=None):
    return await Volume(token_pack).rh_post_action(id, req)


'''
Instance
'''
@app.post("/v1/instance/{id}/action")
@route_wrapper
async def post_instance_action(id: str, req: Request,
        x_auth_token=Header(None), token_pack=None):
    return await Instance(token_pack).rh_post_action(id, req)


'''
Volume Backup
'''
@app.get("/v1/volume/backup")
@route_wrapper
async def get_volume_backups(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await VolumeBackup(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/volume/backup/{id}")
@route_wrapper
async def get_volume_backup(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_get(id)


@app.post("/v1/volume/backup")
@route_wrapper
async def post_volume_backup(req: VolumeBackupPost,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_post(req.model_dump())


@app.post("/v1/volume/backup/{id}/action")
@route_wrapper
async def post_volume_backup_action(id: str,
        req: VolumeBackupAction,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/volume/backup/{id}")
@route_wrapper
async def put_volume_backup(id: str,
        req: VolumeBackupPut,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/volume/backup/{id}")
@route_wrapper
async def delete_volume_backup(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_delete(id)


@app.get("/v1/volume/backup/{id}/snapshot")
@route_wrapper
async def get_volume_backup_snapshot(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_get_snapshot_list(id)


@app.post("/v1/volume/backup/{id}/snapshot")
@route_wrapper
async def post_volume_backup_snapshot(id: str,
        req: VolumeBackupSnapshotPost,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_post_snapshot(
            id, req.model_dump())


@app.delete("/v1/volume/backup/{id}/snapshot/{ss_id}")
@route_wrapper
async def delete_volume_backup_snapshot(id: str, ss_id: str,
        x_auth_token=Header(None), token_pack=None):
    return await VolumeBackup(token_pack).rh_delete_snapshot(id, ss_id)


'''
Instance
'''
#@app.post("/v1/instance/{id}/action")
#@route_wrapper
#async def post_instance_action(id:str, req: Request,
#        x_auth_token=Header(None), token_pack=None):
#    return await Instance(token_pack).post_action(id, req)


'''
Instance Snapshot
'''
@app.get("/v1/instance/snapshot")
@route_wrapper
async def get_instance_snapshots(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await InstanceSnapshot(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/instance/snapshot/{id}")
@route_wrapper
async def get_instance_snapshot(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceSnapshot(token_pack).rh_get(id)


@app.post("/v1/instance/snapshot")
@route_wrapper
async def post_instance_snapshot(req: InstanceSnapshotPost,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceSnapshot(token_pack).rh_post(req.model_dump())


@app.delete("/v1/instance/snapshot/{id}")
@route_wrapper
async def delete_instance_snapshot(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceSnapshot(token_pack).rh_delete(id)


'''
Instance Backup
'''
@app.get("/v1/instance/backup")
@route_wrapper
async def get_instance_backups(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await InstanceBackup(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/instance/backup/{id}")
@route_wrapper
async def get_instance_backup(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceBackup(token_pack).rh_get(id)


@app.post("/v1/instance/backup")
@route_wrapper
async def post_instance_backup(req: InstanceBackupPost,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceBackup(token_pack).rh_post(req.model_dump())


@app.post("/v1/instance/backup/{id}/action")
@route_wrapper
async def post_instance_backup_action(id: str,
        req: InstanceBackupAction,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceBackup(token_pack).rh_post_action(
            id, req.model_dump())


@app.put("/v1/instance/backup/{id}")
@route_wrapper
async def put_instance_backup(id: str,
        req: InstanceBackupPut,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceBackup(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/instance/backup/{id}")
@route_wrapper
async def delete_instance_backup(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await InstanceBackup(token_pack).rh_delete(id)

