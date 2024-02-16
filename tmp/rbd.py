import asyncio
import json


async def case_shell_output(cmd):
    # Execute in the shell.
    print(cmd)
    p = await asyncio.create_subprocess_shell(cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
    #print(f"Process {p} started.")
    stdout, stderr = await p.communicate()
    print(f"RC: {p.returncode}")
    print(f"stdout: {stdout.decode().strip()}")
    print(f"stderr: {stderr.decode().strip()}")
    return stdout.decode().strip()

async def create_start():
    vol_spec = "volume-ssd/volume-abeab3fb-9594-4dce-a9d5-53f3f0115f09"
    cmd = f"rbd snap create {vol_spec}@start"
    await case_shell_output(cmd)
    cmd = f"rbd snap protect {vol_spec}@start"
    await case_shell_output(cmd)

async def create_user():
    vol_spec = "volume-ssd/volume-abeab3fb-9594-4dce-a9d5-53f3f0115f09"
    cmd = f"rbd snap create {vol_spec}@user"
    await case_shell_output(cmd)
    cmd = f"rbd snap protect {vol_spec}@user"
    await case_shell_output(cmd)

async def delete_image():
    image_spec = "backup/test"
    cmd = f"rbd snap ls {image_spec} --format json"
    output = await case_shell_output(cmd)
    snapshots = json.loads(output)
    for ss in snapshots:
        cmd = f"rbd snap unprotect {image_spec}@{ss['name']}"
        await case_shell_output(cmd)
    cmd = f"rbd snap purge {image_spec}"
    await case_shell_output(cmd)
    cmd = f"rbd rm {image_spec}"
    await case_shell_output(cmd)

async def copy_image():
    vol_spec = "volume-ssd/volume-abeab3fb-9594-4dce-a9d5-53f3f0115f09"
    args = "--export-format 2 --no-progress"
    cmd = f"rbd export {args} {vol_spec}@start -" \
            f" | rbd import {args} - backup/test"
    await case_shell_output(cmd)

async def main_task():
    print("main-task: Start.")
    asyncio.Task.current_task().id = "main_task"
    #await delete_image()
    #await copy_image()
    #print("next")
    #await asyncio.sleep(5)
    print("exit")


evloop = asyncio.get_event_loop()
evloop.run_until_complete(main_task())
evloop.close()

