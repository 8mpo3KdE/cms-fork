from fastapi import APIRouter
from fastapi.requests import Request

import api

router_block = APIRouter(prefix="/v1/block", tags=["block"])


# quota
@router_block.get("/limit")
async def get_block_limit(req: Request):
    fwd_path = "/limits"
    return await api.op_api(req, "get", "volumev3", fwd_path)

@router_block.get("/quota-set/{id}")
async def get_block_quota_sets(req: Request, id: str):
    fwd_path = f"/os-quota-sets/{id}"
    return await api.op_api(req, "get", "volumev3", fwd_path)

@router_block.put("/quota-set/{id}")
async def put_block_quota_set(req: Request, id: str):
    fwd_path = f"/os-quota-sets/{id}"
    return await api.op_api(req, "put", "volumev3", fwd_path)

# block:type
@router_block.get("/type")
async def get_block_types(req: Request):
    fwd_path = "/types"
    return await api.op_api(req, "get", "volumev3", fwd_path)


# block:volume
@router_block.get("/volume")
async def get_block_volumes(req: Request):
    fwd_path = "/volumes"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.get("/volume/detail")
async def get_block_volumes_detail(req: Request):
    fwd_path = "/volumes/detail"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.get("/volume/{id}")
async def get_block_volume(req: Request, id: str):
    fwd_path = f"/volumes/{id}"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.post("/volume")
async def post_block_volume(req: Request):
    fwd_path = "/volumes"
    return await api.op_api(req, "post", "volumev3", fwd_path)


@router_block.post("/volume/{id}/action")
async def post_block_volume_action(req: Request, id: str):
    fwd_path = f"/volumes/{id}/action"
    return await api.op_api(req, "post", "volumev3", fwd_path)


@router_block.put("/volume/{id}")
async def put_block_volume(req: Request, id: str):
    fwd_path = f"/volumes/{id}"
    return await api.op_api(req, "put", "volumev3", fwd_path)


@router_block.delete("/volume/{id}")
async def delete_block_volume(req: Request, id: str):
    fwd_path = f"/volumes/{id}"
    return await api.op_api(req, "delete", "volumev3", fwd_path)


@router_block.get("/volume/{id}/metadata")
async def get_block_volume_metadata(req: Request, id: str):
    fwd_path = f"/volumes/{id}/metadata"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.put("/volume/{id}/metadata")
async def put_block_volume_metadata(req: Request, id: str):
    fwd_path = f"/volumes/{id}/metadata"
    return await api.op_api(req, "put", "volumev3", fwd_path)


@router_block.get("/volume/{id}/metadata/{key}")
async def get_block_volume_metadata_key(req: Request, id: str, key: str):
    fwd_path = f"/volumes/{id}/metadata/{key}"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.put("/volume/{id}/metadata/{key}")
async def put_block_volume_metadata_key(req: Request, id: str, key: str):
    fwd_path = f"/volumes/{id}/metadata/{key}"
    return await api.op_api(req, "put", "volumev3", fwd_path)


@router_block.delete("/volume/{id}/metadata/{key}")
async def delete_block_volume_metadata_key(req: Request, id: str, key: str):
    fwd_path = f"/volumes/{id}/metadata/{key}"
    return await api.op_api(req, "delete", "volumev3", fwd_path)


# volmue:backup
@router_block.get("/backup")
async def get_block_backups(req: Request):
    fwd_path = "/volume/backup"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_block.post("/backup")
async def post_block_backup(req: Request):
    fwd_path = "/volume/backup"
    return await api.op_api(req, "post", "cms-backup", fwd_path)


@router_block.put("/backup/{id}")
async def put_block_backup(req: Request, id: str):
    fwd_path = f"/volume/backup/{id}"
    return await api.op_api(req, "put", "cms-backup", fwd_path)


@router_block.delete("/backup/{id}")
async def delete_block_backup(req: Request, id: str):
    fwd_path = f"/volume/backup/{id}"
    return await api.op_api(req, "delete", "cms-backup", fwd_path)


@router_block.get("/backup/{id}")
async def get_block_backup(req: Request, id: str):
    fwd_path = f"/volume/backup/{id}"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_block.post("/backup/{id}/action")
async def post_block_backup_action(req: Request, id: str):
    fwd_path = f"/volume/backup/{id}/action"
    return await api.op_api(req, "post", "cms-backup", fwd_path)


@router_block.get("/backup/{id}/snapshot")
async def get_block_backup_snapshot(req: Request, id: str):
    fwd_path = f"/volume/backup/{id}/snapshot"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


# volume:snapshot
@router_block.get("/snapshot")
async def get_block_snapshots(req: Request):
    fwd_path = "/snapshots"
    return await api.op_api(req, "get", "volumev3", fwd_path)


@router_block.post("/snapshot")
async def post_block_snapshot(req: Request):
    fwd_path = "/snapshots"
    return await api.op_api(req, "post", "volumev3", fwd_path)


@router_block.put("/snapshot/{id}")
async def put_block_snapshot(req: Request, id: str):
    fwd_path = f"/snapshots/{id}"
    return await api.op_api(req, "put", "volumev3", fwd_path)


@router_block.delete("/snapshot/{id}")
async def delete_block_snapshot(req: Request, id: str):
    fwd_path = f"/snapshots/{id}"
    return await api.op_api(req, "delete", "volumev3", fwd_path)


@router_block.get("/snapshot/{id}")
async def get_block_snapshot(req: Request, id: str):
    fwd_path = f"/snapshots/{id}"
    return await api.op_api(req, "get", "volumev3", fwd_path)

