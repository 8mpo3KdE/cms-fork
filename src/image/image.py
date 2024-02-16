import os
import asyncio
import logging
import json
import urllib

import aiohttp
import aiofiles

from common import util, quota
from common.config import config, zone_conf
from common.resource_base import ResourceBase
from common.rbd import RBD
from db import db
from objects import FileFormat, ImageFormat, Visibility
from openstack.keystone import Auth, Project
from openstack.glance import Image as OSImage
from openstack.cinder import Volume as OSVolume
from openstack.nova import Instance as OSInstance
from openstack import os_util

log = logging.getLogger("uvicorn")
staging_path = "/opt/image-staging"


class Image(ResourceBase):
    def __init__(self, token_pack):
        super().__init__(token_pack, res_name="image")
        self.action_map = {"copy": self.action_copy}
        self.quota = quota.Quota(self.project_id, config, db, self.token_pack)

    async def get_obj_list(self, query=None):
        q = {"deleted": False,
                "project_id": self.project_id}
        objs = await db.get(self.table_name, q)
        if "all_projects" in query:
            query.pop("all_projects")
        os_objs = await OSImage(self.token_pack).get_obj_list(query=query)
        return objs + os_objs

    async def rh_post(self, req):
        req = req[self.res_name]
        usage = await self.quota.get_osp_resource_usage("image_size_total")
        if await self.quota.check_quota_limits("glance", "image_size_total",
                usage):
            msg = f"Image usage {usage} exceeds the limit!"
            log.error(msg)
            return {"status": 413, "data": {"message": msg}}
        if req["source_zone"]:
            image = {"name": req["name"],
                "project_id": req["project_id"],
                "owner": req["project_id"],
                "size": req["size"],
                "container_format": req["file_format"],
                "disk_format": req["image_format"],
                "visibility": req["visibility"],
                "status": "importing"}
            await db.add(self.table_name, image)
            image["usage"] = req["usage"]
            task = asyncio.create_task(self.task_import_progress(image),
                    name=image["id"])
            task.add_done_callback(util.task_done_cb)
            data = {self.res_name: {"id": image["id"]}}
            return {"status": 202, "data": data}
        elif req["link"]:
            task_func = self.task_add_image_from_link
        elif req["resource_type"] and req["resource_id"]:
            task_func = self.task_add_image_from_res
        else:
            msg = f"Bad request for creating image."
            return {"status": 400, "data": {"message": msg}}
        params = {"name": req["name"],
                "container_format": FileFormat.BARE,
                "disk_format": ImageFormat.RAW,
                "visibility": req["visibility"]}
        resp = await OSImage(self.token_pack).post(params)
        if resp["status"] != 201:
            if resp["status"] == 413:
                resp["data"] = {"message": "Image count reach the limit."}
            return resp
        task = asyncio.create_task(task_func(resp["data"]["id"], req))
        task.add_done_callback(util.task_done_cb)
        return resp

    async def rh_put(self, id, req_data):
        req = req_data[self.res_name]
        if req["name"]:
            params = [{"op": "replace",
                    "path": "/name",
                    "value": req["name"]}]
            resp = await OSImage(self.token_pack).patch(id, params)
            if resp["status"] == 403:
                resp["data"] = {"message": "Operation is not permitted!"}
            return resp
        if req["source_zone"]:
            objs = await db.get(self.table_name, {"id": id})
            if not objs:
                return {"status": 404}
            task = asyncio.create_task(self.task_add_imported_image(objs[0]))
            task.add_done_callback(util.task_done_cb)
        return {"status": 200, "data": {self.res_name: {"id": id}}}

    async def rh_delete(self, id):
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, id, update)
        resp = await OSImage(self.token_pack).delete(id)
        if resp["status"] in [204, 404]:
            return {"status": 202, "data": {self.res_name: {"id": id}}}
        else:
            return resp

    async def action_copy(self, id, args):
        log.info(f"Action copy image {id}.")
        for arg in args:
            task = asyncio.create_task(self.task_copy_image(id, arg))
            task.add_done_callback(util.task_done_cb)
        return {"status": 202}

    def get_file_name_from_url(self, url):
        name = url.split("?")[0].split("/")[-1]
        name = urllib.parse.unquote(name)
        return name

    async def download_src_file(self, url, work_space):
        name = self.get_file_name_from_url(url)
        src_file = f"{work_space}/{name}"
        max_download_attempts = 10
        # NOTE: Change timeout from 5 minutes (default setting) to unlimited.
        # However, set the sock_connect and sock_read timeouts just in case
        # no connection is made or no data is read for a certain period of
        # time. Apparently people have been having downloading large files
        # with aiohttp due to the 5-minute default timeout.
        # This is different from the synchronous requests package,
        # which sets the default timeout to None.
        # See the following references:
        # - GitHub Issue: https://github.com/aio-libs/aiohttp/issues/2249
        # - StackOverflow.com Q: https://stackoverflow.com/a/67661000
        # - aiohttp official documentation:
        #   https://docs.aiohttp.org/en/stable/client_reference.html
        # - Requests timeouts:
        #   https://requests.readthedocs.io/en/stable/user/quickstart/#timeouts
        timeout_policy = aiohttp.ClientTimeout(
            total=None,
            sock_connect=10,
            sock_read=10
        )
        for attempt_count in range(1, max_download_attempts + 1):
            log.info(f"Download {name} from {url}, try #{attempt_count}.")
            try:
                async with aiohttp.ClientSession(
                        timeout=timeout_policy) as session:
                    async with session.get(url) as resp:
                        log.debug(f"Download resp status: {resp.status}")
                        log.debug(f"Download resp headers: {resp.headers}")
                        log.debug(f"Download resp data: {resp.text}")
                        log.debug(f"Downloading to: {src_file}")
                        async with aiofiles.open(src_file, "wb") as file:
                            async for chunk, _ in resp.content.iter_chunks():
                                await file.write(chunk)
                log.info(f"Download {name} from {url} is completed.")
                return name
            except asyncio.TimeoutError as ex:
                log.error(f"Image download timeout #{attempt_count}. {ex}")
                if attempt_count == max_download_attempts:
                    return
            except Exception as ex:
                log.error(f"Image download failed #{attempt_count}. {ex}")
                if attempt_count == max_download_attempts:
                    return

    async def convert_file(self, input_filepath, img_format):
        log.info(f"Convert {input_filepath} from {img_format} to raw.")
        output_filepath = f"{input_filepath.rsplit('.', 1)[0]}.raw"
        cmd = f"{QEMU_PATH} convert -O raw {input_filepath} {output_filepath}"
        await util.exec_cmd(cmd)
        return output_filepath

    async def extract_src_file(self, src_file_name, work_space, file_format):
        log.info(f"Extract file {src_file_name} as {file_format}.")

        if file_format == FileFormat.BARE:
            return src_file_name
        elif file_format == FileFormat.TGZ:
            cmd = f"cd {work_space}; tar -xzf {src_file_name}"
            image_file_name = src_file_name.rstrip(".tgz")
        elif file_format == FileFormat.GZIP:
            cmd = f"cd {work_space}; gzip -dfv {src_file_name}"
            image_file_name = src_file_name.rstrip(".gz")
        elif file_format == FileFormat.BZIP:
            cmd = f"cd {work_space}; bz2 -d {src_file_name}"
            image_file_name = src_file_name.rstrip(".bz2")
        else:
            return
        if await util.exec_cmd(cmd):
            return
        if os.path.exists(f"{work_space}/{image_file_name}"):
            return image_file_name

    async def save_image(self, image_name, image_file_name, work_space):
        file_name = f"{work_space}/{image_file_name}"
        #cmd = f"qemu-img info --output=json {file_name}"
        #rc, output = await util.exec_cmd(cmd, output=True)
        #metadata = json.loads(output)
        #image_format = metadata["format"]
        log.info("Convert image file to Ceph.")
        cmd = f"qemu-img convert -O raw {file_name} rbd:image/{image_name}"
        if await util.exec_cmd(cmd):
            return
        await RBD().create_snapshot("image", image_name, "snap")
        fsid = self.get_ceph_cluster_id()
        image_url = f"rbd://{fsid}/image/{image_name}/snap"
        return image_url

    async def update_image_location(self, image_id, location):
        log.info(f"Update image {image_id} location {location}.")
        svc_token_pack = await Auth().get_svc_token(zone_conf)
        params = [{"op": "add",
                "path": "/locations/1",
                "value": {
                    "url": location,
                    "metadata": {"store": "rbd"}}}]
        resp = await OSImage(svc_token_pack).patch(image_id, params)
        return resp

    def get_ceph_cluster_id(self):
        fsid = ""
        with open("/etc/ceph/ceph.conf", "r") as file:
            for line in file:
                if "fsid" in line:
                    fsid = line.split("=")[1].strip()
                    break
        return fsid

    async def task_add_image_from_link(self, id, req):
        log.info(f"Task add image {id} from link.")
        url = str(req["link"])
        work_space = f"{staging_path}/{id}"
        await util.exec_cmd(f"mkdir -p {work_space}")
        src_file_name = await self.download_src_file(url, work_space)
        if not src_file_name:
            await util.exec_cmd(f"rm -fr {work_space}")
            return
        image_file_name = await self.extract_src_file(src_file_name,
                work_space, req["file_format"])
        if not image_file_name:
            await util.exec_cmd(f"rm -fr {work_space}")
            return
        image_url = await self.save_image(id, image_file_name, work_space)
        await self.update_image_location(id, image_url)
        await util.exec_cmd(f"rm -fr {work_space}")
        for copy in req["copies"]:
            await self.task_copy_image(id, copy)
        log.info(f"Task add image {id} from link is done.")

    async def task_add_image_from_res(self, id, req):
        res_id = req["resource_id"]
        res_type = req["resource_type"]
        log.info(f"Task add image {id} from {res_type} {res_id}.")
        vol_type = None
        if res_type == "instance":
            res = await OSInstance(self.token_pack).get_obj(res_id)
            if not res:
                log.error(f"Get instance {res_id} failed!")
                return
            if res["image"]:
                image_type = "instance"
                image_id = res_id
            else:
                vol_id = res["os-extended-volumes:volumes_attached"][0]["id"]
                volume = await OSVolume(self.token_pack).get_obj(vol_id)
                if not volume:
                    log.error(f"Get volume {vol_id} failed!")
                    return
                image_type = "volume"
                image_id = volume["id"]
                vol_type = volume["volume_type"]
        elif res_type == "volume":
            res = await OSVolume(self.token_pack).get_obj(res_id)
            if not res:
                log.error(f"Get volume {res_id} failed!")
                return
            image_type = "volume"
            image_id = res["id"]
            vol_type = res["volume_type"]
        else:
            log.error(f"Invalid resource type {res_type}!")
            return
        if image_type == "instance":
            log.error(f"Not supported to create image from instance image!")
            return
        rbd = RBD()
        pool = await os_util.get_pool_by_volume_type(vol_type)
        await rbd.create_snapshot(pool, f"volume-{image_id}", "clone")
        await rbd.clone(f"{pool}/volume-{image_id}@clone", f"image/{id}")
        await rbd.flatten("image", id)
        await rbd.create_snapshot("image", id, "snap")
        await rbd.delete_snapshot(pool, f"volume-{image_id}", "clone")
        fsid = self.get_ceph_cluster_id()
        location = f"rbd://{fsid}/image/{id}/snap"
        await self.update_image_location(id, location)
        for copy in req["copies"]:
            await self.task_copy_image(id, copy)
        log.info(f"Task add image from res is done.")

    async def task_add_imported_image(self, image):
        image_id = image["id"]
        log.info(f"Add imported image {image_id}.")
        for task in asyncio.all_tasks():
            if task.get_name() == image_id:
                log.info(f"Cancel progress task {image_id}")
                task.cancel()
                break
        params = {"name": image["name"],
                "container_format": image["container_format"],
                "disk_format": image["disk_format"],
                "visibility": image["visibility"],
                "owner": image["owner"]}
        resp = await OSImage(self.token_pack).post(params)
        if resp["status"] != 201:
            log.error(f"Add imported image failed. {resp}")
            return
        os_image_id = resp["data"]["id"]
        await RBD().mv("image", image_id, os_image_id)
        fsid = self.get_ceph_cluster_id()
        location = f"rbd://{fsid}/image/{os_image_id}/snap"
        await self.update_image_location(os_image_id, location)
        update = {"status": "deleted", "deleted": True}
        await db.update(self.table_name, image_id, update)
        log.info(f"Task add imported image is done.")

    async def get_remote_auth(self, zone_name):
        log.info(f"Auth from remote zone {zone_name}.")
        remote_zone_conf = config[f"zone.{zone_name}"]
        token_pack = await Auth().get_svc_token(remote_zone_conf)
        if not token_pack:
            log.error(f"Auth from zone {zone_name} failed!")
            return None, None
        for c in token_pack["catalog"]:
            if c["type"] == "cms-image":
                break
        else:
            log.error(f"No CMS image endpoint from zone {zone_name}!")
            return None, None
        svc_url = c["endpoints"][0]["url"] + "/image"
        return token_pack, svc_url

    async def task_copy_image(self, id, args):
        svc_token_pack = await Auth().get_svc_token(zone_conf)
        resp = await OSImage(svc_token_pack).get(id)
        if resp["status"] != 200:
            log.error(f"Copy image {id} not found!")
            return
        if not args["image_name"]:
            args["image_name"] = resp["data"]["name"]
        if not args["project_name"]:
            project = await Project(svc_token_pack).get_obj(
                    resp["data"]["owner"])
            args["project_name"] = project["name"]
        image_id = id
        copy_zone = args["zone_name"]
        rbd = RBD()
        log.info(f"Task copy image {image_id} to {args}.")
        token_pack, svc_url = await self.get_remote_auth(copy_zone)
        if not token_pack:
            return
        project_id = await Project(token_pack).get_id_by_name(
                args["project_name"])
        if not project_id:
            log.error(f"Get project {args['project_name']} failed!")
            return
        log.info(f"Create remote image in {copy_zone}.")
        usage = await rbd.get_usage("image", image_id)
        headers = {"x-auth-token": token_pack["token"],
                "content-type": "application/json"}
        params = {"name": args["image_name"],
                "project_id": project_id,
                "visibility": Visibility.PRIVATE,
                "file_format": FileFormat.BARE,
                "image_format": ImageFormat.RAW,
                "source_zone": config["DEFAULT"]["zone"],
                "usage": usage}
        resp = await util.send_req("post", svc_url, headers,
                data={self.res_name: params})
        if resp["status"] != 202:
            log.error(f"Create remote image in {copy_zone} failed!")
            log.debug(f"status: {resp['status']}, data: {resp['data']}")
            return
        copy_id = resp["data"][self.res_name]["id"]
        log.info(f"Copy image to remote image {copy_id}.")
        args = "--export-format 2 --no-progress"
        cmd = f"rbd export {args} image/{image_id} -" \
                f" | rbd --cluster {copy_zone} --id infra" \
                f" import {args} - image/{copy_id}"
        rc = await util.exec_cmd(cmd)
        if rc:
            log.error(f"Copy image failed {rc}!")
            return
        log.info(f"Update remote image {copy_id}.")
        token_pack, svc_url = await self.get_remote_auth(copy_zone)
        if not token_pack:
            return
        headers = {"x-auth-token": token_pack["token"],
                    "content-type": "application/json"}
        params = {"source_zone": config["DEFAULT"]["zone"]}
        res_url = f"{svc_url}/{copy_id}"
        resp = await util.send_req("put", res_url, headers,
                data={self.res_name: params})
        if resp["status"] != 200:
            log.error(f"Set remote image status error!")
            return
        log.info(f"Task copy image {image_id} to {copy_zone} is done.")

    async def task_import_progress(self, image):
        rbd = RBD()
        image_id = image["id"]
        src_usage = image["usage"]
        usage = 0
        while usage < src_usage:
            await asyncio.sleep(5)
            usage = await rbd.get_usage("image", image_id)
            if not usage:
                continue
            update = {"status": "importing {:.2%}".format(usage/src_usage)}
            await db.update(self.table_name, image_id, update)

    async def rh_get_quota(self):
        log.debug(f"Get image quota for project: {self.project_id}")
        reg_limits = await self.quota.get_quota_all_default_limits("glance")
        limits = await self.quota.get_quota_all_limits("glance")
        reg_quote_result = {}
        quota_result = {}
        if reg_limits is None:
            return {"status": 404,
                    "data": {"message": "There is no registered limit."}}
        for reg_limit in reg_limits:
            quota_key = reg_limit.get("resource_name")
            quota_value = reg_limit.get("default_limit")
            reg_quote_result[quota_key] = quota_value
        if limits is not None:
            for limit in limits:
                quota_key = limit.get("resource_name")
                quota_value = limit.get("resource_limit")
                quota_result[quota_key] = quota_value
        # Get usage of image under this project.
        image_usage = {}
        query = {"owner": self.project_id}
        resp_data = await OSImage(self.token_pack).get_list(query=query)
        if not resp_data or resp_data.get("status") != 200:
            log.info(f"Can't get the usage of image under this project.")
        else:
            image_count = 0
            image_size_count = 0
            for image in resp_data.get("data").get("images"):
                image_count = image_count + 1
                if image.get("size") is None:
                    continue
                image_size_count = image_size_count + image.get("size")
            image_usage["count"] = image_count
            image_usage["size"] = image_size_count / (1024**2)
        return {"status": 200,
                "data": {"registered_limits": reg_quote_result,
                         "limits": quota_result,
                         "usage": image_usage}}

