import asyncio
import logging
from fastapi import FastAPI, Header, WebSocket
from fastapi.staticfiles import StaticFiles

from common import util, config
from common.route_wrapper import route_wrapper
from openstack.keystone import Auth
from cloudshell import CloudShell
from cloudshell import preflight_check, load_exists_ports

log = logging.getLogger("uvicorn")
app = FastAPI()


@app.on_event("startup")
async def api_start():
    log.info("Start server.")
    preflight_check()
    await load_exists_ports()
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


@app.post("/v1/cloudshell/start")
@route_wrapper
async def start_session(
        x_auth_token=Header(None),
        token_pack=None):
    return await CloudShell(token_pack).start_session()


@app.websocket("/v1/cloudshell/connect/{port}")
async def ws_connect(
        websocket: WebSocket,
        port: str):
    return await CloudShell().ws_connect(websocket, port)

app.mount("/static", StaticFiles(directory="static", html=True),
        name="static")

