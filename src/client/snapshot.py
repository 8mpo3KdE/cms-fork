import logging

import util
import compute
from client.common import ResourceBase
from client.common import get_svc_url


log = logging.getLogger("cms")


class InstanceSnapshot(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.res = "instance_snapshot"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/snapshot/instance"
        else:
            self.url = "{}/snapshot/instance".format(
                    get_svc_url(token_pack, "cms-backup"))

    def create(self):
        if util.is_uuid(self.args.instance):
            sid = self.args.instance
        else:
            sid = compute.Instance(self.args, self.token_pack).get_id_by_name(
                    self.args.instance)
            if not sid:
                return
        res = {"name": self.args.name,
                "instance_id": sid,
                "volumes": self.args.volume_id}
        data = {"instance_snapshot": res}
        resp = self.send_req("post", self.url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def rollback(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        data = {"rollback": {}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


arg_schema = {
    "instance": {
        "res-class": InstanceSnapshot,
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
                "name": "--volume-id",
                "attr": {
                    "action": "append"
                }
            }
        ],
        "rollback": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ]
    }
}

