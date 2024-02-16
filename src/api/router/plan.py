from fastapi import APIRouter
from fastapi.requests import Request

import api

router_plan = APIRouter(prefix="/v1/plan", tags=["plan"])


# backup-plan
@router_plan.get("/backup-plan")
async def get_backup_plans(req: Request):
    fwd_path = "/backup-plan"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.get("/backup-plan/{id}")
async def get_backup_plan(req: Request, id: str):
    fwd_path = f"/backup-plan/{id}"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.post("/backup-plan")
async def post_backup_plan(req: Request):
    fwd_path = "/backup-plan"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.post("/backup-plan/{id}/action")
async def post_backup_plan_action(req: Request, id: str):
    fwd_path = f"/backup-plan/{id}/action"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.delete("/backup-plan/{id}")
async def delete_backup_plan(req: Request, id: str):
    fwd_path = f"/backup-plan/{id}"
    return await api.op_api(req, "delete", "cms-plan", fwd_path)


@router_plan.get("/backup-plan/{id}/resource")
async def get_backup_plan_resource(req: Request, id: str):
    fwd_path = f"/backup-plan/{id}/resource"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.post("/backup-plan/{id}/resource")
async def post_backup_plan_resource(req: Request, id: str):
    fwd_path = f"/backup-plan/{id}/resource"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.delete("/backup-plan/{id}/resource/{res_id}")
async def delete_backup_plan_resource(req: Request, id: str, res_id: str):
    fwd_path = f"/backup-plan/{id}/resource/{res_id}"
    return await api.op_api(req, "delete", "cms-plan", fwd_path)


# snapshot plan
@router_plan.get("/snapshot-plan")
async def get_snapshot_plans(req: Request):
    fwd_path = "/snapshot-plan"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.get("/snapshot-plan/{id}")
async def get_snapshot_plan(req: Request, id: str):
    fwd_path = f"/snapshot-plan/{id}"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.post("/snapshot-plan")
async def post_snapshot_plan(req: Request):
    fwd_path = "/snapshot-plan"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.post("/snapshot-plan/{id}/action")
async def post_snapshot_plan_action(req: Request, id: str):
    fwd_path = f"/snapshot-plan/{id}/action"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.delete("/snapshot-plan/{id}")
async def delete_snapshot_plan(req: Request, id: str):
    fwd_path = f"/snapshot-plan/{id}"
    return await api.op_api(req, "delete", "cms-plan", fwd_path)


@router_plan.get("/snapshot-plan/{id}/resource")
async def get_snapshot_plan_resource(req: Request, id: str):
    fwd_path = f"/snapshot-plan/{id}/resource"
    return await api.op_api(req, "get", "cms-plan", fwd_path)


@router_plan.post("/snapshot-plan/{id}/resource")
async def post_snapshot_plan_resource(req: Request, id: str):
    fwd_path = f"/snapshot-plan/{id}/resource"
    return await api.op_api(req, "post", "cms-plan", fwd_path)


@router_plan.delete("/snapshot-plan/{id}/resource/{res_id}")
async def delete_snapshot_plan_resource(req: Request, id: str, res_id: str):
    fwd_path = f"/snapshot-plan/{id}/resource/{res_id}"
    return await api.op_api(req, "delete", "cms-plan", fwd_path)

