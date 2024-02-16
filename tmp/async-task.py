import asyncio


def task_done_cb(self):
    print("I am done.")
    self.result()
    return
    try:
        self.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(e)


async def sub_task_1():
    print("sub-task-1: start...")
    asyncio.Task.current_task().id = "11111111"
    print("sub-task-1: list all tasks...")
    tasks = asyncio.Task.all_tasks()
    for task in tasks:
        print(task.id)
    print("sub-task-1: sleep for 3 sec...")
    await asyncio.sleep(3)
    print("sub-task-1: done...")


async def sub_task_2():
    print("Start sub-task 2...")
    asyncio.Task.current_task().id = "22222222"
    print("sub-task-2: list all tasks...")
    tasks = asyncio.Task.all_tasks()
    for task in tasks:
        print(task.id)
    cmd = "ls aaa"
    p = await asyncio.create_subprocess_shell(cmd,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    print(f"sub-task-2: command return code: {p.returncode}.")
    print(f"sub-task-2: stdout: {stdout.decode().strip()}.")
    print(f"sub-task-2: stderr: {stderr.decode().strip()}.")


async def sub_task_3():
    print("Start sub-task 3...")
    await asyncio.sleep(1)
    raise RuntimeError("Oops...")


async def main_task():
    print("main-task: start...")
    asyncio.Task.current_task().id = "deadbeef"
    count = 1
    while count <= 8:
        print(f"main-task: count {count}...")
        if count == 2:
            print("main-task: Add task sub-task-1...")
            evloop = asyncio.get_event_loop()
            evloop.create_task(sub_task_1())
            #task = asyncio.ensure_future(sub_task_1())
            #task.add_done_callback(task_done_cb)
        elif count == 3:
            tasks = asyncio.Task.all_tasks()
            for task in tasks:
                if task.id == "11111111":
                    print("main-task: Cancel task 11111111.")
                    task.cancel()
        elif count == 4:
            print("main-task: Add task sub-task-2...")
            task = asyncio.ensure_future(sub_task_2())
        elif count == 5:
            print("main-task: Add task sub-task-3...")
            # This creates a reference to the task, which won't be freed
            # when task is done. Exception won't be captured when task is done.
            # Adding callback help to capture the exception, but the task still
            # won't be freed until the caller is freed.
            task = asyncio.ensure_future(sub_task_3())
            task.add_done_callback(task_done_cb)
            #
            # This doesn't create a reference to the task, which will be freed
            # when task is done. Exception will be captured when task is freed.
            #asyncio.ensure_future(sub_task_3())
        print(f"main-task: sleep for 2 sec...")
        await asyncio.sleep(2)
        count += 1


evloop = asyncio.get_event_loop()
evloop.run_until_complete(main_task())
evloop.close()

