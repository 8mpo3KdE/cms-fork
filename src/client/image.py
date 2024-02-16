from client.common import ResourceBase
from client.common import get_svc_url
import block
import compute


class Image(ResourceBase):
    def __init__(self, args, token_pack):
        super().__init__(args, token_pack)
        self.type = "image"
        if args.cms_api_url:
            self.url = f"{args.cms_api_url}/v1/image/image"
        else:
            self.url = "{}/image".format(get_svc_url(token_pack, "cms-image"))

    def create(self):
        params = {"name": self.args.name}
        if self.args.link:
            params["link"] = self.args.link
        if self.args.instance:
            params["resource_type"] = "instance"
            ins = compute.Instance(self.args, self.token_pack)
            params["resource_id"] = ins.get_id_by_name(self.args.instance)
        if self.args.volume:
            params["resource_type"] = "volume"
            ins = block.Volume(self.args, self.token_pack)
            params["resource_id"] = ins.get_id_by_name(self.args.volume)
        resp = self.send_req("post", self.url, self.headers,
                {self.type: params})
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

    def copy(self):
        id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}/action"
        data = {"copy": [{
                   "zone_name": self.args.zone,
                   "project_name": self.args.project,
                   "image_name": self.args.name}
               ]}
        if self.args.new_name:
            data["copy"][0]["image_name"] = self.args.new_name
        resp = self.send_req("post", url, self.headers, data)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

arg_schema = {
    "image": {
        "res-class": Image,
        "list": [],
        "show": [
            {"name": "name"}
        ],
        "create": [
            {"name": "name"},
            {"name": "--link"},
            {"name": "--instance"},
            {"name": "--volume"}
        ],
        "copy": [
            {"name": "name"},
            {
                "name": "--zone",
                "attr": {"required": True}
            },
            {
                "name": "--project",
                "attr": {"required": True}
            },
            {
                "name": "--name",
                "attr": {
                    "dest": "new_name"
                }
            },
        ],
        "delete": [
            {"name": "name"}
        ]
    }
}

