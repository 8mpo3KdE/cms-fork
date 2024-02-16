import logging
from fastapi import FastAPI, WebSocket
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

import api
from common import config
from openstack.keystone import Auth

from router.message_queue import router_msg_q
from router.object_store import router_object_store	
from router.cloudshell import router_cloudshell
from router.container import router_container
from router.identity import router_identity
from router.network import router_network
from router.compute import router_compute 
from router.builder import router_builder
from router.monitor import router_monitor
from router.database import router_db 
from router.image import router_image 
from router.block import router_block 
from router.plan import router_plan 

log = logging.getLogger("uvicorn")
app = FastAPI()

app.include_router(router_object_store)	
app.include_router(router_container)
app.include_router(router_cloudshell)
app.include_router(router_identity)
app.include_router(router_network)
app.include_router(router_compute)
app.include_router(router_builder)
app.include_router(router_monitor)
app.include_router(router_image)
app.include_router(router_block)
app.include_router(router_msg_q)
app.include_router(router_plan)
app.include_router(router_db)


@app.on_event("startup")
async def api_start():
    log.info("Start server.")
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


@app.get("/health")
async def get_health():
    return api.get_health()


@app.get("/config")
async def get_config():
    return api.get_config()


# cloudshell
@app.websocket("/v1/cloudshell/connect/{port}")
async def ws_connect_port(ws: WebSocket, port: str, id: str):
    fwd_path = f"/cloudshell/connect/{port}?id={id}"
    return await api.websocket_bridge(ws, fwd_path)


app.mount("/v1/cloudshell/static", 
    StaticFiles(directory="../cloudshell/static", html=True), name="static")


@app.get("/{path_name:path}")
async def get_all(req: Request):
    return api.get_portal(req.url.path)

