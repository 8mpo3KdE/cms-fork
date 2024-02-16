import logging

from common import util
from common.resource_base_os import ResourceBaseOS

log = logging.getLogger("uvicorn")


class LoadBalancer(ResourceBaseOS):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="loadbalancer",
                svc_name="load-balancer")
        self.svc_url = self.svc_url + "/v2"
        self.res_url = f"{self.svc_url}/lbass/{self.res_name}s"

