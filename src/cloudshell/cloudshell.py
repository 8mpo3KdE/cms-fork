import asyncio
import logging
import paramiko
import hashlib
import json

from common import util, config
from fastapi import WebSocketDisconnect
from openstack.keystone import Auth
from portmanager import PortManager

# suppressing websocket debugging logs. 
logging.getLogger('uvicorn.error').setLevel(logging.ERROR)

log = logging.getLogger("uvicorn")
port_mgr = PortManager()


class CloudShell(object):
    def __init__(self, token_pack=None):
        if token_pack:
            self.token_pack = token_pack
            self.uid = token_pack["user"]["id"]
            self.token = token_pack["token"]
            self.project = token_pack["project"]["id"]
            self.role_admin = False
            self.host_ip = config.config["DEFAULT"]["host-address"]
            for role in token_pack["roles"]:
                if role["name"] == "admin":
                    self.role_admin = True
                    break
        
    async def _start_session(self):
        try:
            port = port_mgr.get_new_port()
        except ValueError as e:
            log.error(e.args)
            return {
                "status": 423,
                "reason": e.args
            }
        else:
            cert_path = "/etc/pki/ca-trust/source/anchors"
            registry = config.config["DEFAULT"]["registry"]
            cmd_create_cntr = f"ssh root@{self.host_ip}" \
                              f" \"docker run -d" \
                              f" --name=cloudshell-host{port}" \
                              f" -p {port}:22" \
                              f" -v /root/.ssh:/root/.ssh:ro" \
                              f" -v {cert_path}:{cert_path}:ro" \
                              f" {registry}/cms/cloudshell:2.0.0" \
                               " /usr/bin/bash -c" \
                              f" 'update-ca-trust && /usr/sbin/sshd -D'\""

            await util.exec_cmd(cmd_create_cntr)

            return {
                "port": port
            }

    async def _inject_credential(self, port):
        auth_interface = "public"
        auth_url_type = "publicURL"
        auth_url = ""
        region = ""

        for cat in self.token_pack['catalog']:
            if cat["type"] == "identity":
                for endpoint in cat["endpoints"]:
                    if endpoint["interface"] == auth_interface: 
                        auth_url = endpoint["url"]
                        region = endpoint["region"]
                        break
                break

        cred_file = f"export OS_PROJECT_DOMAIN_NAME=" + \
            self.token_pack["project"]["domain"]["name"] + \
            f"\nexport OS_PROJECT_NAME=" + \
            self.token_pack["project"]["name"] + \
            f"\nexport OS_TOKEN=" + \
            self.token + \
            f"\nexport OS_AUTH_URL={auth_url}" + \
            f"\nexport OS_INTERFACE={auth_interface}" + \
            f"\nexport OS_ENDPOINT_TYPE={auth_url_type}" + \
            f"\nexport OS_REGION_NAME={region}" + \
            f"\nexport OS_IDENTITY_API_VERSION=3" + \
            f"\nexport OS_AUTH_PLUGIN=token" + \
            f"\nexport OS_AUTH_TYPE=token" + \
            f"\nexport OS_CACERT=/etc/pki/ca-trust/source/anchors/client.pem"
        
        cmd = f"ssh -p {port} root@{self.host_ip} -T " + \
            f"\"echo '{cred_file}' >> .bash_profile | " + \
            f"rm /run/nologin -f\""
        
        await util.exec_cmd(cmd)

    async def start_session(self):
        curr_port = port_mgr.get_port_by_uid_pid(self.uid, self.project)
        if len(curr_port):
            port = curr_port[0]["number"]
            key = curr_port[0]["hashed_token"]
            port_mgr.update(port)
            return {
                "status": 200,
                "data": {
                    "port": port,
                    "key": key
                }
            }

        try:
            session_info = await self._start_session()
            await asyncio.sleep(3)
            await self._inject_credential(session_info["port"])
        except Exception as e:
            log.error(e)
            return {
                "status": 500
            }
        else:
            hashed_token = hashlib.md5(self.token.encode()).hexdigest()
            port_mgr.add(session_info["port"], self.uid,
                        self.project, hashed_token)
            return {
                "status": 200, 
                "data": {
                    "port": session_info["port"],
                    "key": hashed_token
                }
            }
    
    def _recv(self, chan, chan_size):
        res = ""
        if chan.recv_ready():
            res = chan.recv(chan_size)
        if chan.recv_stderr_ready():
            res = chan.recv_stderr(chan_size)
        return res

    async def _waited_recv(self, chan, chan_size, ws):
        while True:          
            await asyncio.sleep(0.05)
            res = self._recv(chan, chan_size)
            if res != "":
                await ws.send_text(res)

    async def ws_connect(self, websocket, port):
        client_key = websocket.query_params['id']
        if not port_mgr.check_token_valid(port, client_key):
            return {
                "status": 401
            }
        
        used = port_mgr.get(number_only=True)
        if port not in used:
            log.error(f"ws handshake refused: port {port} not found.")
            
            return {
                "status": 404,
            }
        
        chan_byte_size = 32 * 1024
        ssh_user_name = "root"
        host_ip = config.config["DEFAULT"]["host-address"]

        await websocket.accept()
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host_ip, username=ssh_user_name,
            port=int(port), timeout=5)
        
        chan = ssh.invoke_shell(term="xterm")

        asyncio.create_task(self._waited_recv(chan,
                chan_byte_size, websocket))

        auth_needed = True
        try:
            while True:
                raw_msg = await websocket.receive_text()
                port_mgr.update(port)
                msg = json.loads(raw_msg)
                
                auth_token = msg.get("auth")
                
                if auth_token and auth_needed:
                    valid_token = await Auth(
                            config.svc_token_pack).validate(auth_token)
                    if not valid_token:
                        raise Exception("Unauthorized")
                    else:
                        auth_needed = False

                resize = msg.get("resize")
                if resize and len(resize) == 2:
                    chan.resize_pty(*resize)

                cmd = msg.get("data")
                if cmd:
                    chan.send(cmd)
                
        except WebSocketDisconnect:
            log.info(f"client at port {port} disconnected")
        except Exception as err:
            log.error(err)


def preflight_check():
    """check if vm exists, check if image exists"""
    pass


async def load_exists_ports():
    port = await get_used_port()
    for p in port:
        port_mgr.add(p)
    
    asyncio.create_task(port_mgr.enable_cleaner())


async def get_used_port():
    host_ip = config.config["DEFAULT"]["host-address"]

    cmd_ls_in_use = f"ssh root@{host_ip} " + \
                    "ss -lanpt | grep LISTEN | grep \"9***\" " + \
                    "| awk '{ print $4 }' | awk -F \":\" '{ print $2 }'"

    cmd_ret = await util.exec_cmd(cmd_ls_in_use, True)
    used_ports = list()

    for used in cmd_ret[1].split("\n"):
        if str(used).startswith("9"):
            used_ports.append(used)

    return used_ports

