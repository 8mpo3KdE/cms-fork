import logging

import compute
import network
import util
from client.common import ResourceBase
from client.common import get_svc_url

log = logging.getLogger("cms")


class NFS(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/nfs"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def get_disk_id(self, cluster_id, disk_name):
        if util.is_uuid(disk_name):
            return disk_name
        url = f"{self.url}/{cluster_id}/disk"
        resp = self.send_req("get", url, self.headers)
        for disk in resp.json()["disks"]:
            if disk["name"] == disk_name:
                return disk["id"]
        print(f"ERROR: Disk $disk_name is not foune!")

    def list_disk(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/disk"
        resp = self.send_req("get", url, self.headers)
        if resp and (resp.status_code == 200):
            objs = resp.json()["disks"]
            util.output(self.args, objs)
        else:
            print(f"RC: {resp.status_code}")
            print(f"Response: {resp.text}")

    def add_disk(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/disk"
        data = {"disk": {
                "name": self.args.disk_name,
                "size": self.args.size,
                "exported": self.args.exported}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def extend_disk(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        did = self.get_disk_id(id, self.args.disk_name)
        if not did:
            return
        url = f"{self.url}/{id}/disk/{did}/action"
        data = {"extend": {"size": self.args.size}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def remove_disk(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        did = self.get_disk_id(id, self.args.disk_name)
        if not did:
            return
        url = f"{self.url}/{id}/disk/{did}"
        resp = self.send_req("delete", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def list_directory(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/directory"
        resp = self.send_req("get", url, self.headers)
        if resp and (resp.status_code == 200):
            objs = resp.json()["directories"]
            print(objs)
        else:
            print(f"RC: {resp.status_code}")
            print(f"Response: {resp.text}")

    def add_directory(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        did = self.get_disk_id(id, self.args.disk)
        if not did:
            return
        url = f"{self.url}/{id}/disk/{did}/directory"
        data = {"directory": {
                "name": self.args.directory_name}}
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def remove_directory(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        did = self.get_disk_id(id, self.args.disk)
        if not did:
            return
        url = f"{self.url}/{id}/disk/{did}/directory/{self.args.directory_name}"
        resp = self.send_req("delete", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Kubernetes(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/kubernetes"
        else:
            svc_url = get_svc_url(token_pack, "cms-builder")
            self.url = f"{svc_url}/kubernetes"

    def create(self):
        params = {"name": self.args.name,
                "credential_name": self.args.cms_credential_name,
                "credential_secret": self.args.cms_credential_secret}
        map = {"control_size": self.args.control_size,
                "domain": self.args.domain,
                "api_access": self.args.api_access,
                "service_access": self.args.service_access,
                "api_address": self.args.api_address,
                "ingress_address": self.args.ingress_address,
                "pod_address_block": self.args.pod_address_block,
                "service_address_block": self.args.service_address_block,
                "node_subnet_address": self.args.node_subnet_address,
                "node_subnet_id": self.args.node_subnet,
                "corp_gateway_address": self.args.corp_gateway_address,
                "public_gateway_address": self.args.public_gateway_address,
                "internal_api_address": self.args.internal_api_address,
                "internal_ingress_address": self.args.internal_ingress_address,
                "security_group_id": self.args.security_group,
                "version": self.args.version}
        for name in map.keys():
            if map[name]:
                params[name] = map[name]
        resp = self.send_req("post", self.url, self.headers,
                {"cluster": params})
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def set(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}"
        params = {"status": self.args.status}
        resp = self.send_req("put", url, self.headers, {"cluster": params})
        print(f"RC: {resp.status_code}")

    def add_worker(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        url = f"{self.url}/{id}/worker"
        params = {"count": self.args.count,
                "spec_id": spec_id}
        resp = self.send_req("post", url, self.headers, {"worker": params})
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def get_config(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/config"
        resp = self.send_req("get", url, self.headers)
        if resp.status_code == 200:
            print(yaml.dump(resp.json(), default_flow_style = False))
        else:
            print(f"RC: {resp.status_code}")

    def list_worker(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/worker"
        resp = self.send_req("get", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class MariaDB(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/mariadb"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        if self.args.volume_size:
            res["volume_size"] = self.args.volume_size
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class PostgreSQL(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/postgresql"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        if self.args.volume_size:
            res["volume_size"] = self.args.volume_size
        if self.args.version:
            res["version"] = self.args.version
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Redis(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/redis"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        if self.args.volume_size:
            res["volume_size"] = self.args.volume_size
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def extend(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        data = {"extend_volume": {"size": self.args.size}}
        url = f"{self.url}/{id}/action"
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class RabbitMQ(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/rabbitmq"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Kafka(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/kafka"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


class Harbor(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "cluster"
        svc_url = get_svc_url(token_pack, "cms-builder")
        self.url = f"{svc_url}/harbor"

    def create(self):
        spec_id = compute.Spec(self.args, self.token_pack).get_id_by_name(
                self.args.spec)
        if not spec_id:
            return
        subnet_id = network.Subnet(self.args, self.token_pack).get_id_by_name(
                self.args.subnet)
        if not subnet_id:
            return
        res = {"name": self.args.name,
                "cluster_size": self.args.cluster_size,
                "subnet_id": subnet_id,
                "spec_id": spec_id}
        data = {self.type: res}
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
        data = {self.type: res}
        url = f"{self.url}/{id}"
        resp = self.send_req("put", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")


arg_schema = {
    "nfs": {
        "res-class": NFS,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ],
        "list-disk": [
            {"name": "name"}
        ],
        "add-disk": [
            {"name": "name"},
            {
                "name": "--size",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--disk-name",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--exported",
                "attr": {"action": "store_true"}
            }
        ],
        "extend-disk": [
            {"name": "name"},
            {
                "name": "--size",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--disk-name",
                "attr": {
                    "required": True
                }
            }
        ],
        "remove-disk": [
            {"name": "name"},
            {
                "name": "--disk-name",
                "attr": {
                    "required": True
                }
            }
        ],
        "list-directory": [
            {"name": "name"}
        ],
        "add-directory": [
            {"name": "name"},
            {
                "name": "--disk",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--directory-name",
                "attr": {
                    "required": True
                }
            }
        ],
        "remove-directory": [
            {"name": "name"},
            {
                "name": "--disk",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--directory-name",
                "attr": {
                    "required": True
                }
            }
        ]
    },
    "kubernetes": {
        "res-class": Kubernetes,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--control-size"},
            {
                "name": "--api-access",
                "attr": {
                    "choices": ["corp", "public"]
                }
            },
            {
                "name": "--service-access",
                "attr": {
                    "choices": ["corp", "public"]
                }
            },
            {"name": "--version"},
            {"name": "--domain"},
            {"name": "--api-address"},
            {"name": "--ingress-address"},
            {"name": "--pod-address-block"},
            {"name": "--service-address-block"},
            {"name": "--node-subnet-address"},
            {"name": "--node-subnet"},
            {"name": "--corp-gateway-address"},
            {"name": "--public-gateway-address"},
            {"name": "--internal-api-address"},
            {"name": "--internal-ingress-address"},
            {"name": "--security-group"}
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ],
        "add-worker": [
            {"name": "name"},
            {"name": "--count"},
            {"name": "--spec"}
        ],
        "get-config": [
            {"name": "name"}
        ],
        "list-worker": [
            {"name": "name"}
        ]
    },
    "mariadb": {
        "res-class": MariaDB,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "postgresql": {
        "res-class": PostgreSQL,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--version"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "redis": {
        "res-class": Redis,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "extend": [
            {"name": "name"},
            {
                "name": "--size",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "rabbitmq": {
        "res-class": RabbitMQ,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "kafka": {
        "res-class": Kafka,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "harbor": {
        "res-class": Harbor,
        "list": [],
        "list-instance": [
            {"name": "name"}
        ],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--volume-size"},
            {
                "name": "--cluster-size",
                "attr": {
                    "default": 1
                }
            },
            {
                "name": "--subnet",
                "attr": {
                    "required": True
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "required": True
                }
            }
        ],
        "set": [
            {"name": "name"},
            {"name": "--status"}
        ],
        "delete": [
            {"name": "name"}
        ]
    }
}

