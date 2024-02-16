import asyncio
import logging
from common import util, config
from common.resource_base import ResourceBase
from common.rbd import RBD
from db import db
from backup.instance_snapshot import InstanceSnapshot
from openstack.cinder import Volume as OSVolume
from openstack.nova import Instance as OSInstance
from openstack import os_util

log = logging.getLogger("uvicorn")


class Instance(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="volume")

    async def rh_post_action(self, id, c_req):
        body = await c_req.json()
        action = list(body.keys())[0]
        if action == "rollback":
            return await self.action_rollback(id, body[action])
        msg = f"Invalid action {action}!"
        return {"status": 400, "data": {"message": msg}}

    async def action_rollback(self, id, args):
        ss_id = args["snapshot_id"]
        rbd = RBD()
        log.info(f"Action rollback instance {id} to snapshot {ss_id}.")
        ins = await OSInstance(self.token_pack).get_obj(id)
        if not ins:
            return {"status": 404}
        if ins["status"] != "SHUTOFF":
            msg = f"Instance {ins['id']} is not SHUTOFF!"
            return {"status": 409, "data": {"message": msg}}
        ins_vol_snapshots = await db.get("instance_volume_snapshot",
                {"instance_snapshot_id": ss_id})
        for ins_vol_snapshot in ins_vol_snapshots:
            vol_ss_id = ins_vol_snapshot["id"]
            vol_id = ins_vol_snapshot["volume_id"]
            vol = await OSVolume(self.token_pack).get_obj(vol_id)
            if not vol:
                log.error(f"Volume {vol_id} not found!")
                continue
            pool = await os_util.get_pool_by_volume_type(vol["volume_type"])
            spec = f"{pool}/volume-{vol_id}@snapshot-{vol_ss_id}"
            log.info(f"Rollback to snapshot {spec}.")
            await rbd.rollback_snapshot(pool, f"volume-{vol_id}",
                    f"snapshot-{vol_ss_id}")
        return {"status": 200}

