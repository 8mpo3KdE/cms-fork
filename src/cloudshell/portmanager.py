import asyncio
import logging
import time
import random

from common.config import config
from common import util

log = logging.getLogger("uvicorn")


class PortManager:
    def __init__(self):
        self.used_port = []
        self.timeout = 10 * 60

    def _check_port_exists(self, port_num):
        if not len(self.used_port):
            return False

        for port in self.used_port:
            if port["number"] == port_num:
                return True

        return False

    def get_new_port(self):
        port_max = 9100
        port_min = 9000

        if len(self.used_port) >= port_max - port_min + 1:
            raise ValueError("Total of CloudShell has reached the limit.")

        port = str(random.randint(port_min, port_max))
        while port in self.used_port:
            port = str(random.randint(port_min, port_max))

        return port

    def add(self, port_num, uid="", project_id="", hashed_token=""):
        exists = self._check_port_exists(port_num)

        if exists:
            self.update(port_num)
        else:
            port = {
                "number": port_num,
                "uid": uid,
                "project_id": project_id,
                "updated_at": time.time(),
                "hashed_token": hashed_token
            }
            self.used_port.append(port)

    def check_token_valid(self, port, token):
        for p in self.used_port:
            if port == p["number"]:
                if token == p["hashed_token"]:
                    return True
                else:
                    return False
        return False

    def get(self, number_only=True):
        if number_only:
            return list(map(lambda p: p["number"], self.used_port))
        else:
            return self.used_port

    def update(self, port_num):
        for port in self.used_port:
            if port["number"] == port_num:
                port["updated_at"] = time.time()

    def get_port_by_uid_pid(self, uid, pid):
        return list(
                filter(
                    lambda p: p["uid"] == uid and p["project_id"] == pid, 
                    self.used_port
                )
            )

    async def enable_cleaner(self):
        log.info("Port cleaner on duty. " +
                 f"The timeout is set to {self.timeout} secs.")

        while True:
            if len(self.used_port):
                for port in self.used_port:
                    diff = time.time() - port["updated_at"]
                    if diff > self.timeout:
                        await self._destory_container(port["number"])
                        self.used_port = \
                            list(filter(
                                lambda p: not p["number"] == port["number"],
                                self.used_port
                            ))
                await asyncio.sleep(self.timeout)

            else:
                await asyncio.sleep(self.timeout)

    async def _destory_container(self, port_num):
        host_ip = config["DEFAULT"]["host-address"]
        cmd = f"ssh root@{host_ip} docker rm -f cloudshell-host{port_num}"

        await util.exec_cmd(cmd)
        await asyncio.sleep(1)

