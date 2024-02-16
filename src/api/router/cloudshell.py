import logging
from fastapi import APIRouter
from fastapi.requests import Request

import api

log = logging.getLogger("uvicorn")

router_cloudshell = APIRouter(prefix="/v1/cloudshell", tags=["cloudshell"])


@router_cloudshell.post("/start")
async def post_cloudshell(req: Request):
    fwd_path = "/cloudshell/start"
    return await api.op_api(req, "post", "cms-cloudshell", fwd_path)


# the connect route is located at ../route.py 
# websocket doesn't work with APIRouter.

