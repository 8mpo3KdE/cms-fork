import logging

import block
import compute
import util
from client.common import ResourceBase
from client.common import get_svc_url

log = logging.getLogger("cms")


class VolumeBackup(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.res = "volume_backup"
        self.args = args
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/backup/volume"
        else:
            self.url = "{}/backup/volume".format(
                    get_svc_url(token_pack, "cms-backup"))

    def create(self):
        sid = block.Volume(self.args, self.token_pack).get_id_by_name(
                self.args.volume_name)
        if not sid:
            return
        res = {"name": self.args.name,
                "volume_id": sid}
        if self.args.incremental:
            res["incremental"] = self.args.incremental
        if self.args.copy_zone:
            res["copy_zone"] = self.args.copy_zone
        if self.args.copy_project:
            res["copy_project"] = self.args.copy_project
        data = {"volume_backup": res}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def set(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        res = {}
        if self.args.status:
            res["status"] = self.args.status
        if res:
            data = {"volume_backup": res}
            url = f"{self.url}/{id}"
            resp = self.send_req("put", url, self.headers, data)
            print(f"RC: {resp.status_code}")

    def update(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {}
        data = {"action": "update", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def restore(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {}
        if self.args.volume_name:
            metadata = {"volume_name": self.args.volume_name}
        data = {"action": "restore", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def copy(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {"zone": self.args.zone, "project": self.args.project}
        data = {"action": "copy", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class InstanceBackup(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.res = "instance_backup"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/backup/instance"
        else:
            self.url = "{}/backup/instance".format(
                    get_svc_url(token_pack, "cms-backup"))

    def create(self):
        if util.is_uuid(self.args.instance_name):
            sid = self.args.instance_name
        else:
            sid = compute.Instance(self.args, self.token_pack).get_id_by_name(
                    self.args.instance_name)
            if not sid:
                return
        res = {"name": self.args.name,
                "instance_id": sid,
                "volumes": self.args.volume_id}
        if self.args.incremental:
            res["incremental"] = self.args.incremental
        if self.args.copy_zone:
            res["copy_zone"] = self.args.copy_zone
        if self.args.copy_project:
            res["copy_project"] = self.args.copy_project
        data = {"instance_backup": res}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def set(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        res = {}
        if self.args.status:
            res["status"] = self.args.status
        if res:
            data = {"instance_backup": res}
            url = f"{self.url}/{id}"
            resp = self.send_req("put", url, self.headers, data)
            print(f"RC: {resp.status_code}")

    def update(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {}
        data = {"action": "update", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def restore(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {}
        if self.args.instance_name:
            metadata = {"instance_name": self.args.instance_name}
        data = {"action": "restore", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def copy(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        metadata = {"zone": self.args.zone, "project": self.args.project}
        data = {"action": "copy", "metadata": metadata}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


arg_schema = {
    "volume-backup": {
        "res-class": VolumeBackup,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--volume-name",
                "attr": {"required": True}
            },
            {
                "name": "--incremental",
                "attr": {"action": "store_true"}
            },
            {
                "name": "--copy-zone"
            },
            {
                "name": "--copy-project"
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "update": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ],
        "restore": [
            {"name": "name"},
            {"name": "--volume-name"}
        ],
        "copy": [
            {"name": "name"},
            {
                "name": "--zone",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--project",
                "attr": {
                    "required": True
                }
            }
        ]
    },
    "instance-backup": {
        "res-class": InstanceBackup,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--instance-name",
                "attr": {"required": True}
            },
            {
                "name": "--incremental",
                "attr": {"action": "store_true"}
            },
            {
                "name": "--volume-id",
                "attr": {
                    "required": True,
                    "action": "append"
                }
            },
            {
                "name": "--copy-zone"
            },
            {
                "name": "--copy-project"
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "update": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ],
        "restore": [
            {"name": "name"},
            {"name": "--instance-name"}
        ],
        "copy": [
            {"name": "name"},
            {
                "name": "--zone",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--project",
                "attr": {
                    "required": True
                }
            }
        ]
    }
}

