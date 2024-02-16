import asyncio
import logging
import json

from common import util


class RBD(object):
    def __init__(self):
        pass

    async def delete(self, pool, image):
        cmd = f"rbd rm --pool {pool} --image {image}"
        await util.exec_cmd(cmd)

    async def get_size(self, pool, image):
        cmd = f"rbd info --pool {pool} --image {image} --format json"
        rc, output = await util.exec_cmd(cmd, output=True)
        if rc:
            return
        info = json.loads(output)
        return info["size"]

    async def get_usage(self, pool, image):
        cmd = f"rbd du --pool {pool} --image {image} --format json"
        rc, output = await util.exec_cmd(cmd, output=True)
        if rc:
            return 0
        images = json.loads(output)["images"]
        usage = 0
        for image in images:
            usage += image["used_size"]
        return usage

    async def get_parent(self, pool, image):
        cmd = f"rbd info --pool {pool} --image {image} --format json"
        rc, output = await util.exec_cmd(cmd, output=True)
        if rc:
            return
        info = json.loads(output)
        if "parent" in info:
            return info["parent"]

    async def clone(self, parent_snapshot, child_image):
        cmd = f"rbd clone {parent_snapshot} {child_image}"
        await util.exec_cmd(cmd)

    async def deep_copy(self, src_pool, src_image, dst_pool, dst_image):
        cmd = f"rbd deep cp {src_pool}/{src_image} {dst_pool}/{dst_image}"
        await util.exec_cmd(cmd)

    async def flatten(self, pool, image):
        cmd = f"rbd flatten {pool}/{image}"
        await util.exec_cmd(cmd)

    async def mv(self, pool, src, dst):
        cmd = f"rbd mv {pool}/{src} {pool}/{dst}"
        await util.exec_cmd(cmd)

    async def get_snapshot(self, pool, image, name=None):
        cmd = f"rbd snap ls --pool {pool} --image {image} --format json"
        rc, output = await util.exec_cmd(cmd, output=True)
        if rc:
            return
        snapshots = json.loads(output)
        if name:
            for ss in snapshots:
                if ss["name"] == name:
                    return ss
            else:
                return
        return snapshots

    async def create_snapshot(self, pool, image, name, cluster=None, id=None):
        args = ""
        if cluster:
            args = f"--cluster {cluster} --id {id}"
        spec = f"{pool}/{image}@{name}"
        await util.exec_cmd(f"rbd {args} snap create {spec}")
        await util.exec_cmd(f"rbd {args} snap protect {spec}")

    async def delete_snapshot(self, pool, image, name, cluster=None, id=None):
        args = ""
        if cluster:
            args = f"--cluster {cluster} --id {id}"
        spec = f"{pool}/{image}@{name}"
        await util.exec_cmd(f"rbd {args} snap unprotect {spec}")
        await util.exec_cmd(f"rbd {args} snap rm {spec}")

    async def rollback_snapshot(self, pool, image, name):
        spec = f"{pool}/{image}@{name}"
        await util.exec_cmd(f"rbd snap rollback {spec}")

    '''
    import rados
    import rbd
    async def connect(self):
        log.info("Connecting to ceph cluster.")
        ceph_config_file = "/etc/ceph/ceph.conf"
        with rados.Rados(conffile=ceph_config_file) as cluster:
            cluster_id = cluster.get_fsid()
            log.info(f"Connected to cluster {cluster_id}.")
            with cluster.open_ioctx("image") as img_ioctx:
                cmd = ("qemu-img convert -O raw {} rbd:image/{}".format(
                        file_name, image_name))
                if await util.exec_cmd(cmd):
                    return
                with rbd.Image(img_ioctx, image_name) as image:
                    image.create_snap(name="snap")
                    image.protect_snap("snap")
                    # NOTE: Instead of calling a sub-process, another option
                    # would be to use the image.aio_write() method. Unlike the
                    # synchronous write() method, the aio_write() method
                    # requires a 3rd parameter: a completion callback
                    # (passing in a lambda fn seems to work.)
                    # The only documentation I found was in the Ceph source
                    # code. See GitHub link below:
                    # github.com/ceph/ceph/blob/master/src/pybind/rbd/rbd.pyx
                    # - Line 4746 has aio_write() method
                    # - Line 3610 has protect_snap() method
                    #
                    # NOTE: the aio_write() method documentation states that
                    # it is async, but the method declaration is not written
                    # using the async/await keywords in Python.
                    # TODO: determine the implications of this
    '''

