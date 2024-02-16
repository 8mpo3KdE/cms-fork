from client.common import ResourceBase
from client.common import get_svc_url


class Volume(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "volume"
        self.detail = True
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/block/volume"
        else:
            svc_url = get_svc_url(token_pack, "volumev3")
            self.url = f"{svc_url}/volumes"

    def create(self):
        backup_id = self.get_id_by_name(self.args.backup,
                Backup(self.args, self.token_pack))
        if not backup_id:
            return
        data = {self.type: {
                "name": self.args.name,
                "backup_id": backup_id}}
        svc_url = get_svc_url(self.token_pack, "cms-backup")
        url = f"{svc_url}/volume"
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

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
            url = f"{self.args.cms_api_url}/v1/block/volume/{id}/action"
        else:
            svc_url = get_svc_url(self.token_pack, "cms-backup")
            url = f"{svc_url}/volume/{id}/action"
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def metadata_add(self, id, key, value):
        svc_url = get_svc_url(self.token_pack, "volumev3")
        url = f"{svc_url}/volumes/{id}/metadata/{key}"
        data = {"meta": {key: value}}
        resp = self.send_req("put", url, self.headers, data)

    def metadata_delete(self, id, key):
        svc_url = get_svc_url(self.token_pack, "volumev3")
        url = f"{svc_url}/volumes/{id}/metadata/{key}"
        resp = self.send_req("delete", url, self.headers)


class Snapshot(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "snapshot"
        self.detail = True
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/block/snapshot"
        else:
            svc_url = get_svc_url(token_pack, "volumev3")
            self.url = f"{svc_url}/snapshots"

    def create(self):
        vol_id = self.get_id_by_name(self.args.volume,
                Volume(self.args, self.token_pack))
        if not vol_id:
            return
        data = {self.type: {
                "name": self.args.name,
                "volume_id": vol_id,
                "force": True}}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Backup(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "backup"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/block/backup"
        else:
            svc_url = get_svc_url(token_pack, "cms-backup")
            self.url = f"{svc_url}/volume/backup"

    def list_snapshot(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/snapshot"
        resp = self.send_req("get", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def create(self):
        vol_id = self.get_id_by_name(self.args.volume,
                Volume(self.args, self.token_pack))
        if not vol_id:
            return
        res = {"name": self.args.name,
                "volume_id": vol_id}
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
    "volume": {
        "res-class": Volume,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--backup"}
        ],
        "rollback": [
            {"name": "name"},
            {
                "name": "--snapshot",
                "attr": {"required": True}
            }
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "volume-snapshot": {
        "res-class": Snapshot,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "volume-backup": {
        "res-class": Backup,
        "list": [],
        "list-snapshot": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--volume",
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

