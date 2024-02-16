import os
import asyncio
import logging
import yaml
import base64
import jinja2
from pathlib import Path
from enum import Enum
from uuid import UUID
from ipaddress import IPv4Address, IPv4Network
from pydantic import BaseModel

from common.config import config, zone_conf
from common import util
from common import validator
from common.resource_base import ResourceBase
from db import db
from openstack.keystone import Auth
from openstack.neutron import Network, Subnet, Port, Router, \
        FloatingIP, SecurityGroup, SecurityGroupRule
from openstack.nova import Flavor, Instance
from openstack.glance import Image
from openstack.octavia import LoadBalancer


log = logging.getLogger("uvicorn")


class Access(str, Enum):
    corp = "corp"
    public = "public"


class K8sObject(BaseModel):
    name: str
    control_size: int = 1
    domain: str = "kubernetes"
    api_access: Access = Access.corp
    service_access: Access = Access.corp
    api_address: IPv4Address = ""
    ingress_address: IPv4Address = ""
    pod_address_block: IPv4Network = "10.250.0.0/16"
    service_address_block: IPv4Network = "10.251.0.0/22"
    node_address_block: IPv4Network = "192.168.200.0/24"
    node_subnet_id: UUID = ""
    corp_gateway_address: IPv4Address = ""
    public_gateway_address: IPv4Address = ""
    internal_api_address: IPv4Address = ""
    internal_ingress_address: IPv4Address = ""
    security_group_id: UUID = ""
    credential_name: str
    credential_secret: str
    version: str = ""


class K8sPost(BaseModel):
    kubernetes: K8sObject


class K8sPutObject(BaseModel):
    status: str = ""


class K8sPut(BaseModel):
    kubernetes: K8sPutObject


class K8sWorkerObject(BaseModel):
    count: int
    spec_id: UUID


class K8sWorkerPost(BaseModel):
    worker: K8sWorkerObject


class K8s(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="kubernetes",
                table_name="k8s_cluster")
        self.svc_path = os.getcwd()
        self.build_log = "/var/log/cms/k8s-build.log"
        if "build-log" in config["kubernetes"]:
            self.build_log = config["kubernetes"]["build-log"]
        loader = jinja2.FileSystemLoader(f"{self.svc_path}/k8s-template")
        self.j2_env = jinja2.Environment(trim_blocks=True,
                lstrip_blocks=True, loader=loader)
        self.tmp_path = None

    async def rh_get_version(self):
        vers = config[self.res_name]["version"].split(",")
        return {"status": 200, "data": {self.res_name: {"versions": vers}}}

    async def validate_fip(self, req, key):
        fip = str(req[key])
        fip_ins = FloatingIP(self.token_pack)
        log.info(f"Validate {key} {fip}.")
        obj = await fip_ins.get_obj_by_fip(fip)
        if not obj:
            msg = f"Get {key} {fip} failed!"
            return msg
        network = await Network(self.token_pack).get_obj(
                obj["floating_network_id"])
        if key == "api_address":
            if (req["api_access"] == "corp") \
                    and (network["name"] != "external-corp"):
                msg = f"{key} {fip} is not from external-corp!"
                return msg
            if (req["api_access"] == "public") \
                    and (network["name"] != "external-public"):
                msg = f"{key} {fip} is not from external-public!"
                return msg
        elif key == "ingress_address":
            if (req["service_access"] == "corp") \
                    and (network["name"] != "external-corp"):
                msg = f"{key} {fip} is not from external-corp!"
                return msg
            if (req["service_access"] == "public") \
                    and (network["name"] != "external-public"):
                msg = f"{key} {fip} is not from external-public!"
                return msg
        else:
            msg = f"{key} is invalid!"
            return msg

        if obj["port_id"]:
            msg = f"{key} {fip} is attached to port {obj['port_id']}!"
            return msg

    async def rh_post(self, req_data):
        req = req_data[self.res_name]
        v = {"name": "k8s-name",
             "control_size": "size-control"}
        msg = validator.validate(req, v)
        if msg:
            return {"status": 400, "data": {"message": msg}}
        versions = config["kubernetes"]["version"].split(",")
        if req["version"]:
            if req["version"] in versions:
                version = req["version"]
            else:
                msg = f"Version {req['version']} is not supported!"
                return {"status": 400, "data": {"message": msg}}
        else:
            version = versions[-1]
        if req["api_address"]:
            msg = await self.validate_fip(req, "api_address")
            if msg:
                return {"status": 400, "data": {"message": msg}}
        if req["ingress_address"]:
            msg = await self.validate_fip(req, "ingress_address")
            if msg:
                return {"status": 400, "data": {"message": msg}}
        result = await self.validate_credential(req["credential_name"],
                req["credential_secret"])
        if result["msg"]:
            return {"status": 400, "data": {"message": result["msg"]}}
        cluster = {"name": req["name"],
                "version": version,
                "project_id": self.project_id,
                "control_size": req["control_size"],
                "worker_count": 0,
                "domain": req["domain"],
                "api_access": req["api_access"],
                "service_access": req["service_access"],
                "api_address": str(req["api_address"]),
                "api_address_auto": True,
                "ingress_address": str(req["ingress_address"]),
                "ingress_address_auto": True,
                "pod_address_block": str(req["pod_address_block"]),
                "service_address_block": str(req["service_address_block"]),
                "node_address_block": str(req["node_address_block"]),
                "node_subnet_id": str(req["node_subnet_id"]),
                "node_subnet_auto": True,
                "sg_id": str(req["security_group_id"]),
                "sg_auto": True,
                "status": "building"}
        if cluster["api_address"]:
            cluster["api_address_auto"] = False
        if cluster["ingress_address"]:
            cluster["ingress_address_auto"] = False
        if cluster["node_subnet_id"]:
            obj = await Subnet(self.token_pack).get_obj(
                    cluster["node_subnet_id"])
            if not obj:
                msg = f"Subnet {cluster['node_subnet_id']} not found!"
                return {"status": 400, "data": {"message": msg}}
            cluster["node_subnet_auto"] = False
            cluster["node_network_id"] = obj["network_id"]
            cluster["node_address_block"] = obj["cidr"]
            if not req["corp_gateway_address"]:
                msg = f"Corp gateway address is missing!"
                return {"status": 400, "data": {"message": msg}}
            if (cluster["service_access"] == "public") \
                    and (not req["public_gateway_address"]):
                msg = f"Public gateway address is missing!"
                return {"status": 400, "data": {"message": msg}}
        if cluster["sg_id"]:
            cluster["sg_auto"] = False
        await db.add(self.table_name, cluster)
        if not cluster["node_subnet_auto"]:
            cluster["corp_gw_addr"] = str(req["corp_gateway_address"])
            cluster["public_gw_addr"] = str(req["public_gateway_address"])
            cluster["int_api_addr"] = str(req["internal_api_address"])
            cluster["int_ingress_addr"] = str(req["internal_ingress_address"])
            cluster["corp_gw_id"] = ""
            cluster["corp_gw_port_id"] = ""
            cluster["public_gw_id"] = ""
            cluster["public_gw_port_id"] = ""
            cluster["int_api_port_id"] = ""
            cluster["int_ingress_port_id"] = ""
        cluster["credential_name"] = req["credential_name"]
        cluster["credential_secret"] = req["credential_secret"]
        cluster["credential_id"] = result["id"]
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
        msg = await self.check_delete(cluster)
        if msg:
            return {"status": 409, "data": {"message": msg}}
        await db.update(self.table_name, id, {"status": "deleting"})
        task = asyncio.create_task(self.task_delete_cluster(cluster))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202, "data": {self.res_name: {"id": id}}}

    async def rh_get_config(self, cid):
        objs = await db.get("k8s_instance",
                {"cluster_id": cid, "bootstrap": True})
        if not objs:
            msg = "Bootstrap controller is not found!"
            return {"status": 404, "data": {"message": msg}}
        host = objs[0]["mgmt_addr"]
        cmd = f"ssh core@{host} " \
                "\"sudo cp /etc/kubernetes/admin.conf /home/core/; " \
                "sudo chown core: /home/core/admin.conf\""
        if await util.exec_cmd(cmd):
            return {"status": 404}
        cmd = f"scp core@{host}:admin.conf /tmp"
        await util.exec_cmd(cmd)
        with open("/tmp/admin.conf", "r") as fd:
            conf = yaml.safe_load(fd)
        return {"status": 200, "data": conf}

    async def rh_get_worker(self, cid):
        query = {"cluster_id": cid, "role": "worker"}
        objs = await db.get("k8s_instance", query)
        return {"status": 200, "data": {"workers": objs}}

    async def rh_post_worker(self, cid, req_data):
        req = req_data["worker"]
        cluster = await self.get_obj(cid)
        if cluster["status"] != "active":
            msg = f"Kubernetes cluster is not active!"
            return {"status": 400, "data": {"message": msg}}
        if req["count"] > 10:
            msg = "Add more than 10 workers!"
            return {"status": 400, "data": {"message": msg}}
        spec_id = str(req["spec_id"])
        obj = await Flavor(self.token_pack).get_obj(spec_id)
        if not obj:
            msg = f"Spec {spec_id} not found!"
            return {"status": 400, "data": {"message": msg}}
        await db.update(self.table_name, cluster["id"],
                {"status": "adding worker"})
        task = asyncio.create_task(self.task_add_worker(
                cluster, req["count"], spec_id))
        task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    async def check_delete(self, cluster):
        if not cluster["node_subnet_auto"]:
            return
        if not cluster["node_subnet_id"]:
            return
        query = {"network_id": cluster["node_network_id"]}
        ports = await Port(self.token_pack).get_obj_list(query)
        # controller + worker + 2x VIP + 1x DHCP + 1x or 2x gateway
        port_count = cluster["control_size"] + cluster["worker_count"] + 4
        if cluster["api_access"] != cluster["service_access"]:
            port_count += 1
        log.debug(f"auto port: {port_count}, actual port: {len(ports)}")
        diff = len(ports) - port_count
        if diff > 0:
            return f"{diff} ports need to be cleaned up before delete cluster."
        objs = await LoadBalancer(self.token_pack).get_obj_list()
        for obj in objs:
            if obj["vip_subnet_id"] == cluster["node_subnet_id"]:
                return f"Remove LB {obj['name']} before delete cluster."

    async def build_data(self, cluster):
        cluster_id = cluster["id"]
        log.info(f"Build data for cluster {cluster_id}.")
        spec_name = config["kubernetes"]["control-node-spec"]
        ctrl_spec_id = await Flavor(self.token_pack).get_id_by_name(spec_name)
        if not ctrl_spec_id:
            log.error(f"Get control node spec {spec_name} ID failed!")
            return -1
        cluster["ctrl_spec_id"] = ctrl_spec_id
        image_name = config["kubernetes"]["node-image"]
        image_id = await Image(self.token_pack).get_id_by_name(image_name)
        if not image_id:
            log.error(f"Get image {image_name} ID failed!")
            return -1
        cluster["image_id"] = image_id
        corp_network_id = await Network(self.token_pack).get_id_by_name(
                "external-corp")
        if not corp_network_id:
            log.error(f"Get external-corp network ID failed!")
            return -1
        cluster["corp_network_id"] = corp_network_id
        public_network_id = await Network(self.token_pack).get_id_by_name(
                "external-public")
        if not public_network_id:
            log.error(f"Get external-public network ID failed!")
            return -1
        cluster["public_network_id"] = public_network_id
        svc_token_pack = await Auth().get_svc_token(zone_conf)
        mgmt_network_id = await Network(svc_token_pack).get_id_by_name(
                "svc-mgmt")
        if not mgmt_network_id:
            log.error(f"Get svc-mgmt network ID failed!")
            return -1
        cluster["mgmt_network_id"] = mgmt_network_id

        if cluster["node_subnet_auto"]:
            block = IPv4Network(cluster["node_address_block"])
            cluster["metadata_addr"] = str(block[2])
            cluster["corp_gw_addr"] = str(block[1])
            if cluster["service_access"] == "public":
                cluster["public_gw_addr"] = str(block[3])
            cluster["node_subnet_prefix_len"] = block.prefixlen
            cluster["int_api_addr"] = str(block[4])
            cluster["int_ingress_addr"] = str(block[5])
        else:
            subnet_id = cluster["node_subnet_id"]
            obj = await Subnet(self.token_pack).get_obj(subnet_id)
            if not obj:
                log.error(f"subnet {subnet_id} not found!")
                return -1
            cluster["metadata_addr"] = obj["allocation_pools"][0]["start"]
            cluster["node_subnet_prefix_len"] = obj["cidr"].split("/")[1]
            port_ins = Port(self.token_pack)
            map = {"corp_gw_port_id": "corp_gw_addr",
                    "public_gw_port_id": "public_gw_addr",
                    "int_api_port_id": "int_api_addr",
                    "int_ingress_port_id": "int_ingress_addr"}
            for name in map.keys():
                if cluster[name]:
                    obj = await port_ins.get_obj(cluster[name])
                    cluster[map[name]] = obj["fixed_ips"][0]["ip_address"]

    async def create_sg(self, cluster):
        cluster_name = cluster["name"]
        cluster_id = cluster["id"]
        sg_name = "k8s_" + cluster_name
        log.info(f"Create SG {sg_name}.")
        params = {"name": sg_name}
        resp = await SecurityGroup(self.token_pack).post(
                {"security_group": params})
        if resp["status"] != 201:
            log.error("Create SG {} failed! {}".format(
                    sg_name, resp["data"]))
            return -1
        cluster["sg_id"] = resp["data"]["security_group"]["id"]
        await db.update(self.table_name, cluster_id,
                {"sg_id": cluster["sg_id"]})

        log.info(f"Create SG rules for {sg_name}.")
        params = {"direction": "ingress",
                "ethertype": "IPv4",
                "security_group_id": cluster["sg_id"]}
        resp = await SecurityGroupRule(self.token_pack).post(
                {"security_group_rule": params})
        if resp["status"] != 201:
            log.error("Create SG rule for {} failed! {}".format(
                    sg_name, resp["data"]))
            return -1

    async def create_network(self, cluster):
        cluster_name = cluster["name"]
        cluster_id = cluster["id"]
        network_name = "k8s_" + cluster_name
        log.info(f"Create node network {network_name}.")
        params = {"name": network_name}
        resp = await Network(self.token_pack).post({"network": params})
        if resp["status"] != 201:
            log.error("Create network {} failed! {}".format(
                    network_name, resp["data"]))
            return -1
        cluster["node_network_id"] = resp["data"]["network"]["id"]
        await db.update(self.table_name, cluster_id,
                {"node_network_id": cluster["node_network_id"]})

        subnet_name = "k8s_" + cluster_name
        log.info(f"Create node subnet {subnet_name}.")
        params = {"name": subnet_name,
                "ip_version": 4,
                "network_id": cluster["node_network_id"],
                "cidr": str(cluster["node_address_block"])}
        resp = await Subnet(self.token_pack).post({"subnet": params})
        if resp["status"] != 201:
            log.error("Create subnet {} failed! {}".format(
                    subnet_name, resp["data"]))
            return -1
        cluster["node_subnet_id"] = resp["data"]["subnet"]["id"]
        await db.update(self.table_name, cluster_id,
                {"node_subnet_id": cluster["node_subnet_id"]})

    async def create_router(self, cluster, type):
        cluster_name = cluster["name"]
        cluster_id = cluster["id"]
        router_ins = Router(self.token_pack)
        port_ins = Port(self.token_pack)
        gw_name = f"k8s_{cluster_name}_{type}"
        log.info(f"Create {type} gateway {gw_name}.")
        params = {"name": gw_name,
                "external_gateway_info": {
                    "network_id": cluster[f"{type}_network_id"]
                }}
        resp = await router_ins.post({"router": params})
        if resp["status"] != 201:
            log.error("Create {} gateway {} failed! {}".format(
                    type, gw_name, resp["data"]))
            return -1
        cluster[f"{type}_gw_id"] = resp["data"]["router"]["id"]
        await db.update(self.table_name, cluster_id,
                {f"{type}_gw_id": cluster[f"{type}_gw_id"]})

        log.info(f"Create {type} gateway port.")
        params = {"network_id": cluster["node_network_id"],
                "fixed_ips": [{
                    "subnet_id": cluster["node_subnet_id"],
                    "ip_address": cluster[f"{type}_gw_addr"]
                }],
                "port_security_enabled": False}
        resp = await port_ins.post({"port": params})
        if resp["status"] != 201:
            log.error("Create {} gateway port failed! {}".format(
                    type, resp["data"]))
            return -1
        cluster[f"{type}_gw_port_id"] = resp["data"]["port"]["id"]
        await db.update(self.table_name, cluster_id,
                {f"{type}_gw_port_id": cluster[f"{type}_gw_port_id"]})

        log.info(f"Attach node network to {type} gateway.")
        params = {"port_id": cluster[f"{type}_gw_port_id"]}
        resp = await router_ins.add_interface(
                cluster[f"{type}_gw_id"], params)
        if resp["status"] != 200:
            log.error("Attach to {} gateway failed! {}".format(
                    type, resp["data"]))
            return -1

    async def build_network(self, cluster):
        cluster_name = cluster["name"]
        cluster_id = cluster["id"]
        log.info(f"Build network for cluster {cluster_id}.")
        if cluster["sg_auto"]:
            if await self.create_sg(cluster):
                return -1
        if cluster["node_subnet_auto"]:
            if await self.create_network(cluster):
                return -1
            if await self.create_router(cluster, "corp"):
                return -1
            if cluster["service_access"] == "public":
                if await self.create_router(cluster, "public"):
                    return -1
        else:
            objs = await Port(self.token_pack).get_obj_list(
                    query={"network_id": cluster["node_network_id"]})
            for obj in objs:
                addr = obj["fixed_ips"][0]["ip_address"]
                if addr == cluster["corp_gw_addr"]:
                    cluster["corp_gw_port_id"] = obj["id"]
                    if obj["device_owner"] == "network:router_interface":
                        cluster["corp_gw_id"] = obj["device_id"]
                if addr == cluster["public_gw_addr"]:
                    cluster["public_gw_port_id"] = obj["id"]
                    if obj["device_owner"] == "network:router_interface":
                        cluster["public_gw_id"] = obj["device_id"]
            update = {"corp_gw_port_id": cluster["corp_gw_port_id"],
                    "public_gw_port_id": cluster["public_gw_port_id"]}
            await db.update(self.table_name, cluster_id, update)

    async def build_vip(self, cluster, type):
        cluster_id = cluster["id"]
        cluster_name = cluster["name"]
        log.info(f"Build {type} VIP for cluster {cluster_id}.")
        port_ins = Port(self.token_pack)
        log.info(f"Create internal {type} port.")
        params = {"name": f"k8s_{cluster_name}_int_{type}",
                "network_id": cluster["node_network_id"],
                "fixed_ips": [{
                    "subnet_id": cluster["node_subnet_id"]}],
                "port_security_enabled": False}
        vip_addr = cluster[f"int_{type}_addr"]
        if vip_addr:
            params["fixed_ips"][0]["ip_address"] = vip_addr
        resp = await port_ins.post({"port": params})
        if resp["status"] != 201:
            log.error("Create internal {} port failed! {}".format(
                    type, resp["data"]))
            return -1
        port = resp["data"]["port"]
        cluster[f"int_{type}_addr"] = port["fixed_ips"][0]["ip_address"]
        cluster[f"int_{type}_port_id"] = port["id"]
        await db.update(self.table_name, cluster_id,
                {f"int_{type}_port_id": port["id"]})

        fip_ins = FloatingIP(self.token_pack)
        fip = cluster[f"{type}_address"]
        if cluster[f"{type}_address_auto"]:
            log.info(f"Allocate {type} FIP.")
            params = {"description": f"k8s_{cluster_name}_external_{type}"}
            map = {"api": "api",
                    "ingress": "service"}
            access = f"{map[type]}_access"
            params["floating_network_id"] = \
                    cluster[f"{cluster[access]}_network_id"]
            resp = await fip_ins.post({"floatingip": params})
            if resp["status"] != 201:
                log.error("Allocate FIP from external-{} failed! {}".format(
                        cluster[access], resp["data"]))
                return -1
            fip = resp["data"]["floatingip"]["floating_ip_address"]
            cluster[f"{type}_address"] = fip
            await db.update(self.table_name, cluster_id,
                    {f"{type}_address": fip})

        if (not cluster["node_subnet_auto"]) \
                and (not cluster["corp_gw_id"]):
            return

        log.info(f"Attach {type} FIP {fip} to port {port['id']}.")
        obj = await fip_ins.get_obj_by_fip(fip)
        params = {"port_id": port["id"]}
        resp = await fip_ins.put(obj["id"], {"floatingip": params})
        if resp["status"] != 200:
            log.error("Attach {} FIP {} to port {} failed! {}".format(
                    type, fip, port["id"], resp["data"]))
            return -1

    async def build_node_ign(self, cluster, role, count):
        cluster_id = cluster["id"]
        cluster_name = cluster["name"]
        log.info(f"Build {role} ign for cluster {cluster_id}.")
        t = self.j2_env.get_template(f"{role}.ign.yaml.j2")
        with open("{}/.ssh/id_rsa.pub".format(Path.home()), "r") as fd:
            key = fd.readline().rstrip("\n")
        vars = {"ssh_key": key,
                "node_prefix_len": cluster["node_subnet_prefix_len"],
                "mgmt_prefix_len": 22,
                "api_access": cluster["api_access"],
                "service_access": cluster["service_access"],
                "node_metadata_addr": cluster["metadata_addr"],
                "node_addrs": cluster["node_addrs"],
                "api_port_frontend": 6443,
                "api_port_backend": 8443,
                "api_int_vip": cluster["int_api_addr"],
                "api_vrid": cluster["int_api_addr"].split(".")[-1],
                "ingress_int_vip": cluster["int_ingress_addr"],
                "ingress_vrid": cluster["int_ingress_addr"].split(".")[-1],
                "corp_gw": cluster["corp_gw_addr"],
                "registry_fqdn": config["DEFAULT"]["registry-fqdn"],
                "domain": cluster["domain"]}
        if cluster["service_access"] == "public":
            vars["public_gw"] = cluster["public_gw_addr"]
        idx_offset = 0
        if role == "worker":
            idx_offset = cluster["worker_count"]
        for idx in range(0, count):
            vars["hostname"] = "k8s-{}-{}-{}".format(
                    cluster_name, role, idx + idx_offset + 1)
            vars["idx"] = idx
            if role == "worker":
                vars["ingress"] = ""
                if (idx + idx_offset + 1) <= 3:
                    vars["ingress"] = "nginx"
            ign = f"{self.tmp_path}/{role}-{idx + idx_offset + 1}.ign"
            with open(f"{ign}.yaml", "w") as fd:
                fd.write(t.render(vars))
            cmd = f"butane --pretty --strict {ign}.yaml > {ign}"
            await util.exec_cmd(cmd)

    async def build_node(self, cluster, role, count):
        cluster_id = cluster["id"]
        cluster_name = cluster["name"]
        vip_map = {"controller": cluster["int_api_addr"],
                "worker": cluster["int_ingress_addr"]}
        log.info(f"Build {role} for cluster {cluster_id}.")
        vip = vip_map[role]
        idx_offset = 0
        if role == "worker":
            idx_offset = cluster["worker_count"]
        port_ins = Port(self.token_pack)
        node_ports = []
        node_addrs = []
        for idx in range(0, count):
            port_name = "k8s_{}_{}_{}".format(
                    cluster["name"], role, idx + idx_offset + 1)
            log.info(f"Create user port {port_name}.")
            params = {"name": port_name,
                    "network_id": cluster["node_network_id"],
                    "port_security_enabled": True,
                    "security_groups": [cluster["sg_id"]],
                    "allowed_address_pairs": [{"ip_address": vip}]}
            if role == "worker":
                if (idx + idx_offset + 1) > 3:
                    params.pop("allowed_address_pairs")
            resp = await port_ins.post({"port": params})
            if resp["status"] != 201:
                log.error("Create port {} failed! {}".format(
                        port_name, resp["data"]))
                return -1
            port = resp["data"]["port"]
            node_ports.append(port)
            node_addrs.append(port["fixed_ips"][0]["ip_address"])
            row = {"cluster_id": cluster_id,
                "role": role,
                "node_port_id": port["id"],
                "node_addr": port["fixed_ips"][0]["ip_address"]}
            if (role == "controller") and (idx == 0):
                row["bootstrap"] = True
            await db.add("k8s_instance", row)
        cluster["node_ports"] = node_ports
        cluster["node_addrs"] = node_addrs

        svc_token_pack = await Auth().get_svc_token(zone_conf)
        port_ins_svc = Port(svc_token_pack)
        mgmt_ports = []
        hosts = []
        for idx in range(0, count):
            mgmt_port_name = "k8s_{}_{}_{}_mgmt".format(
                    cluster["name"], role, idx + idx_offset + 1)
            log.info(f"Create mgmt port {mgmt_port_name}.")
            params = {"name": mgmt_port_name,
                    "network_id": cluster["mgmt_network_id"],
                    "project_id": self.project_id,
                    "port_security_enabled": False}
            resp = await port_ins_svc.post({"port": params})
            if resp["status"] != 201:
                log.error("Create mgmt port {} failed! {}".format(
                        mgmt_port_name, resp["data"]))
                return -1
            port = resp["data"]["port"]
            mgmt_ports.append(port)
            hosts.append({"mgmt_addr": port["fixed_ips"][0]["ip_address"]})
            objs = await db.get("k8s_instance",
                    {"node_port_id": node_ports[idx]["id"]})
            if objs:
                update = {"mgmt_port_id": port["id"],
                        "mgmt_addr": port["fixed_ips"][0]["ip_address"]}
                await db.update("k8s_instance", objs[0]["id"], update)
        cluster["mgmt_ports"] = mgmt_ports
        cluster["hosts"] = hosts

        if await self.build_node_ign(cluster, role, count):
            return -1

        ins_ins = Instance(self.token_pack)
        ins_ids = []
        for idx in range(0, count):
            ins_name = "k8s-{}-{}-{}".format(
                    cluster["name"], role, idx + idx_offset + 1)
            hosts[idx]["name"] = ins_name
            log.info(f"Create instance {ins_name}.")
            with open(f"{self.tmp_path}/{role}-{idx + idx_offset + 1}.ign",
                    "r") as fd:
                content = fd.read()
            user_data = base64.b64encode(content.encode("utf-8")).decode(
                    "utf-8")
            params = {"name": ins_name,
                    "networks": [{"port": node_ports[idx]["id"]}],
                    "block_device_mapping_v2": [{
                        "boot_index": "0",
                        "source_type": "image",
                        "uuid": cluster["image_id"],
                        "volume_size": "40",
                        "destination_type": "volume",
                        "delete_on_termination": True}],
                    "user_data": user_data,
                    "flavorRef": cluster["ctrl_spec_id"]}
            if role == "worker":
                params["flavorRef"] = cluster["worker_spec_id"]
            resp = await ins_ins.post({"server": params})
            if resp["status"] != 202:
                log.error("Create instance {} failed! {}".format(
                        ins_name, resp["data"]))
                return -1
            ins_id = resp["data"]["server"]["id"]
            ins_ids.append(ins_id)
            objs = await db.get("k8s_instance",
                    {"node_port_id": node_ports[idx]["id"]})
            if objs:
                update = {"instance_id": ins_id}
                await db.update("k8s_instance", objs[0]["id"], update)
        if await self.wait_for_ready(ins_ins, ins_ids, "ACTIVE",
                count=20):
            return -1
        if await self.wait_for_login(ins_ids):
            return -1

        ins_ins_svc = Instance(svc_token_pack)
        for idx in range(0, count):
            log.info(f"Attach mgmt port {mgmt_ports[idx]['name']}.")
            params = {"port_id": mgmt_ports[idx]["id"]}
            resp = await ins_ins_svc.add_interface(ins_ids[idx],
                    {"interfaceAttachment": params})
            if resp["status"] != 200:
                log.error("Attach mgmt port to {} failed! {}".format(
                        ins_ids[idx], resp["data"]))
                return -1

    def check_build_log(self):
        try:
            if os.stat(self.build_log).st_size > (1024 * 1024 * 1024):
                os.truncate(self.build_log, 0)
        except:
            pass

    async def provision_node(self, cluster, role):
        cluster_id = cluster["id"]
        log.info(f"Provision {role} for cluster {cluster_id}.")
        cmd = f"cd {self.svc_path}/k8s-template;" \
                f"cp crictl.yaml {self.tmp_path}"
        await util.exec_cmd(cmd)
        http_proxy_url = f"http://{config['DEFAULT']['proxy-address']}:3128"
        vars = {"depot_fqdn": config["DEFAULT"]["depot-fqdn"],
                "repo_fedora_coreos": config["repo"]["fedora-coreos"],
                "repo_kubernetes": config["repo"]["kubernetes"],
                "http_proxy_url": http_proxy_url}
        t = self.j2_env.get_template(f"depot.repo.j2")
        with open(f"{self.tmp_path}/depot.repo", "w") as fd:
            fd.write(t.render(vars))
        vars = {"api_int_vip": cluster["int_api_addr"],
                "api_name": "api." + cluster["domain"],
                "registry_fqdn": config["DEFAULT"]["registry-fqdn"],
                "registry_address": config["DEFAULT"]["registry-address"],
                "depot_fqdn": config["DEFAULT"]["depot-fqdn"],
                "depot_address": config["DEFAULT"]["depot-address"]}
        files = ["hosts", "crio.conf"]
        for file in files:
            t = self.j2_env.get_template(f"{file}.j2")
            with open(f"{self.tmp_path}/{file}", "w") as fd:
                fd.write(t.render(vars))
        with open(f"{self.tmp_path}/crio", "w") as fd:
            fd.write(f"HTTPS_PROXY=\"{http_proxy_url}\"")
        self.check_build_log()
        for host in cluster["hosts"]:
            log.info(f"Provision {role} {host['name']}.")
            cmd = f"{self.svc_path}/k8sadm provision" \
                    f" --host {host['mgmt_addr']}" \
                    f" --id {cluster_id}" \
                    f" --version {cluster['version']}" \
                    f" --role {role}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file = fd)
            if rc:
                log.error(f"Provision {role} {host['name']} failed!")
                return -1
        for host in cluster["hosts"]:
            log.info(f"Reboot {host['name']}.")
            cmd = f"ssh core@{host['mgmt_addr']} sudo reboot"
            rc = await util.exec_cmd(cmd)
        log.info("Wait 10s for target shutdown.")
        await asyncio.sleep(10)
        for host in cluster["hosts"]:
            log.info(f"Post-Provision {role} {host['name']}.")
            cmd = f"{self.svc_path}/k8sadm post-provision" \
                    f" --host {host['mgmt_addr']}" \
                    f" --id {cluster_id}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file = fd)
            if rc:
                log.error(f"Post-Provision {role} {host} failed!")
                return -1
 
    async def join_node(self, cluster, role, hosts):
        cluster_id = cluster["id"]
        log.info(f"Join {role} to cluster {cluster_id}")
        objs = await db.get("k8s_instance",
                {"cluster_id": cluster_id, "bootstrap": True})
        bootstrap_host = objs[0]["mgmt_addr"]
        log.info(f"Build join configuration.")
        vars = {"api_name": "api." + cluster["domain"],
                "api_port_frontend": 6443,
                "api_port_backend": 8443}
        cmd = f"ssh core@{bootstrap_host} sudo kubeadm token create"
        rc, output = await util.exec_cmd(cmd, output = True)
        vars["token"] = output.rstrip("\n")
        cmd = f"ssh core@{bootstrap_host} " \
                "\"openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt " \
                "| openssl rsa -pubin -outform der 2>/dev/null " \
                "| openssl dgst -sha256 -hex\""
        rc, output = await util.exec_cmd(cmd, output = True)
        vars["cert_hash"] = "sha256:{}".format(
                output.rstrip("\n").split(" ")[1])
        if role == "controller":
            cmd = f"ssh core@{bootstrap_host} " \
                    "\"sudo kubeadm init phase upload-certs --upload-certs " \
                    "| tail -1\""
            rc, output = await util.exec_cmd(cmd, output = True)
            vars["cert_key"] = output.rstrip("\n")
        self.check_build_log()
        for host in hosts:
            if role == "worker":
                worker_idx = int(host["name"].split("-")[-1])
                vars["node_labels"] = ""
                if worker_idx <= 3:
                    vars["node_labels"] = "ingress=nginx"
            t = self.j2_env.get_template(f"join-{role}.yaml.j2")
            with open(f"{self.tmp_path}/join-{role}.yaml", "w") as fd:
                fd.write(t.render(vars))
            cmd = f"{self.svc_path}/k8sadm join" \
                    f" --host {host['mgmt_addr']}" \
                    f" --id {cluster_id}" \
                    f" --role {role}"
            with open(self.build_log, "a") as fd:
                rc = await util.exec_cmd(cmd, output_file = fd)
            if rc:
                log.error(f"Join node {role} {host['name']} failed!")
                return -1

    async def bootstrap_cluster(self, cluster):
        cluster_id = cluster["id"]
        host = cluster["hosts"][0]
        log.info(f"Bootstrap cluster on {host['name']}.")
        vars = {"name": cluster["name"],
                "version": cluster["version"],
                "api_port_frontend": 6443,
                "api_port_backend": 8443,
                "api_name": "api." + cluster["domain"],
                "service_address_block": cluster["service_address_block"],
                "pod_address_block": cluster["pod_address_block"],
                "registry_fqdn": config["DEFAULT"]["registry-fqdn"]}
        files = ["bootstrap.yaml", "kube-flannel.yaml"]
        for file in files:
            t = self.j2_env.get_template(f"{file}.j2")
            with open(f"{self.tmp_path}/{file}", "w") as fd:
                fd.write(t.render(vars))
        self.check_build_log()
        cmd = f"{self.svc_path}/k8sadm bootstrap" \
                f" --host {host['mgmt_addr']}" \
                f" --id {cluster_id}"
        with open(self.build_log, "a") as fd:
            rc = await util.exec_cmd(cmd, output_file = fd)
        if rc:
            log.error(f"Bootstrap on {host} failed!")
            return -1

    async def deploy_service(self, cluster):
        cluster_id = cluster["id"]
        log.info(f"Deploy Kubernetes services on cluster {cluster_id}.")
        vars = {"os_auth_url": zone_conf["auth-url"],
                "os_project_id": self.project_id,
                "os_credential_name": cluster["credential_name"],
                "os_credential_secret": cluster["credential_secret"],
                "os_credential_id": cluster["credential_id"],
                "node_subnet_id": cluster["node_subnet_id"],
                "external_network_id": cluster["corp_network_id"]}
        if cluster["service_access"] == "public":
            vars["external_network_id"] = cluster["public_network_id"]
        t = self.j2_env.get_template("cloud.conf.j2")
        with open(f"{self.tmp_path}/cloud.conf", "w") as fd:
            fd.write(t.render(vars))

        with open(f"{self.tmp_path}/cloud.conf", "r") as fd:
                content = fd.read()
        cloud_conf= base64.b64encode(content.encode("utf-8")).decode("utf-8")
        vars = {"cloud_conf": cloud_conf}
        t = self.j2_env.get_template("cloud.yaml.j2")
        with open(f"{self.tmp_path}/cloud.yaml", "w") as fd:
            fd.write(t.render(vars))

        vars = {"registry_fqdn": config["DEFAULT"]["registry-fqdn"]}
        await util.exec_cmd(f"mkdir -p {self.tmp_path}/svc")
        file_name = "openstack-cloud-controller-manager-ds.yaml"
        t = self.j2_env.get_template(
                f"cloud-provider-openstack/controller-manager/{file_name}.j2")
        with open(f"{self.tmp_path}/svc/{file_name}", "w") as fd:
            fd.write(t.render(vars))
        file_name = "cinder-csi-controllerplugin.yaml"
        t = self.j2_env.get_template(
                f"cloud-provider-openstack/cinder-csi-plugin/{file_name}.j2")
        with open(f"{self.tmp_path}/svc/{file_name}", "w") as fd:
            fd.write(t.render(vars))
        file_name = "cinder-csi-nodeplugin.yaml"
        t = self.j2_env.get_template(
                f"cloud-provider-openstack/cinder-csi-plugin/{file_name}.j2")
        with open(f"{self.tmp_path}/svc/{file_name}", "w") as fd:
            fd.write(t.render(vars))
        file_name = "ingress-nginx-baremetal-1.23.yaml"
        t = self.j2_env.get_template(f"ingress/{file_name}.j2")
        with open(f"{self.tmp_path}/svc/{file_name}", "w") as fd:
            fd.write(t.render(vars))
        self.check_build_log()
        host = cluster["hosts"][0]
        cmd = f"{self.svc_path}/k8sadm deploy-service" \
                f" --host {host['mgmt_addr']}" \
                f" --id {cluster_id}"
        with open(self.build_log, "a") as fd:
            rc = await util.exec_cmd(cmd, output_file = fd)
        if rc:
            log.error(f"Deploy service on {host} failed!")
            return -1

    async def task_create_cluster(self, cluster):
        err = False
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        log.info(f"Task create cluster {cluster_id}.")
        if await self.build_data(cluster):
            err = True
        elif await self.build_network(cluster):
            err = True
        elif await self.build_vip(cluster, "api"):
            err = True
        elif await self.build_vip(cluster, "ingress"):
            err = True
        if err:
            await db.update(self.table_name, cluster_id, status_error)
            return
        self.tmp_path = f"/tmp/{cluster_id}"
        await util.exec_cmd(f"mkdir -p {self.tmp_path}")
        if await self.build_node(cluster, "controller",
                cluster["control_size"]):
            err = True
        elif await self.provision_node(cluster, "controller"):
            err = True
        elif await self.bootstrap_cluster(cluster):
            err = True
        if err:
            await db.update(self.table_name, cluster_id, status_error)
            await util.exec_cmd(f"rm -fr {self.tmp_path}")
            return
        if len(cluster["hosts"]) > 1:
            hosts = cluster["hosts"][1:]
            if await self.join_node(cluster, "controller", hosts):
                await db.update(self.table_name, cluster_id, status_error)
                await util.exec_cmd(f"rm -fr {self.tmp_path}")
                return
        await self.deploy_service(cluster)
        await util.exec_cmd(f"rm -fr {self.tmp_path}")
        await db.update(self.table_name, cluster_id, {"status": "active"})
        log.info(f"Task create cluster {cluster_id} is done.")

    async def delete_node(self, cluster, role):
        cluster_id = cluster["id"]
        log.info(f"Delete {role} in cluster {cluster_id}.")
        query = {"cluster_id": cluster_id, "role": role}
        nodes = await db.get("k8s_instance", query)
        svc_token_pack = await Auth().get_svc_token(zone_conf)
        ins_ins_svc = Instance(svc_token_pack)
        port_ins_svc = Port(svc_token_pack)
        for node in nodes:
            if not node["instance_id"] or not node["mgmt_port_id"]:
                continue
            port = await port_ins_svc.get_obj(node["mgmt_port_id"])
            if not port:
                node["mgmt_port_id"] = None
                continue
            if not port["device_id"]:
                continue
            log.info(f"Detach mgmt interface from {node['instance_id']}.")
            resp = await ins_ins_svc.remove_interface(node["instance_id"],
                    node["mgmt_port_id"])
            if (resp["status"] != 202) and (resp["status"] != 404):
                log.error("Detach mgmt interface from {} failed! {}".format(
                        node["instance_id"], resp["data"]))
                return -1
        for node in nodes:
            id = node["mgmt_port_id"]
            if not id:
                continue
            log.info(f"Delete mgmt port {id}.")
            resp = await port_ins_svc.delete(id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete mgmt port {} failed! {}".format(
                        id, resp["data"]))
                return -1
        ins_ins = Instance(self.token_pack)
        ins_ids = []
        for node in nodes:
            id = node["instance_id"]
            if not id:
                continue
            log.info(f"Delete instance {id}.")
            resp = await ins_ins.delete(id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete instance {} failed! {}".format(
                        id, resp["data"]))
                return -1
            ins_ids.append(id)
        if await self.wait_for_ready(ins_ins, ins_ids, "DELETED",
                count=20):
            return -1
        node_port_ins = Port(self.token_pack)
        for node in nodes:
            id = node["node_port_id"]
            if not id:
                continue
            log.info(f"Delete node port {id}.")
            resp = await node_port_ins.delete(id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete node port {} failed! {}".format(
                        id, resp["data"]))
                return -1
        for node in nodes:
            await db.delete("k8s_instance", node["id"])

    async def delete_port(self, port_ins, cluster, key):
        log.info(f"Delete {key} from cluster {cluster['id']}.")
        id = cluster[key]
        if not id:
            return
        resp = await port_ins.delete(id)
        if (resp["status"] != 204) and (resp["status"] != 404):
            log.error(f"Delete port {id} failed! {resp['data']}")
            return -1
        await db.update(self.table_name, cluster["id"], {key: None})

    async def delete_fip(self, fip_ins, cluster, key):
        log.info(f"Delete {key} from cluster {cluster['id']}.")
        fip = cluster[key]
        if not fip:
            return
        obj = await fip_ins.get_obj_by_fip(fip)
        if obj:
            resp = await fip_ins.delete(obj["id"])
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error(f"Delete FIP {fip} failed! {resp['data']}")
                return -1
        await db.update(self.table_name, cluster["id"], {key: None})

    async def delete_router(self, router_ins, port_ins, cluster, type):
        router_key = f"{type}_gw_id"
        port_key = f"{type}_gw_port_id"

        if cluster[port_key] and cluster[router_key]:
            log.info(f"Remove router port {port_key}.")
            params = {"port_id": cluster[port_key]}
            resp = await router_ins.remove_interface(cluster[router_key],
                    params)
            if (resp["status"] != 200) and (resp["status"] != 404):
                log.error("Remove router port {} failed! {}".format(
                        cluster[port_key], resp["data"]))
                return -1
            await db.update(self.table_name, cluster["id"], {port_key: None})
            if await self.wait_for_ready(port_ins, [cluster[port_key]],
                    "DELETED"):
                log.error(f"Wait for port deleted timeout!")

        if cluster[router_key]:
            log.info(f"Delete router {router_key}.")
            resp = await router_ins.delete(cluster[router_key])
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete router {} failed! {}".format(
                        cluster[router_key], resp["data"]))
                return -1
            await db.update(self.table_name, cluster["id"], {router_key: None})

    async def delete_network(self, cluster):
        cluster_id = cluster["id"]
        log.info(f"Delete network in cluster {cluster_id}.")

        port_ins = Port(self.token_pack)
        if await self.delete_port(port_ins, cluster, "int_api_port_id"):
            return -1
        if await self.delete_port(port_ins, cluster, "int_ingress_port_id"):
            return -1

        fip_ins = FloatingIP(self.token_pack)
        if cluster["api_address_auto"]:
            if await self.delete_fip(fip_ins, cluster, "api_address"):
                return -1
        if cluster["ingress_address_auto"]:
            if await self.delete_fip(fip_ins, cluster, "ingress_address"):
                return -1

        if cluster["node_subnet_auto"]:
            router_ins = Router(self.token_pack)
            if await self.delete_router(router_ins, port_ins, cluster,
                    "corp"):
                return -1
            if await self.delete_router(router_ins, port_ins, cluster,
                    "public"):
                return -1

            id = cluster["node_subnet_id"]
            if id:
                log.info(f"Delete subnet {id} from cluster {cluster_id}")
                resp = await Subnet(self.token_pack).delete(id)
                if (resp["status"] != 204) and (resp["status"] != 404):
                    log.error("Delete node subnet {} failed! {}".format(
                            id, resp["data"]))
                    return -1
                await db.update(self.table_name, cluster_id,
                            {"node_subnet_id": None})
            id = cluster["node_network_id"]
            if id:
                log.info(f"Delete network {id} from cluster {cluster_id}")
                resp = await Network(self.token_pack).delete(id)
                if (resp["status"] != 204) and (resp["status"] != 404):
                    log.error("Delete node network {} failed! {}".format(
                            id, resp["data"]))
                    return -1
                await db.update(self.table_name, cluster_id,
                        {"node_network_id": None})
        if cluster["sg_auto"]:
            id = cluster["sg_id"]
            if id:
                log.info(f"Delete SG {id} from cluster {cluster_id}")
                resp = await SecurityGroup(self.token_pack).delete(id)
                if (resp["status"] != 204) and (resp["status"] != 404):
                    log.error("Delete SG {} failed! {}".format(
                            id, resp["data"]))
                    return -1
                await db.update(self.table_name, cluster_id, {"sg_id": None})

    async def task_delete_cluster(self, cluster):
        cluster_id = cluster["id"]
        err = False
        name = cluster["name"]
        log.info(f"Task delete cluster {cluster_id}.")

        if await self.delete_node(cluster, "controller"):
            err = True
        elif await self.delete_node(cluster, "worker"):
            err = True
        elif await self.delete_network(cluster):
            err = True
        if err:
            update = {"status": "error"}
        else:
            update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, cluster_id, update)
        log.info(f"Task delete cluster {cluster_id} is done.")

    async def task_add_worker(self, cluster, count, spec_id):
        err = False
        cluster_id = cluster["id"]
        status_error = {"status": "error"}
        log.info(f"Task add worker to {cluster_id}.")
        cluster["worker_spec_id"] = spec_id
        self.tmp_path = f"/tmp/{cluster_id}"
        await util.exec_cmd(f"mkdir -p {self.tmp_path}")
        if await self.build_data(cluster):
            err = True
        elif await self.build_node(cluster, "worker", count):
            err = True
        elif await self.provision_node(cluster, "worker"):
            err = True
        if err:
            await db.update(self.table_name, cluster_id, status_error)
            await util.exec_cmd(f"rm -fr {self.tmp_path}")
            return
        if await self.join_node(cluster, "worker", cluster["hosts"]):
            await db.update(self.table_name, cluster_id, status_error)
            await util.exec_cmd(f"rm -fr {self.tmp_path}")
            return
        await util.exec_cmd(f"rm -fr {self.tmp_path}")
        worker_count = cluster["worker_count"] + count
        await db.update(self.table_name, cluster_id,
                {"status": "active", "worker_count": worker_count})
        log.info(f"Task add worker to {cluster_id} is done.")

