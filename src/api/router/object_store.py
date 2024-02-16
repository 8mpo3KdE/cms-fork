from fastapi import APIRouter
from fastapi.requests import Request

import api

router_object_store = APIRouter(prefix="/v1/object-store",
                                tags=["object-store"])


@router_object_store.post("/share/key")
async def post_share_key(req: Request):
    fwd_path = ""
    return await api.op_api(req, "post", "object-store", fwd_path)


@router_object_store.post("/share")
async def get_share(req: Request):
    fwd_path = ""
    return await api.get_obj_url(req)

