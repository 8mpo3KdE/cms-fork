import asyncio
import logging
from fastapi import FastAPI, Header

from common import util, config
from common.route_wrapper import route_wrapper
from openstack.keystone import Auth
from db import db
from image import Image
from objects import ImagePost, ImagePut, ImageAction


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


@app.get("/", response_model=dict)
async def get_root():
    return {"message": util.msg_root}


@app.get("/v1/image/quota")
@route_wrapper
async def get_image_quota(token_pack=None, x_auth_token=Header(None)):
    return await Image(token_pack).rh_get_quota()


@app.get("/v1/image")
@route_wrapper
async def get_images(
        x_auth_token=Header(None), token_pack=None,
        limit: int = 100, name: str = None):
    return await Image(token_pack).rh_get_list(
            query={"name": name, "limit": limit})


@app.get("/v1/image/{id}")
@route_wrapper
async def get_image(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Image(token_pack).rh_get(id)


@app.post("/v1/image")
@route_wrapper
async def post_image(req: ImagePost, x_auth_token=Header(None),
        token_pack=None):
    return await Image(token_pack).rh_post(req.model_dump())


@app.post("/v1/image/{id}/action")
@route_wrapper
async def post_image_action(id: str,
        req: ImageAction,
        x_auth_token=Header(None), token_pack=None):
    return await Image(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/image/{id}")
@route_wrapper
async def put_image(id: str,
        req: ImagePut,
        x_auth_token=Header(None), token_pack=None):
    return await Image(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/image/{id}")
@route_wrapper
async def delete_image(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Image(token_pack).rh_delete(id)

