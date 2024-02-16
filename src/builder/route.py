import asyncio
import logging
from fastapi import FastAPI, Header

from common import util, config
from common.route_wrapper import route_wrapper
from openstack.keystone import Auth
from db import db
from nfs import NFS, NFSPost, NFSPut, NFSDiskPost, NFSDirectoryPost, \
        NFSDiskAction
from k8s import K8s, K8sPost, K8sPut, K8sWorkerPost
from mariadb import MariaDB, MariaDBPost, MariaDBPut, MariaDBAction
from postgresql import PostgreSQL, PostgreSQLPost, PostgreSQLPut, \
        PostgreSQLAction
from redis import Redis, RedisPost, RedisPut, RedisAction
from rabbitmq import RabbitMQ, RabbitMQPost, RabbitMQPut, RabbitMQAction
from kafka import Kafka, KafkaPost, KafkaPut, KafkaAction
from harbor import Harbor, HarborPost, HarborPut, HarborAction

log = logging.getLogger("uvicorn")
app = FastAPI()


@app.on_event("startup")
async def api_start():
    log.info("Start server.")
    await db.create_engine()
    rc = -1
    while rc:
        rc = await db.check_table()
        if rc:
            log.error(f"Failed to check DB! Retry.")
            await asyncio.sleep(10)
    log.info("Checked DB.")
    auth_ins = Auth()
    while not config.svc_token_pack:
        config.svc_token_pack = await auth_ins.get_svc_token(config.zone_conf)
        if not config.svc_token_pack:
            log.error(f"Failed to service token! Retry.")
            await asyncio.sleep(10)
    log.info("Got service token.")


@app.on_event("shutdown")
async def api_shutdown():
    log.info("Shutdown server.")


@app.get("/")
async def get_root():
    return {"message": util.msg_root}


'''
NFS Cluster
'''
@app.get("/v1/nfs")
@route_wrapper
async def get_nfs_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await NFS(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/nfs/{id}")
@route_wrapper
async def get_nfs(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_get(id)


@app.get("/v1/nfs/{id}/instance")
@route_wrapper
async def get_nfs_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_get_instance(id)


@app.post("/v1/nfs")
@route_wrapper
async def post_nfs(req: NFSPost,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_post(req.model_dump())


@app.put("/v1/nfs/{id}")
@route_wrapper
async def put_nfs(id: str, req: NFSPut,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/nfs/{id}")
@route_wrapper
async def delete_nfs(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_delete(id)


'''
NFS Disk
'''
@app.get("/v1/nfs/{cid}/disk")
@route_wrapper
async def get_nfs_disk_list(cid: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_get_disk_list(cid)


#@app.get("/v1/nfs/{cid}/disk/{id}")
#@route_wrapper
#async def get_nfs_disk(cid: str, id: str,
#        x_auth_token=Header(None), token_pack=None):
#    return await NFS(token_pack).rh_get_disk(cid, id)


@app.post("/v1/nfs/{cid}/disk")
@route_wrapper
async def post_nfs_disk(cid: str, req: NFSDiskPost,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_post_disk(cid, req.model_dump())


@app.post("/v1/nfs/{cid}/disk/{id}/action")
@route_wrapper
async def post_nfs_disk_action(cid: str, id: str, req: NFSDiskAction,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_post_disk_action(cid, id, req.model_dump())


@app.delete("/v1/nfs/{cid}/disk/{id}")
@route_wrapper
async def delete_nfs_disk(cid: str, id: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_delete_disk(cid, id)


'''
NFS Directory
'''
@app.get("/v1/nfs/{cid}/directory")
@route_wrapper
async def get_nfs_directory_list(cid: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_get_directory(cid)


@app.post("/v1/nfs/{cid}/disk/{did}/directory")
@route_wrapper
async def post_nfs_directory(cid: str, did: str, req: NFSDirectoryPost,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_post_directory(cid, did, req.model_dump())


@app.delete("/v1/nfs/{cid}/disk/{did}/directory/{name}")
@route_wrapper
async def delete_nfs_directory(cid: str, did: str, name: str,
        x_auth_token=Header(None), token_pack=None):
    return await NFS(token_pack).rh_delete_directory(cid, did, name)


'''
Kubernetes Cluster
'''
@app.get("/v1/kubernetes")
@route_wrapper
async def get_k8s_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await K8s(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/kubernetes/version")
@route_wrapper
async def get_k8s_version(x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_get_version()


@app.get("/v1/kubernetes/{id}")
@route_wrapper
async def get_k8s(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_get(id)


@app.get("/v1/kubernetes/{id}/config")
@route_wrapper
async def get_k8s_config(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_get_config(id)


@app.post("/v1/kubernetes")
@route_wrapper
async def post_k8s(req: K8sPost,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_post(req.model_dump())


@app.put("/v1/kubernetes/{id}")
@route_wrapper
async def put_k8s(id: str, req: K8sPut,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/kubernetes/{id}")
@route_wrapper
async def delete_k8s(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_delete(id)


'''
Kubernetes Worker
'''
@app.get("/v1/kubernetes/{id}/worker")
@route_wrapper
async def get_k8s_worker_list(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_get_worker(id)


@app.post("/v1/kubernetes/{id}/worker")
@route_wrapper
async def post_k8s_worker(id: str, req: K8sWorkerPost,
        x_auth_token=Header(None), token_pack=None):
    return await K8s(token_pack).rh_post_worker(id, req.model_dump())


'''
MariaDB Cluster
'''
@app.get("/v1/mariadb")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await MariaDB(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/mariadb/version")
@route_wrapper
async def get_mariadb_version(x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_get_version()


@app.get("/v1/mariadb/{id}")
@route_wrapper
async def get_mariadb(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_get(id)


@app.get("/v1/mariadb/{id}/instance")
@route_wrapper
async def get_mariadb_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_get_instance(id)


@app.post("/v1/mariadb")
@route_wrapper
async def post_mariadb(req: MariaDBPost,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_post(req.model_dump())


@app.post("/v1/mariadb/{id}/action")
@route_wrapper
async def post_mariadb_action(id: str, req: MariaDBAction,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/mariadb/{id}")
@route_wrapper
async def put_mariadb(id: str, req: MariaDBPut,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/mariadb/{id}")
@route_wrapper
async def delete_mariadb(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await MariaDB(token_pack).rh_delete(id)


'''
PostgreSQL Cluster
'''
@app.get("/v1/postgresql")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await PostgreSQL(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/postgresql/version")
@route_wrapper
async def get_postgresql_version(x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_get_version()


@app.get("/v1/postgresql/{id}")
@route_wrapper
async def get_postgresql(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_get(id)


@app.get("/v1/postgresql/{id}/instance")
@route_wrapper
async def get_postgresql_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_get_instance(id)


@app.post("/v1/postgresql")
@route_wrapper
async def post_postgresql(req: PostgreSQLPost,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_post(req.model_dump())


@app.post("/v1/postgresql/{id}/action")
@route_wrapper
async def post_postgresql_action(id: str, req: PostgreSQLAction,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/postgresql/{id}")
@route_wrapper
async def put_postgresql(id: str, req: PostgreSQLPut,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/postgresql/{id}")
@route_wrapper
async def delete_postgresql(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await PostgreSQL(token_pack).rh_delete(id)


'''
Redis Cluster
'''
@app.get("/v1/redis")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await Redis(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/redis/version")
@route_wrapper
async def get_redis_version(x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_get_version()


@app.get("/v1/redis/{id}")
@route_wrapper
async def get_redis(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_get(id)


@app.get("/v1/redis/{id}/instance")
@route_wrapper
async def get_redis_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_get_instance(id)


@app.post("/v1/redis")
@route_wrapper
async def post_redis(req: RedisPost,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_post(req.model_dump())


@app.post("/v1/redis/{id}/action")
@route_wrapper
async def post_redis_action(id: str, req: RedisAction,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/redis/{id}")
@route_wrapper
async def put_redis(id: str, req: RedisPut,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/redis/{id}")
@route_wrapper
async def delete_redis(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Redis(token_pack).rh_delete(id)


'''
RabbitMQ Cluster
'''
@app.get("/v1/rabbitmq")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await RabbitMQ(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/rabbitmq/version")
@route_wrapper
async def get_rabbitmq_version(x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_get_version()


@app.get("/v1/rabbitmq/{id}")
@route_wrapper
async def get_rabbitmq(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_get(id)


@app.get("/v1/rabbitmq/{id}/instance")
@route_wrapper
async def get_rabbitmq_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_get_instance(id)


@app.post("/v1/rabbitmq")
@route_wrapper
async def post_rabbitmq(req: RabbitMQPost,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_post(req.model_dump())


@app.post("/v1/rabbitmq/{id}/action")
@route_wrapper
async def post_rabbitmq_action(id: str, req: RabbitMQAction,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/rabbitmq/{id}")
@route_wrapper
async def put_rabbitmq(id: str, req: RabbitMQPut,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/rabbitmq/{id}")
@route_wrapper
async def delete_rabbitmq(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await RabbitMQ(token_pack).rh_delete(id)


'''
Kafka Cluster
'''
@app.get("/v1/kafka")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await Kafka(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/kafka/version")
@route_wrapper
async def get_kafka_version(x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_get_version()


@app.get("/v1/kafka/{id}")
@route_wrapper
async def get_kafka(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_get(id)


@app.get("/v1/kafka/{id}/instance")
@route_wrapper
async def get_kafka_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_get_instance(id)


@app.post("/v1/kafka")
@route_wrapper
async def post_kafka(req: KafkaPost,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_post(req.model_dump())


@app.post("/v1/kafka/{id}/action")
@route_wrapper
async def post_kafka_action(id: str, req: KafkaAction,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/kafka/{id}")
@route_wrapper
async def put_kafka(id: str, req: KafkaPut,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/kafka/{id}")
@route_wrapper
async def delete_kafka(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Kafka(token_pack).rh_delete(id)


'''
Harbor Cluster
'''
@app.get("/v1/harbor")
@route_wrapper
async def get_maria_list(
        x_auth_token=Header(None), token_pack=None,
        all_projects: bool = True, name: str = None):
    return await Harbor(token_pack).rh_get_list(query={"name": name})


@app.get("/v1/harbor/version")
@route_wrapper
async def get_harbor_version(x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_get_version()


@app.get("/v1/harbor/{id}")
@route_wrapper
async def get_harbor(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_get(id)


@app.get("/v1/harbor/{id}/instance")
@route_wrapper
async def get_harbor_instance(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_get_instance(id)


@app.post("/v1/harbor")
@route_wrapper
async def post_harbor(req: HarborPost,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_post(req.model_dump())


@app.post("/v1/harbor/{id}/action")
@route_wrapper
async def post_harbor_action(id: str, req: HarborAction,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_post_action(id, req.model_dump())


@app.put("/v1/harbor/{id}")
@route_wrapper
async def put_harbor(id: str, req: HarborPut,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_put(id, req.model_dump())


@app.delete("/v1/harbor/{id}")
@route_wrapper
async def delete_harbor(id: str,
        x_auth_token=Header(None), token_pack=None):
    return await Harbor(token_pack).rh_delete(id)

