import util
from client.common import ResourceBase
from client.common import get_svc_url


class Network(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "network"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/network"
        else:
            self.url = "{}/v2.0/networks".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        data = {"name": self.args.name}
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
            print(resp.json())


class Subnet(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "subnet"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/subnet"
        else:
            self.url = "{}/v2.0/subnets".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        nid = Network(self.args, self.token).get_id_by_name(
                self.args.network)
        if not nid:
            return
        data = {"name": self.args.name,
                "network_id": nid,
                "cidr": self.args.range}
        if self.args.gateway:
            data["gateway_ip"] = self.args.gateway
        if self.args.no_gateway:
            data["gateway_ip"] = "none"
        if self.args.host_route:
            l = []
            for route in self.args.host_route:
                d = {}
                for i in route.split(","):
                    d[i.split("=")[0]] = i.split("=")[1]
                l.append(d)
            data["host_routes"] = l
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
            print(resp.json())


class Port(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "port"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/port"
        else:
            self.url = "{}/v2.0/ports".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        data = {}
        data["name"] = self.args.name
        nid = Network(self.args, self.token).get_id_by_name(
                self.args.network)
        if not nid:
            return
        data["network"] = nid
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
                print(resp.json())


class Router(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "router"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/route"
        else:
            self.url = "{}/v2.0/routers".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        data = {"name": self.args.name}
        data["device"] = self.args.device
        if self.args.device == "virtual-gateway":
            if (not self.args.version) or (not self.args.spec):
                print("ERROR: Argument version and spec are reuqired " \
                        "for device virtual-gateway!")
                return
            data["device_info"] = {"version": self.args.version,
                    "spec": self.args.spec}
        if self.args.external:
            data["externals"] = [
                    {"name": e, "snat": True} for e in self.args.external]
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
            print(resp.json())

    def set(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        ext = {}
        if self.args.external:
            ext["name"] = self.args.external
        if self.args.snat:
            ext["snat"] = self.args.snat
        data = {}
        if ext:
            data["external"] = ext
        if self.args.name:
            data["name"] = self.args.name
        resp = self.send_req("put", self.url + f"/{id}", self.headers, data)
        if resp and (resp.status_code == 200):
            print(resp.json())


class SecurityGroup(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "security_group"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/security-group"
        else:
            self.url = "{}/v2.0/security-groups".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        data = {"name": self.args.name}
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
                print(resp.json())


class SecurityGroupRule(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "security_group_rule"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/network/security-group-rule"
        else:
            self.url = "{}/v2.0/security-group-rules".format(
                    get_svc_url(token_pack, "network"))

    def create(self):
        sg_id = security_group(self.args, self.token).get_id_by_name(
                self.args.security_group)
        if not sg_id:
            return
        data = {"security_group": sg_id,
                "direction": self.args.direction}
        if self.args.protocol:
            data["protocol"] = self.args.protocol
        if self.args.ip_version:
            data["ip_version"] = self.args.ip_version
        if self.args.port:
            p = str(self.args.port).split(":")
            if len(p) == 1:
                data["port_min"] = int(p[0])
                data["port_max"] = int(p[0])
            else:
                data["port_min"] = int(p[0])
                data["port_max"] = int(p[1])
        if self.args.remote_ip:
            data["remote_ip"] = self.args.remote_ip
        if self.args.remote_group:
            sg_id = security_group(self.args, self.token).get_id_by_name(
                    self.args.remote_security)
            if not sg_id:
                return
            data["remote_group"] = sg_id
        resp = self.send_req("post", self.url, self.headers, data)
        if resp and (resp.status_code == 201):
                print(resp.json())


arg_schema = {
    "network": {
        "res-class": Network,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "subnet": {
        "res-class": Subnet,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--network",
                "attr": {"required": True}
            },
            {
                "name": "--range",
                "attr": {
                    "required": True,
                    "metavar": "<CIDR>"
                }
            },
            {"name": "--gateway"},
            {
                "name": "--no-gateway",
                "attr": {"action": "store_true"}
            },
            {
                "name": "--host-route",
                "attr": {
                    "action": "append",
                    "metavar": "destination=<CIDR>,nexthop=<address>"
                }
            }
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "port": {
        "res-class": Port,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--network",
                "attr": {"required": True}
            }
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "router": {
        "res-class": Router,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {
                "name": "--device",
                "attr": {
                    "choices": ["logical-router", "virtual-gateway"],
                    "required": True
                }
            },
            {
                "name": "--external",
                "attr": {
                    "choices": ["public", "corp"],
                    "action": "append",
                }
            },
            {
                "name": "--version",
                "attr": {
                    "help": "Version of virtual gateway",
                }
            },
            {
                "name": "--spec",
                "attr": {
                    "help": "VM spec for virtual gateway",
                }
            }
        ],
        "set": [
            {"name": "name"},
            {
                "name": "--name",
                "attr": {
                    "dest": "new_name"
                }
            },
            {
                "name": "--external",
                "attr": {
                    "choices": ["public", "corp"]
                }
            },
            {
                "name": "--snat",
                "attr": {
                    "action": "store_true",
                }
            }
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "security-group": {
        "res-class": SecurityGroup,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"}
        ],
        "delete": [
            {"name": "name"}
        ]
    },
    "security-group-rule": {
        "res-class": SecurityGroupRule,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {
                "name": "--security-group",
                "attr": {"required": True}
            },
            {
                "name": "--direction",
                "attr": {
                    "choices": ["ingress", "egress"],
                    "required": True
                }
            },
            {
                "name": "--ip-version",
                "attr": {"choices": [4, 6]}
            },
            {"name": "--protocol"},
            {"name": "--port"},
            {"name": "--remote-ip"},
            {"name": "--remote-group"}
        ],
        "delete": [
            {"name": "name"}
        ]
    }
}

