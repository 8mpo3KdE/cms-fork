from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, \
        DateTime

from common.database import DBBase

metadata = MetaData()

table_map = {
    "image": Table("image", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project_id", String(36)),
        Column("size", Integer),
        Column("container_format", String(24)),
        Column("disk_format", String(24)),
        Column("visibility", String(24)),
        Column("owner", String(36)),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "task": Table("task", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project", String(36)),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24)))
}

db = None


class DB(DBBase):
    def __init__(self, name):
        super().__init__(name, metadata, table_map)

