from fastapi import APIRouter
from fastapi.requests import Request

import api

router_msg_q = APIRouter(prefix="/v1/message-queue", tags=["message-queue"])


''' 
RabbitMQ
'''

@router_msg_q.get("/rabbitmq")
async def get_rabbitmq_list(req: Request):
    fwd_path = "/rabbitmq"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/rabbitmq/version")
async def get_rabbitmq_version(req: Request):
    fwd_path = f"/rabbitmq/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/rabbitmq/{id}")
async def get_rabbitmq(req: Request, id: str):
    fwd_path = f"/rabbitmq/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/rabbitmq/{id}/instance")
async def get_rabbitmq_instance(req: Request, id: str):
    fwd_path = f"/rabbitmq/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.post("/rabbitmq")
async def post_rabbitmq(req: Request):
    fwd_path = "/rabbitmq"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_msg_q.put("/rabbitmq/{id}")
async def put_rabbitmq(req: Request, id: str):
    fwd_path = f"/rabbitmq/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_msg_q.delete("/rabbitmq/{id}")
async def delete_rabbitmq(req: Request, id: str):
    fwd_path = f"/rabbitmq/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_msg_q.post("/rabbitmq/{id}/action")
async def post_rabbitmq_action(req: Request, id: str):
    fwd_path = f"/rabbitmq/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


''' 
Kafka
'''

@router_msg_q.get("/kafka")
async def get_kafka_list(req: Request):
    fwd_path = "/kafka"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/kafka/version")
async def get_kafka_version(req: Request):
    fwd_path = f"/kafka/version"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/kafka/{id}")
async def get_kafka(req: Request, id: str):
    fwd_path = f"/kafka/{id}"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.get("/kafka/{id}/instance")
async def get_kafka_instance(req: Request, id: str):
    fwd_path = f"/kafka/{id}/instance"
    return await api.op_api(req, "get", "cms-builder", fwd_path)


@router_msg_q.post("/kafka")
async def post_kafka(req: Request):
    fwd_path = "/kafka"
    return await api.op_api(req, "post", "cms-builder", fwd_path)


@router_msg_q.put("/kafka/{id}")
async def put_kafka(req: Request, id: str):
    fwd_path = f"/kafka/{id}"
    return await api.op_api(req, "put", "cms-builder", fwd_path)


@router_msg_q.delete("/kafka/{id}")
async def delete_kafka(req: Request, id: str):
    fwd_path = f"/kafka/{id}"
    return await api.op_api(req, "delete", "cms-builder", fwd_path)


@router_msg_q.post("/kafka/{id}/action")
async def post_kafka_action(req: Request, id: str):
    fwd_path = f"/kafka/{id}/action"
    return await api.op_api(req, "post", "cms-builder", fwd_path)

