import uvicorn

from common import config
import db


def main():
    config.load("image")
    db.db = db.DB("cms_image")
    zone = config.config["DEFAULT"]["zone"]
    zone_conf = config.config[f"zone.{zone}"]
    config.zone_conf = config.config[f"zone.{zone}"]
    uvicorn.run("route:app",
            host=config.config["DEFAULT"]["server-host"],
            port=int(config.config["DEFAULT"]["server-port"]),
            log_config=config.log_config)


if __name__ == '__main__':
    main()

