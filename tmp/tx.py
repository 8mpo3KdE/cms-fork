import os
import asyncio
import bz2


def task_done_cb(self):
    #print("I am done.")
    #self.result()
    #return
    try:
        self.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(e)


class PipeProtocol(asyncio.Protocol):
    def __init__(self, arg1):
        self.seq = 0

    #def connection_made(self, transport):
    #    #super(PipeProtocol, self).connection_made(transport=transport)
    #    print("pipe opened")

    def data_received(self, data):
        #super(PipeProtocol, self).data_received(data)
        # Default data size is 256KB.
        self.seq += 1
        tx_data = bz2.compress(data)
        print(f"rx: {len(data)} bytes to {len(tx_data)}, seq: {self.seq}")

    #def connection_lost(self, exc):
    #    #super(PipeProtocol, self).connection_lost(exc)
    #    print("pipe closed")


async def task_mirror():
    print("INFO: [task_mirror] start.")
    asyncio.Task.current_task().id = "mirror"

    loop = asyncio.get_event_loop()
    rfd, wfd = os.pipe()
    proto = PipeProtocol(arg1="arg1")
    transport, protocol = await loop.connect_read_pipe(
            lambda: proto, os.fdopen(rfd))

    #cmd = "for i in $(seq 8); do echo $i; sleep 1; done"
    cmd = "cat api"
    #cmd = "rbd export volume/volume-f5e09c95-d29b-4d4e-b4a4-0ed918e7fe1e -"
    print(f"INFO: Run command \"{cmd}\".")
    p = await asyncio.create_subprocess_shell(cmd, stdout=wfd, stderr=wfd)
    os.close(wfd)

    while p.returncode is None:
        await asyncio.sleep(1)
        #print(f"rc: {p.returncode}")

    print(f"INFO: Run command is done.")


async def main_task():
    print("INFO: [main_task] start.")
    asyncio.Task.current_task().id = "main"
    task = asyncio.ensure_future(task_mirror())
    task.add_done_callback(task_done_cb)
    end = False
    while not end:
        await asyncio.sleep(2)
        #print("INFO: [main_task] Check tasks.")
        tasks = asyncio.Task.all_tasks()
        pending = 0
        for task in tasks:
            #print(f"INFO: [main_task] Check task {task._coro} {task._state}.")
            if task._state == "PENDING":
                pending += 1
        print(f"INFO: [main_task] Pending tasks: {pending}.")
        if pending == 1:
            end = True

evloop = asyncio.get_event_loop()
evloop.run_until_complete(main_task())
evloop.close()

