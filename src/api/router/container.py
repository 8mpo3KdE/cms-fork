from fastapi import APIRouter
from fastapi.requests import Request

import api

router_container = APIRouter(prefix="/v1/container", tags=["container"])

'''
kubernetes
'''

@router_container.get("/kubernetes")
async def get_kubernetess(req: Request):
    fwd_path = "/kubernetes"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/kubernetes/version")
async def get_kubernetes_version(req: Request):
    fwd_path = f"/kubernetes/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/kubernetes/{id}")
async def get_kubernetes(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/kubernetes/{id}/config")
async def get_kubernetes_config(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}/config"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.post("/kubernetes")
async def post_kubernetes(req: Request):
    fwd_path = "/kubernetes"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_container.put("/kubernetes/{id}")
async def put_kubernetes(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_container.delete("/kubernetes/{id}")
async def delete_kubernetes(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_container.get("/kubernetes/{id}/worker")
async def get_kubernetes_worker(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}/worker"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.post("/kubernetes/{id}/worker")
async def post_kubernetes_worker(req: Request, id: str):
    fwd_path = f"/kubernetes/{id}/worker"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


'''
Harbor
'''

@router_container.get("/harbor")
async def get_harbor_list(req: Request):
    fwd_path = "/harbor"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/harbor/version")
async def get_harbor_version(req: Request):
    fwd_path = "/harbor/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/harbor/{id}")
async def get_harbor(req: Request, id: str):
    fwd_path = f"/harbor/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.get("/harbor/{id}/instance")
async def get_harbor_instance(req: Request, id: str):
    fwd_path = f"/harbor/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_container.post("/harbor")
async def post_harbor(req: Request):
    fwd_path = "/harbor"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_container.put("/harbor/{id}")
async def put_harbor(req: Request, id: str):
    fwd_path = f"/harbor/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_container.delete("/harbor/{id}")
async def delete_harbor(req: Request, id: str):
    fwd_path = f"/harbor/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_container.post("/harbor/{id}/action")
async def post_harbor_action(req: Request, id: str):
    fwd_path = f"/harbor/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)

