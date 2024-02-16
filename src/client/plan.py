import logging

import block
import compute
from client.common import ResourceBase
from client.common import get_svc_url

log = logging.getLogger("cms")


class PlanBase(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)

    def execute(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        data = {"execute": {}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")

    def stop(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        data = {"stop": {}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")

    def start(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        data = {"start": {}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")

    def list_resource(self):
        plan_id = self.get_id_by_name(self.args.name)
        if not plan_id:
            return
        url = f"{self.url}/{plan_id}/resource"
        resp = self.send_req("get", url, self.headers)
        data = resp.json()["resource"]
        for type in data.keys():
            print(type)
            for res in data[type]:
                print(res["id"])

    def add_resource(self):
        plan_id = self.get_id_by_name(self.args.name)
        if not plan_id:
            return
        if self.args.volume:
            res_ins = block.Volume(self.args, self.token_pack)
            vol_ids = []
            for name in self.args.volume:
                id = res_ins.get_id_by_name(name)
                if not id:
                    log.error(f"Get volume {name} failed!")
                    continue
                log.info(f"Tag volume {name} with plan-{plan_id}.")
                vol_ids.append(id)
        if self.args.instance:
            res_ins = compute.Instance(self.args, self.token_pack)
            ins_ids = []
            for name in self.args.instance:
                id = res_ins.get_id_by_name(name)
                if not id:
                    log.error(f"Get instance {name} failed!")
                    continue
                log.info(f"Tag instance {name} with plan-{plan_id}.")
                ins_ids.append(id)
        url = f"{self.url}/{plan_id}/resource"
        data = {"resource": {}}
        if self.args.volume:
            data["resource"]["volume_ids"] = vol_ids
        if self.args.instance:
            data["resource"]["instance_ids"] = ins_ids
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def remove_resource(self):
        plan_id = self.get_id_by_name(self.args.name)
        if not plan_id:
            return
        if self.args.volume:
            res_ins = block.Volume(self.args, self.token_pack)
            id = res_ins.get_id_by_name(self.args.volume)
            if not id:
                log.error(f"Get volume {self.args.volume} failed!")
                return
            log.info(f"Untag volume {self.args.volume} with plan-{plan_id}.")
        if self.args.instance:
            res_ins = compute.Instance(self.args, self.token_pack)
            id = res_ins.get_id_by_name(self.args.instance)
            if not id:
                log.error(f"Get instance {self.args.instance} failed!")
                return
            log.info(f"Untag instance {self.args.instance}" \
                    f" with plan-{plan_id}.")
        url = f"{self.url}/{plan_id}/resource/{id}"
        resp = self.send_req("delete", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class BackupPlan(PlanBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "backup_plan"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/plan/backup-plan"
        else:
            svc_url = get_svc_url(token_pack, "cms-plan")
            self.url = f"{svc_url}/backup-plan"

    def create(self):
        res = {"name": self.args.name,
                "resource_type": self.args.resource_type,
                "schedule": self.args.schedule,
                "retention": self.args.retention,
                "credential_name": self.args.credential_name,
                "credential_secret": self.args.credential_secret}
        if self.args.copy_zone and self.args.copy_project:
            res["copy_zone"] = self.args.copy_zone
            res["copy_project"] = self.args.copy_project
        if self.args.incremental:
            res["incremental"] = self.args.incremental
        resp = self.send_req("post", self.url, self.headers,
                data={self.type: res})
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class SnapshotPlan(PlanBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "snapshot_plan"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/plan/snapshot-plan"
        else:
            svc_url = get_svc_url(token_pack, "cms-plan")
            self.url = f"{svc_url}/snapshot-plan"

    def create(self):
        res = {"name": self.args.name,
                "resource_type": self.args.resource_type,
                "schedule": self.args.schedule,
                "retention": self.args.retention,
                "credential_name": self.args.credential_name,
                "credential_secret": self.args.credential_secret}
        resp = self.send_req("post", self.url, self.headers,
                data={self.type: res})
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


arg_schema = {
    "backup-plan": {
        "res-class": BackupPlan,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--resource-type",
                "attr": {"required": True}
            },
            {
                "name": "--schedule",
                "attr": {"required": True}
            },
            {
                "name": "--retention",
                "attr": {"required": True}
            },
            {
                "name": "--credential-name",
                "attr": {"required": True}
            },
            {
                "name": "--credential-secret",
                "attr": {"required": True}
            },
            {
                "name": "--incremental",
                "attr": {"action": "store_true"}
            },
            {"name": "--copy-zone"},
            {"name": "--copy-project"}
        ],
        "delete": [
            {"name": "name"}
        ],
        "execute": [
            {"name": "name"}
        ],
        "list-resource": [
            {"name": "name"}
        ],
        "add-resource": [
            {"name": "name"},
            {
                "name": "--volume",
                "attr": {"action": "append"},
            },
            {
                "name": "--instance",
                "attr": {"action": "append"}
            }
        ],
        "remove-resource": [
            {"name": "name"},
            {
                "name": "--resource",
                "attr": {
                    "required": True
                }
            }
        ]
    },
    "snapshot-plan": {
        "res-class": SnapshotPlan,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--resource-type",
                "attr": {"required": True}
            },
            {
                "name": "--schedule",
                "attr": {"required": True}
            },
            {
                "name": "--retention",
                "attr": {"required": True}
            },
            {
                "name": "--credential-name",
                "attr": {"required": True}
            },
            {
                "name": "--credential-secret",
                "attr": {"required": True}
            }
        ],
        "delete": [
            {"name": "name"}
        ],
        "execute": [
            {"name": "name"}
        ],
        "stop": [
            {"name": "name"}
        ],
        "start": [
            {"name": "name"}
        ],
        "list-resource": [
            {"name": "name"}
        ],
        "add-resource": [
            {"name": "name"},
            {
                "name": "--volume",
                "attr": {"action": "append"},
            },
            {
                "name": "--instance",
                "attr": {"action": "append"}
            }
        ],
        "remove-resource": [
            {"name": "name"},
            {"name": "--volume"},
            {"name": "--instance"}
        ]
    }
}

