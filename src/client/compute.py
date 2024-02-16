import util
from client.common import ResourceBase
from client.common import get_svc_url
from client import image
from client import network


class Spec(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        if args.cms_api_url:
            self.type = "flavor"
            self.url = f"{args.cms_api_url}/v1/compute/spec"
        else:
            self.type = "flavor"
            svc_url = get_svc_url(token_pack, "compute")
            self.url = f"{svc_url}/flavors"

    def create(self):
        data = {"name": self.args.name}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Instance(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "server"
        self.detail = True
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/compute/instance"
        else:
            svc_url = get_svc_url(token_pack, "compute")
            self.url = f"{svc_url}/servers"

    def rollback(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        ss_id = self.get_id_by_name(self.args.snapshot,
                Snapshot(self.args, self.token_pack))
        if not ss_id:
            return
        data = {"rollback": {
                "snapshot_id": ss_id}}
        if self.args.cms_api_url:
            url = f"{self.args.cms_api_url}/v1/compute/instance/{id}/action"
        else:
            svc_url = get_svc_url(self.token_pack, "cms-backup")
            url = f"{svc_url}/instance/{id}/action"
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def create(self):
        data = {"name": self.args.name}
        spec_id = Spec(self.args, self.token).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        data["spec"] = spec_id
        image_id = image.Image(self.args, self.token).get_id_by_name(
                self.args.image)
        if not image_id:
            return
        data["image"] = image_id
        nets = []
        for i in self.args.network:
            d = util.parse_kvs(i)
            net = {}
            if "port" in d:
                net["port"] = d["port"]
            else:
                if "name" in d:
                    nid = network.Network(self.args, self.token).\
                            get_id_by_name(d["name"])
                    if not nid:
                        return
                    net["id"] = nid
                if "address" in d:
                    net["address"] = d["address"]
            nets.append(net)
        data["networks"] = nets
        if self.args.block_device:
            d = util.parse_kvs(self.args.block_device)
            bd = {}
            if "src-type" in d:
                bd["source_type"] = d["src-type"]
            else:
                print("src-type is required for block-device.")
                return
            if "src-id" in d:
                bd["source_id"] = d["src-id"]
            else:
                print("src-id is required for block-device.")
                return
            if "size" in d:
                bd["volume_size"] = d["size"]
            if "retian" in d:
                bd["retain"] = d["retain"]
            bd["boot_index"] = 0
            data["block_devices"] = [bd]
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def metadata_add(self, id, key, value):
        url = f"{self.url}/{id}/metadata/{key}"
        data = {"meta": {key: value}}
        resp = self.send_req("put", url, self.headers, data)

    def metadata_delete(self, id, key):
        url = f"{self.url}/{id}/metadata/{key}"
        resp = self.send_req("delete", url, self.headers)


class Snapshot(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "snapshot"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/compute/snapshot"
        else:
            svc_url = get_svc_url(token_pack, "cms-backup")
            self.url = f"{svc_url}/instance/snapshot"

    def create(self):
        ins_id = self.get_id_by_name(self.args.instance,
                Instance(self.args, self.token_pack))
        if not ins_id:
            return
        data = {self.type: {
                "name": self.args.name,
                "instance_id": ins_id}}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Backup(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "backup"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/compute/backup"
        else:
            svc_url = get_svc_url(token_pack, "cms-backup")
            self.url = f"{svc_url}/instance/backup"

    def create(self):
        ins_id = self.get_id_by_name(self.args.instance,
                Instance(self.args, self.token_pack))
        if not ins_id:
            return
        res = {"name": self.args.name,
                "instance_id": ins_id}
        if self.args.incremental:
            res["incremental"] = self.args.incremental
        if self.args.copy_zone:
            res["copy_zone"] = self.args.copy_zone
        if self.args.copy_project:
            res["copy_project"] = self.args.copy_project
        data = {self.type: res}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def update(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        data = {"update": {}}
        url = f"{self.url}/{id}/action"
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


arg_schema = {
    "spec": {
        "res-class": Spec,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--ram",
                "attr": {"required": True}
            },
            {
                "name": "--vcpu",
                "attr": {"required": True}
            },
            {
                "name": "--disk",
                "attr": {"required": True}
            },
            {"name": "--id"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "instance": {
        "res-class": Instance,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--spec",
                "attr": {
                    "required": True,
                    "metavar": "<spec name>"
                }
            },
            {
                "name": "--image",
                "attr": {
                    "metavar": "<image name>"
                }
            },
            {
                "name": "--network",
                "attr": {
                    "required": True,
                    "action": "append",
                    "metavar": "name=<name>,port=<ID>,address=<address>"
                }
            },
            {
                "name": "--block-device",
                "attr": {
                    "metavar": "src-type=<name>,src-id=<ID>,size=<size>," \
                            "retain=<true/false>"
                }
            },
            {
                "name": "--availability-zone",
                "attr": {
                    "metavar": "<zone name>"
                }
            }
        ],
        "delete": [
            {"name": "name"}
        ],
        "rollback": [
            {"name": "name"},
            {
                "name": "--snapshot",
                "attr": {"required": True}
            }
        ]
    },
    "instance-snapshot": {
        "res-class": Snapshot,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--instance",
                "attr": {"required": True}
            }
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "instance-backup": {
        "res-class": Backup,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--instance",
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
        "update": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ]
    }
}

