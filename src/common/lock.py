import asyncio
import logging

log = logging.getLogger("uvicorn")
res_lock = {}


async def acquire(res):
    res_type = res["type"]
    res_id = res["id"]
    log.info(f"Try to acquire lock on {res_type} {res_id}.")
    wait = True
    while wait:
        if res_id not in res_lock.keys():
            wait = False
        else:
            await asyncio.sleep(1)
    res_lock[res_id] = True
    log.info(f"Acquired lock on {res_type} {res_id}.")


async def release(res):
    res_type = res["type"]
    res_id = res["id"]
    if res_id in res_lock.keys():
        res_lock.pop(res_id)
        log.info(f"Released lock on {res_type} {res_id}.")
    else:
        log.error(f"No lock on {res_type} {res_id}")

