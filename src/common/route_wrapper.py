import logging
import functools

from common import config, util
from openstack.keystone import Auth

log = logging.getLogger("uvicorn")


def route_wrapper(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not kwargs["x_auth_token"]:
            return util.response(401,
                    data={"message": "Auth token is missing!"})
        token_pack = await Auth(config.svc_token_pack).validate(
                kwargs["x_auth_token"])
        if not token_pack:
            return util.response(401,
                    data={"message": "Token validation failed!"})
        token_pack["token"] = kwargs["x_auth_token"]
        kwargs["token_pack"] = token_pack
        resp = await func(*args, **kwargs)
        if "data" not in resp:
            resp["data"] = None
        #log.debug("Send response back to client.")
        return util.response(resp["status"], data=resp["data"])
    return wrapper

