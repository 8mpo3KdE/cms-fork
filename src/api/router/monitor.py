from fastapi import APIRouter
from fastapi.requests import Request

import api

router_monitor = APIRouter(prefix="/v1/monitor", tags=["monitor"])


# monitor: cluster
@router_monitor.get("/cluster")
async def get_monitor_clusters(req: Request):
    fwd_path = "/monitor/cluster"
    return await api.op_api(req, "get", "cms-monitor", fwd_path)


@router_monitor.get("/cluster/{id}")
async def get_monitor_cluster(req: Request, id: str):
    fwd_path = f"/monitor/cluster/{id}"
    return await api.op_api(req, "get", "cms-monitor", fwd_path)


@router_monitor.delete("/cluster/{id}")
async def delete_monitor_cluster(req: Request, id: str):
    fwd_path = f"/monitor/cluster/{id}"
    return await api.op_api(req, "delete", "cms-monitor", fwd_path)


@router_monitor.post("/cluster")
async def post_monitor_cluster(req: Request):
    fwd_path = "/monitor/cluster"
    return await api.op_api(req, "post", "cms-monitor", fwd_path)


@router_monitor.put("/cluster/{id}")
async def put_monitor_cluster(req: Request, id: str):
    fwd_path = f"/monitor/cluster/{id}"
    return await api.op_api(req, "put", "cms-monitor", fwd_path)


@router_monitor.post("/cluster/{id}/action")
async def post_monitor_cluster_action(req: Request, id: str):
    fwd_path = f"/monitor/cluster/{id}/action"
    return await api.op_api(req, "post", "cms-monitor", fwd_path)

