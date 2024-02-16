import configparser

config = configparser.ConfigParser()
config["DEFAULT"] = {"log-level": "info"}
zone_conf = {}
svc_token_pack = {}

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s %(levelname)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(asctime)s %(levelname)s %(client_addr)s - "
                    + '"%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/uvicorn.log",
            "maxBytes": 10485760,
            "backupCount": 5
        },
        "access": {
            "formatter": "access",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/uvicorn-access.log",
            "maxBytes": 10485760,
            "backupCount": 5
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False
        }
    }
}


def load(service):
    conf_file = f"/etc/cms/{service}.conf"
    log_file = f"/var/log/cms/{service}.log"
    access_log_file = f"/var/log/cms/{service}-access.log"
    config.read(conf_file)
    log_level = config["DEFAULT"]["log-level"].upper()
    log_config["handlers"]["default"]["filename"] = log_file
    log_config["handlers"]["access"]["filename"] = access_log_file
    log_config["loggers"]["uvicorn"]["level"] = log_level
    log_config["loggers"]["uvicorn.error"]["level"] = log_level
    log_config["loggers"]["uvicorn.access"]["level"] = log_level

