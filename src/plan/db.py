from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, \
        DateTime

from common.database import DBBase

metadata = MetaData()

table_map = {
    "snapshot_plan": Table("snapshot_plan", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("resource_type", String(24)),
        Column("project_id", String(36)),
        Column("schedule", String(128)),
        Column("retention", Integer),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "backup_plan": Table("backup_plan", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("resource_type", String(24)),
        Column("project_id", String(36)),
        Column("schedule", String(128)),
        Column("retention", Integer),
        Column("copy_zone", String(128)),
        Column("copy_project", String(128)),
        Column("incremental", Boolean, default=False),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24)))
}

db = None


class DB(DBBase):
    def __init__(self, name):
        super().__init__(name, metadata, table_map)

