import asyncio
from datetime import datetime
import os
import hashlib
import logging
import json
import aiohttp
from fastapi import Response
import traceback

log = logging.getLogger("uvicorn")

msg_root = "Active."
id_zero = "00000000-0000-0000-0000-000000000000"
time_format_iso = "%Y-%m-%dT%H:%M:%S"


def get_time():
    return datetime.now().strftime(time_format_iso)


def pop_none(d):
    for key in list(d.keys()):
        if type(d[key]) is dict:
            pop_none(d[key])
        elif d[key] is None:
            d.pop(key)


def get_q_str(query):
    q = ""
    if query:
        for key in query.keys():
            if query[key]:
                if not q:
                    q += f"?{key}={query[key]}"
                else:
                    q += f"&{key}={query[key]}"
    return q


def get_svc_url(catalog, service):
    url = None
    for svc in catalog:
        if svc["type"] == service:
            for ep in svc["endpoints"]:
                if ep["interface"] == "public":
                    url = ep["url"]
                    break
            break
    return url


def get_file_hash(name):
    file_key = "{}:{}".format(name, os.stat(name).st_mtime)
    (md5, sha256) = (None, None)
    with open(name, 'rb') as f:
        (md5, sha256) = calculate_hashe(f)
    return md5, sha256


def calculate_hashe(data):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    if hasattr(data, "read"):
        for chunk in iter(lambda: data.read(8192), b""):
            md5.update(chunk)
            sha256.update(chunk)
    else:
        md5.update(data)
        sha256.update(data)
    return md5.hexdigest(), sha256.hexdigest()


async def send_req(op, url, headers, data=None, cookies=None,
        secure_log=False):
    req_data = None
    if data:
        data_type = type(data)
        if (data_type is dict) or (data_type is list):
            req_data = json.dumps(data).encode("utf-8")
        elif (data_type is bytes) or (data_type is str):
            req_data = data
        else:
            log.error(f"Request data type {data_type} is not supported!")
            return {"status": 500, "headers": {}, "data": None}

    resp_status = 500
    resp_headers = {}
    resp_data = None
    resp_cookies = None
    async with aiohttp.ClientSession(cookies=cookies) as session:
        func = getattr(session, op)
        try:
            async with func(url, headers=headers, data=req_data, 
                    ssl=False, allow_redirects=False) as resp:
                resp_data = await resp.read()
                if resp_data:
                    try:
                        resp_data = json.loads(resp_data.decode("utf-8"))
                    except ValueError:
                        pass
            resp_status = resp.status
            resp_headers = resp.headers
            resp_cookies = resp.cookies
            if resp_status >= 400:
                if secure_log:
                    data = "********"
                log.debug(f"Send request op: {op} url: {url} data: {data}")
                log.debug(f"send_req response: {resp_status} {resp_data}")
        except Exception as e:
            log.error(f"Exception: {e}, {op}, {url}")
    return {"status": resp_status, "data": resp_data, "headers": resp_headers,
            "cookies": resp_cookies}


def response(status, headers=None, data=None, cookies=None):
    resp_data = None
    if data is not None:
        data_type = type(data)
        if (data_type is dict) or (data_type is list):
            resp_data = json.dumps(data).encode("utf-8")
        elif (data_type is bytes) or (data_type is str):
            resp_data = data
        else:
            log.error(f"Response data type {data_type} is not supported!")
            return Response(status_code=500)
    new_headers = {}
    if headers:
        for key in headers.keys():
            new_headers[key] = headers[key]
        new_headers["Content-Length"] = str(len(resp_data))
    resp = Response(status_code=status, headers=new_headers, content=resp_data)
    if cookies:
        for k in cookies.keys():
            resp.set_cookie(key=k, value=cookies[k])
    return resp


async def exec_cmd(cmd, output=False, output_file=None):
    log.debug(f"Run \"{cmd}\".")
    if output_file:
        p = await asyncio.create_subprocess_shell(cmd,
                stdout=output_file, stderr=output_file)
        await p.wait()
    else:
        p = await asyncio.create_subprocess_shell(cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await p.communicate()
    if p.returncode == 0:
        if not output_file:
            log.debug(f"stdout: {stdout.decode().strip()}")
    else:
        if not output_file:
            log.debug(f"stderr: {stderr.decode().strip()}")
    if output:
        return p.returncode, stdout.decode().strip()
    else:
        return p.returncode


def task_done_cb(self):
    try:
        self.result()
    except Exception as e:
        log.error(traceback.format_exc())

