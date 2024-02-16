"""
Support quota limit for resources
"""
import logging

from openstack import glance
from openstack.keystone import Limit, RegisteredLimit

log = logging.getLogger("uvicorn")


async def check_resp_data(resp_data, status, error_message):
    if not resp_data or resp_data.get("status") != status:
        log.error(error_message + f" Resp is {resp_data}")
        return True
    return False


class Quota(object):
    def __init__(self, project_id, conf, db, token_pack):
        self.conf = conf
        self.project_id = project_id
        self.db = db
        self.token_pack = token_pack

    async def get_quota_default_limits(self, service_id, resource_name,
            region_id="RegionOne"):
        query = {"service_id": service_id, "resource_name": resource_name,
                "region_id": region_id}
        resp_data = await RegisteredLimit(self.token_pack).get_list(query)
        if await check_resp_data(resp_data, 200,
                f"Get registered limits failed!"):
            return
        def_limit = resp_data.get("data").get("registered_limits")
        if not def_limit:
            return
        return def_limit[0]

    async def get_quota_limits(self, service_id, resource_name,
            region_id="RegionOne"):
        query = {"service_id": service_id, "resource_name": resource_name,
                "region_id": region_id, "project_id": self.project_id}
        resp_data = await Limit(self.token_pack).get_list(query)
        if await check_resp_data(resp_data, 200,
                f"Get limits failed!"):
            return
        def_limit = resp_data.get("data").get("limits")
        if not def_limit:
            return
        return def_limit[0]

    async def check_quota_limits(self, service_name, resource_name, usage):
        service_id = None
        for catalog in self.token_pack.get("catalog"):
            if catalog.get("name") == service_name:
                service_id = catalog.get("id")
        limits = await self.get_quota_default_limits(service_id,
                resource_name)
        project_limits = await self.get_quota_limits(service_id,
                resource_name)
        switch_limit = False
        if project_limits is not None:
            limits = project_limits
            switch_limit = True

        if limits is None:
            return False
        else:
            if switch_limit:
                limits_number = limits.get("resource_limit")
            else:
                limits_number = limits.get("default_limit")

            if limits_number == -1:
                return False
            elif limits_number <= usage:
                return True
        return False

    async def get_resource_usage(self, resource_type):
        query = {"project_id": self.project_id, "deleted": False}
        usage = await self.db.get(resource_type, query)
        return 0 if usage == [] else len(usage)

    async def get_osp_resource_usage(self, resource_name):
        if resource_name == "image_size_total":
            image_size_total = 0
            query = {"owner": self.project_id}
            resp_data = await glance.Image(self.token_pack).get_list(
                    query=query)
            if await check_resp_data(resp_data, 200,
                    f"Get image list failed!"):
                return
            for image in resp_data.get("data").get("images"):
                if image.get("size") is not None:
                    image_size_total += image.get("size")
            return image_size_total // (1024 ** 2)
        return

    async def get_quota_all_default_limits(self, service_name,
            region_id="RegionOne"):
        service_id = None
        for catalog in self.token_pack.get("catalog"):
            if catalog.get("name") == service_name:
                service_id = catalog.get("id")
        query = {"service_id": service_id, "region_id": region_id}
        resp_data = await RegisteredLimit(self.token_pack).get_list(query)
        if await check_resp_data(resp_data, 200,
                f"Get registered limits failed!"):
            return
        reg_limit = resp_data.get("data").get("registered_limits")
        if not reg_limit:
            return
        return reg_limit

    async def get_quota_all_limits(self, service_name, region_id="RegionOne"):
        service_id = None
        for catalog in self.token_pack.get("catalog"):
            if catalog.get("name") == service_name:
                service_id = catalog.get("id")
        query = {"service_id": service_id, "region_id": region_id,
                "project_id": self.project_id}
        resp_data = await Limit(self.token_pack).get_list(query)
        if await check_resp_data(resp_data, 200,
                f"Get limits failed!"):
            return
        limit = resp_data.get("data").get("limits")
        if not limit:
            return
        return limit

