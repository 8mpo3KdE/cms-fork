from fastapi import APIRouter
from fastapi.requests import Request

import api

router_builder = APIRouter(prefix="/v1/nfs", tags=["builder"])


# NFS cluster
@router_builder.get("")
async def get_nfss(req: Request):
    fwd_path = "/nfs"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_builder.get("/{id}")
async def get_nfs(req: Request, id: str):
    fwd_path = f"/nfs/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_builder.get("/{id}/instance")
async def get_nfs_instance(req: Request, id: str):
    fwd_path = f"/nfs/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_builder.post("")
async def post_nfs(req: Request):
    fwd_path = "/nfs"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_builder.put("/{id}")
async def put_nfs(req: Request, id: str):
    fwd_path = f"/nfs/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_builder.delete("/{id}")
async def delete_nfs(req: Request, id: str):
    fwd_path = f"/nfs/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


# NFS directory
@router_builder.get("/{id}/directory")
async def get_nfs_directories(req: Request, id: str):
    fwd_path = f"/nfs/{id}/directory"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_builder.post("/{id}/disk/{did}/directory")
async def post_nfs_directories(req: Request, id: str, did: str):
    fwd_path = f"/nfs/{id}/disk/{did}/directory"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_builder.delete("/{id}/disk/{did}/directory/{name}")
async def delete_nfs_directories(req: Request, id: str, did: str, name: str):
    fwd_path = f"/nfs/{id}/disk/{did}/directory/{name}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


# NFS disk
@router_builder.get("/{id}/disk")
async def get_nfs_disks(req: Request, id: str):
    fwd_path = f"/nfs/{id}/disk"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_builder.post("/{id}/disk")
async def post_nfs_disk(req: Request, id: str):
    fwd_path = f"/nfs/{id}/disk"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_builder.delete("/{cid}/disk/{id}")
async def delete_nfs_disk(req: Request, cid: str, id: str):
    fwd_path = f"/nfs/{cid}/disk/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_builder.post("/{cid}/disk/{id}/action")
async def post_nfs_action(req: Request, cid: str, id: str):
    fwd_path = f"/nfs/{cid}/disk/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)

