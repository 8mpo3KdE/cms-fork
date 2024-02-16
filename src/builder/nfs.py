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
from openstack.nova import Flavor, Instance
from openstack.cinder import Volume, VolumeType


log = logging.getLogger("uvicorn")

class DiskObject(BaseModel):
    name: str = ""
    size: int
    volume_type: str = ""
    exported: bool = False


class NFSObject(BaseModel):
    name: str
    cluster_size: int = 1
    spec_id: UUID
    subnet_id: UUID
    volume_size: int = 40
    disks: list[DiskObject] = []


class NFSPost(BaseModel):
    nfs: NFSObject


class NFSPutObject(BaseModel):
    status: str = ""


class NFSPut(BaseModel):
    nfs: NFSPutObject


class NFSDiskPost(BaseModel):
    disk: DiskObject


class ActionExtend(BaseModel):
    extend: dict


class NFSDiskAction(RootModel):
    root: Union[ActionExtend]


class DirectoryObject(BaseModel):
    name: str


class NFSDirectoryPost(BaseModel):
    directory: DirectoryObject


class NFS(Cluster):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="nfs",
                table_name="nfs_cluster")
        self.action_map = {"extend": self.action_extend}
        self.svc_path = os.getcwd()
        self.build_log = "/var/log/cms/nfs-build.log"
        if "build-log" in config["nfs"]:
            self.build_log = config["nfs"]["build-log"]
        loader = jinja2.FileSystemLoader(f"{self.svc_path}/nfs-template")
        self.j2_env = jinja2.Environment(trim_blocks=True,
                lstrip_blocks=True, loader=loader)

    async def rh_post(self, req_data):
        req = req_data[self.res_name]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        cluster_size = req["cluster_size"]
        if cluster_size not in [1, 2]:
            msg = f"Cluster size {cluster_size} is not supported!"
            return {"status": 400, "data": {"message": msg}}
        if req["volume_size"] > 5000:
            msg = f"Volume size has to be <= 5000GB!"
            return {"status": 400, "data": {"message": msg}}
        spec_id = str(req["spec_id"])
        obj = await Flavor(self.token_pack).get_obj(spec_id)
        if not obj:
            msg = f"Spec {spec_id} not found!"
            return {"status": 400, "data": {"message": msg}}
        if (cluster_size > 1) and req["disks"]:
            for disk in req["disks"]:
                if disk["volume_type"] \
                        and ("multi-attach" not in disk["volume_type"]):
                    msg = f"Volume type has to be multi-attach!"
                    return {"status": 400, "data": {"message": msg}}
        cluster = {"name": req["name"],
                "project_id": self.project_id,
                "subnet_id": str(req["subnet_id"]),
                "cluster_size": cluster_size,
                "volume_size": req["volume_size"],
                "status": "building"}
        await db.add(self.table_name, cluster)
        cluster["spec_id"] = spec_id
        task = asyncio.create_task(self.task_create_cluster(
                cluster, req["disks"]))
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

    async def rh_get_disk_list(self, cid):
        disks = await db.get("nfs_disk", {"cluster_id": cid})
        return {"status": 200, "data": {"disks": disks}}

    async def add_disk(self, req, cluster):
        disk = {"name": req["name"],
                "size": req["size"],
                "exported": req["exported"],
                "cluster_id": cluster["id"],
                "status": "building"}
        await db.add("nfs_disk", disk)
        disk["volume_type"] = req["volume_type"]
        task = asyncio.create_task(self.task_add_disk(disk, cluster))
        task.add_done_callback(util.task_done_cb)
        return disk["id"], task

    async def rh_post_disk(self, cid, req_data):
        req = req_data["disk"]
        v = {"name": "name", "size": "size-volume"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        cluster = await self.get_obj(cid)
        if cluster["status"] != "active":
            msg = f"NFS cluster is not active!"
            return {"status": 400, "data": {"message": msg}}
        if req["volume_type"] and (cluster["cluster_size"] > 1) \
                and ("multi-attach" not in req["volume_type"]):
            msg = f"Volume type has to be multi-attach!"
            return {"status": 400, "data": {"message": msg}}
        disks = await db.get("nfs_disk", {"cluster_id": cid})
        if len(disks) >= 8:
            msg = f"Exceed max 8 disks!"
            return {"status": 400, "data": {"message": msg}}
        for disk in disks:
            if disk["name"] == req["name"]:
                msg = f"Disk {req['name']} exists!"
                return {"status": 400, "data": {"message": msg}}
            if disk["status"] != "active":
                msg = f"Disk {disk['name']} is not active!"
                return {"status": 400, "data": {"message": msg}}
        disk_id, task = await self.add_disk(req, cluster)
        return {"status": 202, "data": {"disk": {"id": disk_id}}}

    async def rh_post_disk_action(self, cid, id, req):
        action = list(req)[0]
        if action not in self.action_map:
            msg = f"Invalid action {action}!"
            return {"status": 405, "data": msg}
        return await self.action_map[action](cid, id, req[action])

    async def rh_delete_disk(self, cid, id):
        cluster = await self.get_obj(cid)
        if not cluster:
            return {"status": 404}
        if (cluster["status"] != "active") and (cluster["status"] != "error"):
            msg = f"NFS cluster is {cluster['status']}, not active or error!"
            return {"status": 400, "data": {"message": msg}}
        disks = await db.get("nfs_disk", {"id": id})
        if not disks:
            msg = f"Disk {id} not found!"
            return {"status": 404, "data": {"message": msg}}
        await db.update("nfs_disk", id, {"status": "deleting"})
        task = asyncio.create_task(self.task_remove_disk(disks[0], cluster))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def rh_get_directory(self, cid):
        nodes = await db.get("cluster_instance", {"cluster_id": cid})
        host = nodes[0]["mgmt_address"]
        cmd = f"ssh {host} cat /etc/exports" + " | awk '{print $1}' ORS=' '"
        rc,output = await util.exec_cmd(cmd, output=True)
        dirs = output.split(" ")
        return {"status": 200, "data": {"directories": dirs}}

    async def rh_post_directory(self, cid, did, req_data):
        req = req_data["directory"]
        v = {"name": "name"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        cluster = await self.get_obj(cid)
        if cluster["status"] != "active":
            msg = f"NFS cluster is not active!"
            return {"status": 400, "data": {"message": msg}}
        disks = await db.get("nfs_disk", {"id": did})
        if not disks:
            msg = f"Disk {did} not found!"
            return {"status": 404, "data": {"message": msg}}
        disk = disks[0]
        if disk["exported"]:
            msg = f"Disk {disk['name']} is exported."
            return {"status": 400, "data": {"message": msg}}
        nodes = await db.get("cluster_instance", {"cluster_id": cid})
        host = nodes[0]["mgmt_address"]
        cmd = f"ssh {host} cat /etc/exports" \
                f" | awk '/{disk['name']}/" "{print $1}' ORS=' '"
        rc,output = await util.exec_cmd(cmd, output=True)
        dirs = output.split(" ")
        for dir in dirs:
            if req["name"] in dir:
                msg = f"Directory {req['name']} exists!"
                return {"status": 400, "data": {"message": msg}}
        task = asyncio.create_task(self.task_add_directory(
                f"/nfs/{disk['name']}/{req['name']}", cluster["id"]))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def rh_delete_directory(self, cid, did, name):
        v = {"name": "name"}
        msg = validator.validate({"name": name}, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        cluster = await self.get_obj(cid)
        if not cluster:
            return {"status": 404}
        if (cluster["status"] != "active") and (cluster["status"] != "error"):
            msg = f"NFS cluster is {cluster['status']}, not active or error!"
            return {"status": 400, "data": {"message": msg}}
        disks = await db.get("nfs_disk", {"id": did})
        if not disks:
            msg = f"Disk {did} not found!"
            return {"status": 404, "data": {"message": msg}}
        disk = disks[0]
        nodes = await db.get("cluster_instance", {"cluster_id": cid})
        host = nodes[0]["mgmt_address"]
        cmd = f"ssh {host} cat /etc/exports" \
                f" | awk '/{disk['name']}/" "{print $1}' ORS=' '"
        rc,output = await util.exec_cmd(cmd, output=True)
        dirs = output.split(" ")
        for dir in dirs:
            if name in dir:
                break
        else:
            msg = f"Directory {name} not found!"
            return {"status": 404, "data": {"message": msg}}
        task = asyncio.create_task(self.task_remove_directory(
                dir, cluster["id"]))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def action_extend(self, cid, did, args):
        size = int(args["size"])
        log.info(f"Action extend volume {did} in {cid} to {size}")
        cluster = await self.get_obj(cid)
        if cluster["status"] != "active":
            msg = f"NFS cluster is not active!"
            return {"status": 400, "data": {"message": msg}}
        disks = await db.get("nfs_disk", {"id": did})
        disk = disks[0]
        if disk["status"] != "active":
            msg = f"Disk {disk['name']} is not active!"
            return {"status": 400, "data": {"message": msg}}
        if size <= disk["size"]:
            msg = f"New size has to be > {disk['size']}GB!"
            return {"status": 400, "data": {"message": msg}}
        if size > 5000:
            msg = f"Volume size has to be <= 5000GB!"
            return {"status": 400, "data": {"message": msg}}
        await db.update("nfs_disk", did, {"status": "extending"})
        task = asyncio.create_task(self.task_action_extend(
                cluster, disk, size))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def task_create_cluster(self, cluster, disks):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        cluster["type"] = "nfs"
        cluster["table"] = self.table_name
        cluster["image_name"] = config["nfs"]["node-image"]
        log.info(f"Task create NFS cluster {cluster_id}.")
        if await self.create_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return

        update = {"service_address": cluster["service_address"]}
        await db.update(self.table_name, cluster_id, update)

        if await self.provision_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
        else:
            tasks = []
            for disk in disks:
                did, task = await self.add_disk(disk, cluster)
                tasks.append(task)
            log.info("Wait for all task_add_disk tasks done.")
            for task in tasks:
                await task
            await db.update(self.table_name, cluster_id, {"status": "active"})
        log.info(f"Task create NFS cluster {cluster_id} is done.")

    async def task_delete_cluster(self, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        cluster["type"] = "nfs"
        cluster["table"] = self.table_name
        log.info(f"Task delete NFS cluster {cluster_id}.")
        disks = await db.get("nfs_disk", {"cluster_id": cluster_id})
        for disk in disks:
            await self.task_remove_disk(disk, cluster)
        if await self.delete_cluster(cluster):
            await db.update(self.table_name, cluster_id, status_error)
            return
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, cluster_id, update)
        log.info(f"Task delete NFS cluster {cluster_id} is done.")

    async def task_add_disk(self, disk, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        log.info(f"Task add disk {disk['name']} to {cluster_id}.")
        vol_ins = Volume(self.token_pack)
        vol_name = f"nfs_{cluster['name']}_{disk['name']}"
        log.info(f"Create volume {vol_name}.")
        params = {"name": vol_name,
                "size": disk["size"]}
        if disk["volume_type"]:
            params["volume_type"] = disk["volume_type"]
        else:
            obj = await VolumeType(self.token_pack).get_obj("default")
            params["volume_type"] = obj["name"] + "-multi-attach"
        resp = await vol_ins.post({"volume": params})
        if resp["status"] != 202:
            log.error("Create volume {} failed! {}".format(
                    vol_name, resp["data"]))
            await db.update("nfs_disk", disk["id"], status_error)
            return
        vol_id = resp["data"]["volume"]["id"]

        if await self.wait_for_ready(vol_ins, [vol_id], "available"):
            await db.update("nfs_disk", disk["id"], status_error)
            return
        update = {"volume_id": vol_id}
        await db.update("nfs_disk", disk["id"], update)

        ins_ins = Instance(self.token_pack)
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        for node in nodes:
            log.info(f"Attach volume {vol_id} to {node['instance_id']}.")
            data = {"volumeAttachment": {"volumeId": vol_id}}
            resp = await ins_ins.add_volume(node["instance_id"], data)
            if resp["status"] != 200:
                log.error("Attach volume {} to {} failed! {}".format(
                        vol_id, node["instance_id"], resp["data"]))
                await db.update("nfs_disk", disk["id"], status_error)
                return
            # In case of multi-attach, volume status is "reserved" right after
            # attach, need to wait till "in-use" when the attachment is
            # completed, before doing the next attachment.
            if await self.wait_for_ready(vol_ins, [vol_id], "in-use"):
                await db.update("nfs_disk", disk["id"], status_error)
                return
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass
        for node in nodes:
            cmd = f"{self.svc_path}/nfsadm add-disk" \
                    f" {node['mgmt_address']} {cluster_id} {disk['name']}" \
                    f" {vol_id[:18]} {disk['exported']}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Add disk failed!")
                await db.update("nfs_disk", disk["id"], status_error)
                return rc
        update = {"status": "active"}
        await db.update("nfs_disk", disk["id"], update)
        log.info(f"Task add disk {disk['name']} to {cluster_id} is done.")

    async def task_remove_disk(self, disk, cluster):
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        log.info(f"Task remove disk {disk['name']} from {cluster_id}.")
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass
        for node in nodes:
            cmd = f"{self.svc_path}/nfsadm remove-disk" \
                    f" {node['mgmt_address']} {cluster_id} {disk['name']}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)

        vol_id = disk["volume_id"]
        if vol_id:
            ins_ins = Instance(self.token_pack)
            vol_ins = Volume(self.token_pack)
            for node in nodes:
                log.info(f"Detach volume {vol_id} from {node['instance_id']}.")
                resp = await ins_ins.remove_volume(node["instance_id"], vol_id)
                if resp["status"] != 202:
                    log.error("Detach volume {} from {} failed! {}".format(
                            vol_id, node["instance_id"], resp["data"]))
                # In case of multi-attach, volume status is "detaching" right
                # after detach, need to wait till "in-use" when the detachment
                # is completed, before doing the next detachment. After the
                # last detachment, the status will be "available".
                status = "in-use"
                if nodes.index(node) == len(nodes) - 1:
                    status = "available"
                if await self.wait_for_ready(vol_ins, [vol_id], status):
                    await db.update("nfs_disk", disk["id"], status_error)

            log.info(f"Delete volume {vol_id}.")
            resp = await vol_ins.delete(vol_id)
            if resp["status"] != 202:
                log.error("Delete volume {} failed! {}".format(
                        vol_id, resp["data"]))
        await db.delete("nfs_disk", disk["id"])
        log.info(f"Task remove disk {disk['name']} from {cluster_id} is done.")

    async def task_add_directory(self, dir_name, cluster_id):
        log.info(f"Task add directory {dir_name} to {cluster_id}.")
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        for node in nodes:
            cmd = f"{self.svc_path}/nfsadm add-directory" \
                    f" {node['mgmt_address']} {cluster_id} {dir_name}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Add directory failed!")
                return rc
        log.info(f"Task add directory {dir_name} to {cluster_id} is done.")

    async def task_remove_directory(self, dir_name, cluster_id):
        log.info(f"Task remove directory {dir_name} from {cluster_id}.")
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass
        for node in nodes:
            cmd = f"{self.svc_path}/nfsadm remove-directory" \
                    f" {node['mgmt_address']} {cluster_id} {dir_name}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
        log.info(f"Task remove directory {dir_name} from {cluster_id} is done.")

    async def task_action_extend(self, cluster, disk, size):
        cluster_id = cluster["id"]
        vol_id = disk["volume_id"]
        log.info(f"Task extend volume {vol_id}.")
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        if await self.extend_disk(nodes, size, path=f"/nfs/{disk['name']}",
                vol_id=vol_id):
            log.error(f"Extend volume {vol_id} on path {path} failed!")
            await db.update("nfs_disk", disk["id"], {"status": "error"})
            return
        update = {"status": "active", "size": size}
        await db.update("nfs_disk", disk["id"], update)
        log.info(f"Task extend volume {vol_id} is done.")

    async def provision_cluster(self, cluster):
        cluster_id = cluster["id"]
        log.info(f"Provision node for NFS cluster {cluster_id}.")
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
        if cluster["cluster_size"] > 1:
            vars = {"vip": cluster["service_address"],
                    "vrid": cluster["service_address"].split(".")[-1]}
            t = self.j2_env.get_template(f"keepalived.conf.j2")
            with open(f"/tmp/{cluster_id}/keepalived.conf", "w") as fd:
                fd.write(t.render(vars))
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        for node in nodes:
            cmd = f"{self.svc_path}/nfsadm deploy {node['mgmt_address']}" \
                    f" {cluster_id} {cluster['cluster_size'] > 1}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file=fd)
            if rc:
                log.error(f"Provision node failed!")
                return rc
        await util.exec_cmd(f"rm -fr /tmp/{cluster_id}")

