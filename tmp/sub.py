import asyncio


async def case_1():
    # Wait till sub-process starts, but not complete.
    cmd = "ls -l; sleep 2; echo done"
    p = await asyncio.create_subprocess_shell(cmd)
    print(f"Process {p} started.")

async def case_2():
    # Wait till sub-process completes.
    cmd = "ls -l; sleep 2; echo done"
    p = await asyncio.create_subprocess_shell(cmd)
    print(f"Process {p} started.")
    await p.wait()

async def case_shell():
    # Execute in the shell.
    cmd = "ls -l | grep async"
    p = await asyncio.create_subprocess_shell(cmd)
    print(f"Process {p} started.")
    await p.wait()

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

async def case_exec():
    # Execute without shell.
    #p = await asyncio.create_subprocess_exec("ls", "-l")
    cmd = "ls -l | grep async"
    p = await asyncio.create_subprocess_exec("bash", "-c", cmd)
    print(f"Process {p} started.")
    await p.wait()

async def case_exec_output():
    # Execute without shell.
    #p = await asyncio.create_subprocess_exec("ls", "-l")
    cmd = "cat txa | grep main_task"
    p = await asyncio.create_subprocess_exec("bash", "-c", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
    print(f"Process {p} started.")
    stdout, stderr = await p.communicate()
    print(f"RC: {p.returncode}")
    print(f"stdout: {stdout.decode().strip()}")
    print(f"stderr: {stderr.decode().strip()}")

async def main_task():
    print("main-task: Start.")
    asyncio.Task.current_task().id = "main_task"
    await case_shell_output("cat tx | grep main")
    #print("next")
    #await asyncio.sleep(5)
    print("exit")


evloop = asyncio.get_event_loop()
evloop.run_until_complete(main_task())
evloop.close()

