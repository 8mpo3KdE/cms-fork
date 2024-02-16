import logging
import requests
import json

import util

log = logging.getLogger("cms")


def get_svc_url(token_pack, service):
    catalog = token_pack["catalog"]
    url = None
    for svc in catalog:
        if svc["type"] == service:
            for ep in svc["endpoints"]:
                if ep["interface"] == "public":
                    url = ep["url"]
                    break
            break
    return url


class ResourceBase(object):
    def __init__(self, args, token_pack):
        self.token_pack = token_pack
        self.args = args
        self.token = token_pack["token"]
        self.headers = {"x-auth-token": self.token,
                "content-type": "application/json"}
        self.url = None

    def send_req(self, op, url, headers, data=None):
        func = getattr(requests, op)
        resp = None
        log.debug(f"URL: {op} {url}")
        log.debug(f"Request: {data}")
        try:
            if data:
                resp = func(url, headers=self.headers, data=json.dumps(data))
            else:
                resp = func(url, headers=self.headers)
            log.debug(f"Response status: {resp.status_code}")
            log.debug(f"Response data: {resp.text}")
        except Exception as e:
            log.error(e)
        return resp

    def get_objs(self):
        if (hasattr(self, "detail")) and self.detail:
            url = self.url + "/detail"
        else:
            url = self.url
        #url = f"{self.url}?all_tenants=true"
        resp = self.send_req("get", url, self.headers)
        if resp and (resp.status_code == 200):
            return resp.json()[self.type + "s"]

    def get_obj_by_id(self, id):
        url = f"{self.url}/{id}"
        resp = self.send_req("get", url, self.headers)
        if (not resp) or (resp.status_code != 200):
            log.error(f"Get resource {self.type} {id} failed!")
            return
        return resp.json()[self.type]

    def get_obj_by_name(self, name):
        if (hasattr(self, "detail")) and self.detail:
            url = f"{self.url}/detail"
        else:
            url = f"{self.url}"
        resp = self.send_req("get", url, self.headers)
        if (not resp) or (resp.status_code != 200):
            log.error(f"Get resource {self.type} {name} failed!")
            return
        objs = resp.json()[self.type + "s"]
        hits = []
        for obj in objs:
            if obj["name"] == name:
                hits.append(obj)
        obj = None
        if len(hits) < 1:
            log.error(f"No resources with name {name} are found!")
        elif len(hits) > 1:
            log.error(f"{len(objs)} resources with name {name} are found!")
        else:
            obj = hits[0]
        return obj 

    def list(self):
        objs = self.get_objs()
        util.output(self.args, objs)

    def list_instance(self):
        id = self.get_id_by_name(self.args.name)
        url = f"{self.url}/{id}/instance"
        resp = self.send_req("get", url, self.headers)
        if (not resp) or (resp.status_code != 200):
            log.error(f"Get resource cluster_instance of {id} failed!")
            return
        objs = resp.json()["cluster_instance"]
        util.output(self.args, objs)

    def show(self):
        if util.is_uuid(self.args.name):
            obj = self.get_obj_by_id(self.args.name)
        else:
            obj = self.get_obj_by_name(self.args.name)
        if obj:
            util.output(self.args, obj)

    def get_id_by_name(self, name, res_ins=None):
        if util.is_uuid(name):
            return name
        if res_ins:
            obj = res_ins.get_obj_by_name(name)
        else:
            obj = self.get_obj_by_name(name)
        if not obj:
            return
        return obj["id"]

    def delete(self):
        if util.is_uuid(self.args.name):
            id = self.args.name
        else:
            id = self.get_id_by_name(self.args.name)
        if not id:
            return
        url = f"{self.url}/{id}"
        resp = self.send_req("delete", url, self.headers)
        print(f"RC: {resp.status_code}")
        print(f"Response: {resp.text}")

