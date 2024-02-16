import asyncio
import logging

from common import util, config
from openstack.keystone import Auth
from openstack.cinder import VolumeType, SchedulerStats

log = logging.getLogger("uvicorn")


async def get_pool_by_volume_type(vol_type_name):
    svc_token_pack = await Auth().get_svc_token(config.zone_conf)
    vol_types = await VolumeType(svc_token_pack).get_obj_list()
    if not vol_types:
        log.error(f"Get volume types failed!")
        return
    for vol_type in vol_types:
        if vol_type["name"] == vol_type_name:
            backend_name = vol_type["extra_specs"]["volume_backend_name"]
            break
    else:
        log.error(f"Volume type {vol_type_name} not found!")
        return
    pools = await SchedulerStats(svc_token_pack).get_pool()
    if not pools:
        log.error(f"Get volume scheduler pools failed!")
        return
    for pool in pools:
        cap = pool["capabilities"]
        if cap["volume_backend_name"] == backend_name:
            backend_pool_name = cap["location_info"].split(":")[-1]
            break
    else:
        log.error(f"Backend {backend_name} not found!")
        return
    return backend_pool_name

