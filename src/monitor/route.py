"""
The route of monitor service.
"""
import asyncio
import logging
from fastapi import FastAPI, Header

from openstack.keystone import Auth
from common.route_wrapper import route_wrapper
from common import util, config
from db import db
from monitor.cluster import MonitorCluster
from monitor.objects import MonitorClusterPost, MonitorClusterPut,\
    MonitorClusterAction

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
Monitor Service
'''


@app.get("/v1/monitor/cluster/{cluster_id}")
@route_wrapper
async def get_monitor_cluster(cluster_id: str, token_pack=None,
        x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_get(cluster_id)


@app.get("/v1/monitor/cluster")
@route_wrapper
async def get_monitor_cluster_list(name: str = None, projects: str = None,
        token_pack=None, x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_get_list(
        query={"name": name, "project": projects})


@app.post("/v1/monitor/cluster")
@route_wrapper
async def post_monitor_cluster(req: MonitorClusterPost, token_pack=None,
        x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_post(req.model_dump())


@app.put("/v1/monitor/cluster/{cluster_id}")
@route_wrapper
async def put_monitor_cluster(cluster_id: str, req: MonitorClusterPut,
        token_pack=None, x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_put(cluster_id,
        req.model_dump())


@app.delete("/v1/monitor/cluster/{cluster_id}")
@route_wrapper
async def delete_monitor_cluster(cluster_id: str, force: bool = False,
        token_pack=None, x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_delete(cluster_id, force)


@app.post("/v1/monitor/cluster/{cluster_id}/action")
@route_wrapper
async def post_monitor_cluster_action(cluster_id: str,
        req: MonitorClusterAction,
        token_pack=None, x_auth_token=Header(None)):
    return await MonitorCluster(token_pack).rh_post_action(cluster_id,
        req.model_dump())

