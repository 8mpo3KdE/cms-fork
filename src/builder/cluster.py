import asyncio
import logging
import base64
import json

from common.config import config, zone_conf
from common import util
from common.resource_base import ResourceBase
from db import db

from openstack.keystone import Auth
from openstack.glance import Image
from openstack.neutron import Network, Subnet, Port, SecurityGroup, \
        SecurityGroupRule
from openstack.cinder import Volume
from openstack.nova import Flavor, Instance


log = logging.getLogger("uvicorn")

class Cluster(ResourceBase):
    def __init__(self, token_pack, res_name, table_name=None):
        super().__init__(token_pack, res_name=res_name,
                table_name=table_name)

    async def rh_get_instance(self, id):
        query = {"cluster_id": id}
        rows = await db.get("cluster_instance", query)
        return {"status": 200, "data": {"cluster_instance": rows}}

    async def create_cluster(self, cluster, enable_vip=True):
        cluster_id = cluster["id"]
        image_id = await Image(self.token_pack).get_id_by_name(
                cluster["image_name"])
        if not image_id:
            return -1
        with open("/root/.ssh/id_rsa.pub", "r") as fd:
            key = fd.read()
        user_data_s = "#cloud-config\n" \
                "users:\n" \
                "  - name: root\n" \
                "    ssh_authorized_keys:\n" \
                f"      - {key}"
        user_data = base64.b64encode(user_data_s.encode("utf-8")).decode(
                "utf-8")
        sg_name = f"{cluster['type']}_{cluster['name']}_default"
        log.info(f"Create SG {sg_name}.")
        params = {"name": sg_name}
        resp = await SecurityGroup(self.token_pack).post(
                {"security_group": params})
        if resp["status"] != 201:
            log.error("Create SG {} failed! {}".format(
                    sg_name, resp["data"]))
            return -1
        sg_id = resp["data"]["security_group"]["id"]
        update = {"sg_id": sg_id}
        await db.update(cluster["table"], cluster_id, update)

        log.info(f"Create SG rules for {sg_name}.")
        params = {"direction": "ingress",
                "ethertype": "IPv4",
                "security_group_id": sg_id}
        resp = await SecurityGroupRule(self.token_pack).post(
                {"security_group_rule": params})
        if resp["status"] != 201:
            log.error("Create SG rule for {} failed! {}".format(
                    sg_name, resp["data"]))
            return -1

        subnet = await Subnet(self.token_pack).get_obj(cluster["subnet_id"])
        if not subnet:
            log.error(f"Get subnet {cluster['subnet_id']} failed!")
            return -1
        network_id = subnet["network_id"]
        cluster["subnet_cidr"] = subnet["cidr"]

        svc_token_pack = await Auth().get_svc_token(zone_conf)
        mgmt_network_id = await Network(svc_token_pack).get_id_by_name(
                "svc-mgmt")

        port_ins = Port(self.token_pack)
        if (cluster["cluster_size"] > 1) and enable_vip:
            vip_port_name = f"{cluster['type']}_{cluster['name']}_vip"
            log.info(f"Create vip port {vip_port_name}.")
            params = {"name": vip_port_name,
                    "network_id": network_id,
                    "fixed_ips": [{"subnet_id": cluster["subnet_id"]}],
                    "port_security_enabled": False}
            resp = await port_ins.post({"port": params})
            if resp["status"] != 201:
                log.error("Create vip port {} failed! {}".format(
                        vip_port_name, resp["data"]))
                return -1
            vip_port = resp["data"]["port"]
            update = {"vip_port_id": vip_port["id"]}
            await db.update(cluster["table"], cluster_id, update)

        vol_ins = Volume(self.token_pack)
        ins_ins = Instance(self.token_pack)
        ins_ids = []
        ports = []
        for idx in range(0, cluster["cluster_size"]):
            port_name = f"{cluster['type']}_{cluster['name']}_{idx + 1}"
            log.info(f"Create port {port_name}.")
            params = {"name": port_name,
                    "network_id": network_id,
                    "fixed_ips": [{"subnet_id": cluster["subnet_id"]}],
                    "port_security_enabled": True,
                    "security_groups": [sg_id]}
            if (cluster["cluster_size"] > 1) and enable_vip:
                params["allowed_address_pairs"] = [
                        {"ip_address":
                            vip_port["fixed_ips"][0]["ip_address"]}]
            resp = await port_ins.post({"port": params})
            if resp["status"] != 201:
                log.error("Create port {} failed! {}".format(
                        port_name, resp["data"]))
                return -1
            port = resp["data"]["port"]
            ports.append(port)
            row = {"cluster_id": cluster_id,
                "cluster_type": cluster["type"],
                "user_port_id": port["id"],
                "user_address": port["fixed_ips"][0]["ip_address"]}
            await db.add("cluster_instance", row)

            vol_name = f"{cluster['type']}_{cluster['name']}_{idx + 1}"
            log.info(f"Create volume {vol_name}.")
            params = {"name": vol_name,
                    "size": cluster["volume_size"],
                    "imageRef": image_id}
            resp = await vol_ins.post({"volume": params})
            if resp["status"] != 202:
                log.error("Create volume {} failed! {}".format(
                        vol_name, resp["data"]))
                return -1
            vol_id = resp["data"]["volume"]["id"]
            update = {"volume_id": vol_id}
            await db.update("cluster_instance", row["id"], update)
            if await self.wait_for_ready(vol_ins, [vol_id], "available"):
                return -1

            ins_name = f"{cluster['type']}_{cluster['name']}_{idx + 1}"
            log.info(f"Create instance {ins_name}.")
            vol_size = cluster["volume_size"]
            params = {"name": ins_name,
                    "networks": [{"port": port["id"]}],
                    "block_device_mapping_v2": [{
                        "boot_index": "0",
                        "destination_type": "volume",
                        "source_type": "volume",
                        "uuid": vol_id}],
                    "user_data": user_data,
                    "flavorRef": cluster["spec_id"]}
            resp = await ins_ins.post({"server": params})
            if resp["status"] != 202:
                log.error("Create instance {} failed! {}".format(
                        ins_name, resp["data"]))
                return -1
            ins = resp["data"]["server"]
            ins_ids.append(ins["id"])
            update = {"instance_id": ins["id"], "instance_name": ins_name}
            await db.update("cluster_instance", row["id"], update)

        if await self.wait_for_ready(ins_ins, ins_ids, "ACTIVE"):
            return -1
        if await self.wait_for_login(ins_ids):
            return -1

        ins_iface_ins = Instance(svc_token_pack)
        mgmt_port_ins = Port(svc_token_pack)
        mgmt_ports = []
        for idx in range(0, cluster["cluster_size"]):
            mgmt_port_name = \
                    f"{cluster['type']}_{cluster['name']}_mgmt_{idx + 1}"
            log.info(f"Create mgmt port {mgmt_port_name}.")
            params = {"name": mgmt_port_name,
                    "network_id": mgmt_network_id,
                    "project_id": self.project_id,
                    "port_security_enabled": False}
            resp = await mgmt_port_ins.post({"port": params})
            if resp["status"] != 201:
                log.error("Create mgmt port {} failed! {}".format(
                        mgmt_port_name, resp["data"]))
                return -1
            mgmt_port = resp["data"]["port"]
            mgmt_ports.append(mgmt_port)
            query = {"instance_id": ins_ids[idx]}
            rows = await db.get("cluster_instance", query)
            update = {"mgmt_port_id": mgmt_port["id"],
                    "mgmt_address": mgmt_port["fixed_ips"][0]["ip_address"]}
            await db.update("cluster_instance", rows[0]["id"], update)

            log.info(f"Attach mgmt port {mgmt_port_name}.")
            data = {"interfaceAttachment": {"port_id": mgmt_port["id"]}}
            resp = await ins_iface_ins.add_interface(ins_ids[idx], data)
            if resp["status"] != 200:
                log.error("Attach mgmt port to {} failed! {}".format(
                        ins_ids[idx], resp["data"]))
                return -1

        if cluster["cluster_size"] > 1:
            if enable_vip:
                cluster["service_address"] = \
                        vip_port["fixed_ips"][0]["ip_address"]
            else:
                cluster["service_address"] = ""
        else:
            cluster["service_address"] = ports[0]["fixed_ips"][0]["ip_address"]

    async def delete_cluster(self, cluster):
        cluster_id = cluster["id"]
        name = cluster["name"]
        svc_token_pack = await Auth().get_svc_token(zone_conf)
        nodes = await db.get("cluster_instance", {"cluster_id": cluster_id})
        ins_iface_ins = Instance(svc_token_pack)
        mgmt_port_ins = Port(svc_token_pack)
        mgmt_port_ids = []
        for node in nodes:
            ins_id = node["instance_id"]
            mgmt_port_id = node["mgmt_port_id"]
            if (not ins_id) or (not mgmt_port_id):
                continue
            port = await mgmt_port_ins.get_obj(node["mgmt_port_id"])
            if (not port) or (not port["device_id"]):
                continue
            log.info(f"Detach mgmt interface from {ins_id}.")
            resp = await ins_iface_ins.remove_interface(ins_id, mgmt_port_id)
            if (resp["status"] != 202) and (resp["status"] != 404):
                log.error("Detach mgmt interface from {} failed! {}".format(
                        ins_id, resp["data"]))
                return -1
            if resp["status"] == 404:
                continue
            mgmt_port_ids.append(mgmt_port_id)
        if await self.wait_for_ready(mgmt_port_ins, mgmt_port_ids, "DOWN"):
            return -1
        for node in nodes:
            port_id = node["mgmt_port_id"]
            if not port_id:
                continue
            log.info(f"Delete mgmt port {port_id}.")
            resp = await mgmt_port_ins.delete(port_id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete mgmt port {} failed! {}".format(
                        port_id, resp["data"]))
                return -1
        ins_ins = Instance(self.token_pack)
        ins_ids = []
        for node in nodes:
            ins_id = node["instance_id"]
            if not ins_id:
                continue
            log.info(f"Delete instance {ins_id}.")
            resp = await ins_ins.delete(ins_id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete instance {} failed! {}".format(
                        ins_id, resp["data"]))
                return -1
            if resp["status"] == 404:
                continue
            ins_ids.append(ins_id)
        if await self.wait_for_ready(ins_ins, ins_ids, "DELETED"):
            return -1
        user_port_ins = Port(self.token_pack)
        for node in nodes:
            port_id = node["user_port_id"]
            if not port_id:
                continue
            log.info(f"Delete user port {port_id}.")
            resp = await user_port_ins.delete(port_id)
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete user port {} failed! {}".format(
                        port_id, resp["data"]))
                return -1
        vol_ins = Volume(self.token_pack)
        for node in nodes:
            vol_id = node["volume_id"]
            if not vol_id:
                continue
            log.info(f"Delete volume {vol_id}.")
            resp = await vol_ins.delete(vol_id)
            if (resp["status"] != 202) and (resp["status"] != 404):
                log.error("Delete volume {} failed! {}".format(
                        vol_id, resp["data"]))
                return -1
        for node in nodes:
            await db.delete("cluster_instance", node["id"])
        if cluster["vip_port_id"]:
            log.info(f"Delete vip port {cluster['vip_port_id']}.")
            resp = await user_port_ins.delete(cluster["vip_port_id"])
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete vip port {} failed! {}".format(
                        cluster["vip_port_id"], resp["data"]))
                return -1
        if cluster["sg_id"]:
            log.info(f"Delete SG {cluster['sg_id']}.")
            sg_ins = SecurityGroup(self.token_pack)
            resp = await sg_ins.delete(cluster["sg_id"])
            if (resp["status"] != 204) and (resp["status"] != 404):
                log.error("Delete SG {} failed! {}".format(
                        cluster["sg_id"], resp["data"]))
                return -1

    async def extend_disk(self, nodes, size, path=None, vol_id=None):
        vol_ids = []
        if vol_id:
            vol_ids.append(vol_id)
        else:
            for node in nodes:
                vol_ids.append(node["volume_id"])
        vol_ins = Volume(self.token_pack)
        params = {"new_size": size}
        for vol_id in vol_ids:
            log.info(f"Extend volume {vol_id}")
            resp = await vol_ins.action(vol_id, {"os-extend": params})
            if resp["status"] != 202:
                log.error(f"Extend volume {vol_id} failed!")
                return -1
        if await self.wait_for_ready(vol_ins, vol_ids, "in-use"):
            log.error(f"Extend volume timeout!")
            return -1
        if path:
            for node in nodes:
                host = node["mgmt_address"]
                cmd = f"ssh {host} xfs_growfs {path}"
                await util.exec_cmd(cmd)
        else:
            for node in nodes:
                host = node["mgmt_address"]
                cmd = f"ssh {host} lsblk -J"
                rc,output = await util.exec_cmd(cmd, output=True)
                blks = json.loads(output)["blockdevices"]
                dev = None
                for blk in blks:
                    if "children" in blk:
                        for child in blk["children"]:
                            if ("mountpoints" in child) \
                                    and ("/" in child["mountpoints"]):
                                dev = child["name"]
                if not dev:
                    log.error(f"Not found device to extend!")
                    return -1
                cmd = f"ssh {host} growpart /dev/{dev[:-1]} {dev[-1]}"
                await util.exec_cmd(cmd)
                cmd = f"ssh {host} xfs_growfs /"
                await util.exec_cmd(cmd)

