import uvicorn

from common import config


def main():
    config.load("api")
    zone = config.config["DEFAULT"]["zone"]
    config.zone_conf = config.config[f"zone.{zone}"]
    uvicorn.run("route:app", 
            host=config.config["DEFAULT"]["server-host"],
            port=int(config.config["DEFAULT"]["server-port"]),
            log_config=config.log_config)


if __name__ == '__main__':
    main()

