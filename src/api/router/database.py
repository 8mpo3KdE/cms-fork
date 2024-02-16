from fastapi import APIRouter
from fastapi.requests import Request

import api

router_db = APIRouter(prefix="/v1/database", tags=["database"])


''' 
MariaDB
'''

@router_db.get("/mariadb")
async def get_maria_list(req: Request):
    fwd_path = "/mariadb"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/mariadb/version")
async def get_mariadb_version(req: Request):
    fwd_path = f"/mariadb/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/mariadb/{id}")
async def get_mariadb(req: Request, id: str):
    fwd_path = f"/mariadb/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/mariadb/{id}/instance")
async def get_mariadb_instance(req: Request, id: str):
    fwd_path = f"/mariadb/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.post("/mariadb")
async def post_mariadb(req: Request):
    fwd_path = "/mariadb"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_db.put("/mariadb/{id}")
async def put_mariadb(req: Request, id: str):
    fwd_path = f"/mariadb/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_db.delete("/mariadb/{id}")
async def delete_mariadb(req: Request, id: str):
    fwd_path = f"/mariadb/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_db.post("/mariadb/{id}/action")
async def post_mariadb_action(req: Request, id: str):
    fwd_path = f"/mariadb/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


''' 
PostgresSQL
'''

@router_db.get("/postgresql")
async def get_postgresql_list(req: Request):
    fwd_path = "/postgresql"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/postgresql/version")
async def get_postgresql_version(req: Request):
    fwd_path = f"/postgresql/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/postgresql/{id}")
async def get_postgresql(req: Request, id: str):
    fwd_path = f"/postgresql/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/postgresql/{id}/instance")
async def get_postgresql_instance(req: Request, id: str):
    fwd_path = f"/postgresql/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.post("/postgresql")
async def post_postgresql(req: Request):
    fwd_path = "/postgresql"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_db.put("/postgresql/{id}")
async def put_postgresql(req: Request, id: str):
    fwd_path = f"/postgresql/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_db.delete("/postgresql/{id}")
async def delete_postgresql(req: Request, id: str):
    fwd_path = f"/postgresql/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_db.post("/postgresql/{id}/action")
async def post_postgresql_action(req: Request, id: str):
    fwd_path = f"/postgresql/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


'''
Redis
'''

@router_db.get("/redis")
async def get_redis_list(req: Request):
    fwd_path = "/redis"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/redis/version")
async def get_redis_version(req: Request):
    fwd_path = f"/redis/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/redis/{id}")
async def get_redis(req: Request, id: str):
    fwd_path = f"/redis/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.get("/redis/{id}/instance")
async def get_redis_instance(req: Request, id: str):
    fwd_path = f"/redis/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_db.post("/redis")
async def post_redis(req: Request):
    fwd_path = "/redis"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_db.put("/redis/{id}")
async def put_redis(req: Request, id: str):
    fwd_path = f"/redis/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_db.delete("/redis/{id}")
async def delete_redis(req: Request, id: str):
    fwd_path = f"/redis/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_db.post("/redis/{id}/action")
async def post_redis_action(req: Request, id: str):
    fwd_path = f"/redis/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)

