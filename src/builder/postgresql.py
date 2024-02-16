import os
import asyncio
import logging
import base64
import jinja2
from uuid import UUID
from typing import Union
from pydantic import BaseModel, RootModel

from common.config import config, zone_conf
from common import util
from common import validator
from cluster import Cluster
from db import db
from openstack.nova import Flavor


log = logging.getLogger("uvicorn")


class PostgreSQLObject(BaseModel):
    name: str
    cluster_size: int = 1
    spec_id: UUID
    subnet_id: UUID
    volume_size: int = 40
    version: str = ""


class PostgreSQLPost(BaseModel):
    postgresql: PostgreSQLObject


class ActionExtendVolume(BaseModel):
    extend_volume: dict


class PostgreSQLAction(RootModel):
    root: Union[ActionExtendVolume]


class PostgreSQLPutObject(BaseModel):
    status: str = ""


class PostgreSQLPut(BaseModel):
    postgresql: PostgreSQLPutObject


class PostgreSQL(Cluster):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="postgresql",
                table_name="postgresql_cluster")
        self.action_map = {"extend_volume": self.action_extend_volume}
        self.svc_path = os.getcwd()
        self.build_log = "/var/log/cms/postgresql-build.log"
        if "build-log" in config["postgresql"]:
            self.build_log = config["postgresql"]["build-log"]
        loader = jinja2.FileSystemLoader(
                f"{self.svc_path}/postgresql-template")
        self.j2_env = jinja2.Environment(trim_blocks=True,
                lstrip_blocks=True, loader=loader)

    async def rh_get_version(self):
        vers = config[self.res_name]["version"].split(",")
        return {"status": 200, "data": {self.res_name: {"versions": vers}}}

    async def rh_post(self, req_data):
        req = req_data[self.res_name]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        cluster_size = req["cluster_size"]
        if cluster_size not in [1, 3]:
            msg = f"Cluster size {cluster_size} is not supported!"
            return {"status": 400, "data": {"message": msg}}
        if req["volume_size"] > 5000:
            msg = f"Volume size has to be <= 5000GB!"
            return {"status": 400, "data": {"message": msg}}
        versions = config["postgresql"]["version"].split(",")
        if req["version"]:
            if req["version"] in versions:
                version = req["version"]
            else:
                msg = f"Version {req['version']} is not supported!"
                return {"status": 400, "data": {"message": msg}}
        else:
            version = versions[-1]
        spec_id = str(req["spec_id"])
        obj = await Flavor(self.token_pack).get_obj(spec_id)
        if not obj:
            msg = f"Spec {spec_id} not found!"
            return {"status": 400, "data": {"message": msg}}
        cluster = {"name": req["name"],
                "version": version,
                "project_id": self.project_id,
                "cluster_size": cluster_size,
                "volume_size": req["volume_size"],
                "subnet_id": str(req["subnet_id"]),
                "status": "building"}
        await db.add(self.table_name, cluster)
        cluster["spec_id"] = spec_id
        task = asyncio.create_task(self.task_create_cluster(cluster))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": cluster["id"]}}}

    async def rh_put(self, id, req_data):
        req = req_data[self.res_name]
        update = {}
        if req["status"]:
            update["status"] = req["status"]
        await db.update(self.table_name, id, update)
        return {"status": 200}

    async def rh_delete(self, id):
        cluster = await self.get_obj(id)
        if not cluster:
            return {"status": 404}
        await db.update(self.table_name, id, {"status": "deleting"})
        task = asyncio.create_task(self.task_delete_cluster(cluster))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def action_extend_volume(self, id, args):
        size = int(args["size"])
        log.info(f"Action extend volume in cluster {id} to {size}")
        cluster = await self.get_obj(id)
        if cluster["status"] != "active":
            msg = f"Cluster is not active!"
            return {"status": 400, "data": {"message": msg}}
        if size > 5000:
            msg = f"Volume size has to be <= 5000GB!"
            return {"status": 400, "data": {"message": msg}}
        if size <= cluster["volume_size"]:
            msg = f"Volume size has to be > {cluster['volume_size']}GB!"
            return {"status": 400, "data": {"message": msg}}
        await db.update(self.table_name, id, {"status": "extending volume"})
        task = asyncio.create_task(self.task_action_extend_volume(
                cluster, size))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def task_create_cluster(self, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        cluster["type"] = "postgresql"
        cluster["table"] = self.table_name
        cluster["image_name"] = config["postgresql"]["node-image"]
        log.info(f"Task create PostgreSQL cluster {cluster_id}.")
        if await self.create_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return
        update = {"service_address": cluster["service_address"]}
        await db.update(self.table_name, cluster_id, update)
        if await self.provision_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
        else:
            await db.update(self.table_name, cluster_id, {"status": "active"})
        log.info(f"Task create PostgreSQL cluster {cluster_id} is done.")

    async def task_delete_cluster(self, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        cluster["type"] = "postgresql"
        cluster["table"] = self.table_name
        log.info(f"Task delete PostgreSQL cluster {cluster_id}.")
        if await self.delete_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, cluster_id, update)
        log.info(f"Task delete PostgreSQL cluster {cluster_id} is done.")

    async def task_action_extend_volume(self, cluster, size):
        cluster_id = cluster["id"]
        log.info(f"Task extend volume in cluster {cluster_id}.")
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        if await self.extend_disk(nodes, size):
            log.error(f"Extend volume in cluster {cluster_id} failed!")
            await db.update(self.table_name, cluster_id, {"status": "error"})
            return
        update = {"status": "active", "volume_size": size}
        await db.update(self.table_name, cluster_id, update)
        log.info(f"Task extend volume in cluster {cluster_id} is done.")

    async def provision_cluster(self, cluster):
        cluster_id = cluster["id"]
        log.info(f"Provision node for PostgreSQL cluster {cluster_id}.")
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass
        await util.exec_cmd(f"mkdir -p /tmp/{cluster_id}")
        orig_nodes = await db.get("cluster_instance",
                {"cluster_id": cluster_id})
        nodes = sorted(orig_nodes, key=lambda d: d["instance_name"])
        with open(f"/tmp/{cluster_id}/hosts", "w") as fd:
            fd.write("127.0.0.1  localhost\n")
            for idx, node in enumerate(nodes):
                fd.write(f"{node['user_address']}  pg_{idx + 1}\n")
        http_proxy_url = f"http://{config['DEFAULT']['proxy-address']}:3128"
        vars = {"http_proxy_url": http_proxy_url,
                "depot_fqdn": config["DEFAULT"]["depot-fqdn"],
                "repo_baseos": config["repo"]["baseos"],
                "repo_appstream": config["repo"]["appstream"]}
        t = self.j2_env.get_template(f"depot.repo.j2")
        with open(f"/tmp/{cluster_id}/depot.repo", "w") as fd:
            fd.write(t.render(vars))
        vars = {"cidr": cluster["subnet_cidr"]}
        t = self.j2_env.get_template(f"pg_hba.conf.j2")
        with open(f"/tmp/{cluster_id}/pg_hba.conf", "w") as fd:
            fd.write(t.render(vars))
        ha = False
        if cluster["cluster_size"] > 1:
            vars = {"vip": cluster["service_address"],
                    "vrid": cluster["service_address"].split(".")[-1]}
            t = self.j2_env.get_template(f"keepalived.conf.j2")
            with open(f"/tmp/{cluster_id}/keepalived.conf", "w") as fd:
                fd.write(t.render(vars))
            ha = True
        for idx, node in enumerate(nodes):
            other_names = []
            for i in range(0, len(nodes)):
                if i == idx:
                    continue
                other_names.append(f"pg_{i + 1}")
            node["other_names"] = other_names
            node["standby_names"] = ""
            if other_names:
                node["standby_names"] = \
                        f"FIRST {len(other_names)} ({','.join(other_names)})"
        for node in nodes:
            log.info(f"Deploy on {node['instance_name']}.")
            arg_ha = ""
            if cluster["cluster_size"] > 1:
                vars = {"vip": cluster["service_address"],
                        "other_names": " ".join(node["other_names"])}
                t = self.j2_env.get_template(f"check-svc.j2")
                with open(f"/tmp/{cluster_id}/check-svc", "w") as fd:
                    fd.write(t.render(vars))
                arg_ha = "--ha"
            cmd = f"{self.svc_path}/postgresqladm deploy" \
                    f" --host {node['mgmt_address']}" \
                    f" --id {cluster_id}" \
                    f" --version {cluster['version']}" \
                    f" {arg_ha}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Deploy node failed!")
                return rc
        for idx,node in enumerate(nodes):
            type = "standby"
            if idx == 0:
                type = "primary"
                arg_primary = ""
            else:
                type = "standby"
                arg_primary = f" --primary {nodes[0]['user_address']}"
            log.info(f"Start the {type} on {node['instance_name']}.")
            vars = {"vip": cluster["service_address"],
                    "local_name": f"pg_{idx + 1}",
                    "standby_names": node["standby_names"]}
            t = self.j2_env.get_template(f"postgresql.conf.j2")
            with open(f"/tmp/{cluster_id}/postgresql.conf", "w") as fd:
                fd.write(t.render(vars))
            with open(self.build_log, "a") as fd:
                cmd = f"{self.svc_path}/postgresqladm start-{type}" \
                        f" --host {node['mgmt_address']}" \
                        f" --id {cluster_id}" \
                        f" {arg_primary}"
                rc = await util.exec_cmd(cmd, output_file=fd)
                if rc:
                    log.error(f"Start the {type} failed!")
                    return rc
                for name in node["other_names"]:
                    cmd = f"{self.svc_path}/postgresqladm create-slot" \
                            f" --host {node['mgmt_address']}" \
                            f" --id {cluster_id}" \
                            f" --name {name}"
                    rc = await util.exec_cmd(cmd, output_file=fd)
        await util.exec_cmd(f"rm -fr /tmp/{cluster_id}")

