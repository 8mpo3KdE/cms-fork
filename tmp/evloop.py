import logging
import logging.handlers
import configparser
import asyncio
import signal
import functools

loop = asyncio.get_event_loop()

log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "error": logging.ERROR}
log = logging.getLogger("service")
log.setLevel(log_level_map["info"])

config = configparser.ConfigParser()
config["DEFAULT"] = {
        "log-file": "/var/log/service/service.log",
        "log-level": "info"}


async def cron():
    count = 0
    while True:
        log.info("cron {}.".format(count))
        await asyncio.sleep(5)
        count += 1


def hdlr_exit(signame):
    log.info("Got signal {}".format(signame))
    loop.stop()


def main():
    log_hdlr = logging.handlers.RotatingFileHandler(
            config["DEFAULT"]["log-file"],
            maxBytes = 10485760, backupCount = 5)
    log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    log_hdlr.setFormatter(log_formatter)
    log_hdlr.setLevel(log_level_map["info"])
    log.addHandler(log_hdlr)

    log.info("Start service.")
    config.read('/usr/local/service-framework/conf/service.conf')
    log_level = config["DEFAULT"]["log-level"]
    log.setLevel(log_level_map[log_level])
    log_hdlr.setLevel(log_level_map[log_level])
    log.info("Log level: {}.".format(log_level))
    log.debug("Debug is enabled.")

    for signame in ("SIGINT", "SIGTERM"):
        loop.add_signal_handler(getattr(signal, signame),
                functools.partial(hdlr_exit, signame))

    asyncio.ensure_future(cron())

    log.info("Start event loop.")
    try:
        loop.run_forever()
    finally:
        log.info("Exit.")
        loop.close()


if __name__ == '__main__':
    main()

