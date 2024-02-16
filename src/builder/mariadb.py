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


class MariaDBObject(BaseModel):
    name: str
    cluster_size: int = 1
    spec_id: UUID
    subnet_id: UUID
    volume_size: int = 40
    version: str = ""


class MariaDBPost(BaseModel):
    mariadb: MariaDBObject


class ActionExtendVolume(BaseModel):
    extend_volume: dict


class MariaDBAction(RootModel):
    root: Union[ActionExtendVolume]


class MariaDBPutObject(BaseModel):
    status: str = ""


class MariaDBPut(BaseModel):
    mariadb: MariaDBPutObject


class MariaDB(Cluster):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="mariadb",
                table_name="mariadb_cluster")
        self.action_map = {"extend_volume": self.action_extend_volume}
        self.svc_path = os.getcwd()
        self.build_log = "/var/log/cms/mariadb-build.log"
        if "build-log" in config["mariadb"]:
            self.build_log = config["mariadb"]["build-log"]
        loader = jinja2.FileSystemLoader(f"{self.svc_path}/mariadb-template")
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
        versions = config["mariadb"]["version"].split(",")
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
        cluster["type"] = "mariadb"
        cluster["table"] = self.table_name
        cluster["image_name"] = config["mariadb"]["node-image"]
        log.info(f"Task create MariaDB cluster {cluster_id}.")
        if await self.create_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return
        update = {"service_address": cluster["service_address"]}
        await db.update(self.table_name, cluster_id, update)
        if await self.provision_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
        else:
            await db.update(self.table_name, cluster_id, {"status": "active"})
        log.info(f"Task create MariaDB cluster {cluster_id} is done.")

    async def task_delete_cluster(self, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        cluster["type"] = "mariadb"
        cluster["table"] = self.table_name
        log.info(f"Task delete MariaDB cluster {cluster_id}.")
        if await self.delete_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, cluster_id, update)
        log.info(f"Task delete MariaDB cluster {cluster_id} is done.")

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
        log.info(f"Provision node for MariaDB cluster {cluster_id}.")
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass
        await util.exec_cmd(f"mkdir -p /tmp/{cluster_id}")
        http_proxy_url = f"http://{config['DEFAULT']['proxy-address']}:3128"
        vars = {"http_proxy_url": http_proxy_url,
                "depot_fqdn": config["DEFAULT"]["depot-fqdn"],
                "repo_baseos": config["repo"]["baseos"],
                "repo_appstream": config["repo"]["appstream"]}
        t = self.j2_env.get_template(f"depot.repo.j2")
        with open(f"/tmp/{cluster_id}/depot.repo", "w") as fd:
            fd.write(t.render(vars))
        arg_ha = ""
        if cluster["cluster_size"] > 1:
            data = {"vip": cluster["service_address"],
                    "vrid": cluster["service_address"].split(".")[-1]}
            t = self.j2_env.get_template(f"keepalived.conf.j2")
            with open(f"/tmp/{cluster_id}/keepalived.conf", "w") as fd:
                fd.write(t.render(data))
            arg_ha = "--ha"
        orig_nodes = await db.get("cluster_instance",
                {"cluster_id": cluster_id})
        nodes = sorted(orig_nodes, key=lambda d: d["instance_name"])
        with open(f"/tmp/{cluster_id}/hosts", "w") as fd:
            fd.write("127.0.0.1  localhost\n")
            for node in nodes:
                fd.write("{}  {}\n".format(node["user_address"],
                        node["instance_name"].replace("_",  "-")))
        addrs = [f"{node['user_address']}:4567" for node in nodes]
        cluster_addrs = ",".join(addrs)
        for node in nodes:
            vars = {"node_address": node["user_address"],
                    "node_name": node["instance_name"],
                    "cluster_addresses": cluster_addrs}
            t = self.j2_env.get_template(f"my.cnf.j2")
            with open(f"/tmp/{cluster_id}/my.cnf", "w") as fd:
                fd.write(t.render(vars))
            cmd = f"{self.svc_path}/mariadbadm deploy" \
                    f" --host {node['mgmt_address']}" \
                    f" --id {cluster_id}" \
                    f" --version {cluster['version']}" \
                    f" {arg_ha}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Provision node failed!")
                return rc
        log.info(f"Bootstrap MariaDB cluster {cluster_id}.")
        cmd = f"{self.svc_path}/mariadbadm bootstrap" \
                f" --host {nodes[0]['mgmt_address']}" \
                f" --id {cluster_id}"
        with open(self.build_log, "a") as fd:
            rc = await util.exec_cmd(cmd, output_file=fd)
        if rc:
            log.error(f"Bootstrap node failed!")
            return rc
        for node in nodes[1:]:
            log.info("Join {} to MariaDB cluster {}.".format(
                    node["instance_name"], cluster_id))
            cmd = f"{self.svc_path}/mariadbadm join" \
                    f" --host {node['mgmt_address']}" \
                    f" --id {cluster_id}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Join node failed!")
                return rc
        await util.exec_cmd(f"rm -fr /tmp/{cluster_id}")

