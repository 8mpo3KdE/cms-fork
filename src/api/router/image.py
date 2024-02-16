from fastapi import APIRouter
from fastapi.requests import Request

import api

router_image = APIRouter(prefix="/v1/image", tags=["image"])


# image: image
@router_image.get("/image")
async def get_images(req: Request):
    fwd_path = "/image"
    return await api.op_api(req, "get", "cms-image", fwd_path)


@router_image.get("/image/{id}")
async def get_image(req: Request, id: str):
    fwd_path = f"/image/{id}"
    return await api.op_api(req, "get", "cms-image", fwd_path)


@router_image.post("/image")
async def post_image(req: Request):
    fwd_path = "/image"
    return await api.op_api(req, "post", "cms-image", fwd_path)


@router_image.post("/image/{id}/action")
async def post_image_action(req: Request, id: str):
    fwd_path = f"/image/{id}/action"
    return await api.op_api(req, "post", "cms-image", fwd_path)


@router_image.put("/image/{id}")
async def post_image_action(req: Request, id: str):
    fwd_path = f"/image/{id}"
    return await api.op_api(req, "put", "cms-image", fwd_path)


@router_image.delete("/image/{id}")
async def delete_image(req: Request, id: str):
    fwd_path = f"/image/{id}"
    return await api.op_api(req, "delete", "cms-image", fwd_path)


@router_image.get("/limit")
async def get_image_limit(req: Request):
    fwd_path = f"/image/quota"
    return await api.op_api(req, "get", "cms-image", fwd_path)

