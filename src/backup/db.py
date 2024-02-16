from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, Boolean, MetaData, \
        DateTime

from common.database import DBBase

metadata = MetaData()

table_map = {
    "instance_snapshot": Table("instance_snapshot", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project_id", String(36)),
        Column("instance_id", String(36)),
        Column("plan_id", String(36)),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "instance_volume_snapshot": Table("instance_volume_snapshot", metadata,
        Column("id", String(36), primary_key=True),
        Column("volume_id", String(36)),
        Column("instance_snapshot_id", String(36))),
    "instance_backup": Table("instance_backup", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project_id", String(36)),
        Column("instance_id", String(36)),
        Column("instance_name", String(128)),
        Column("source_zone", String(128)),
        Column("plan_id", String(36)),
        Column("incremental", Boolean),
        Column("copy_zone", String(128)),
        Column("copy_project", String(128)),
        Column("copy_id", String(36)),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "instance_volume_backup": Table("instance_volume_backup", metadata,
        Column("id", String(36), primary_key=True),
        Column("volume_id", String(36)),
        Column("instance_backup_id", String(36))),
    "volume_backup": Table("volume_backup", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project_id", String(36)),
        Column("volume_id", String(36)),
        Column("volume_name", String(128)),
        Column("volume_type", String(128)),
        Column("size", Integer),
        Column("source_zone", String(128)),
        Column("plan_id", String(36)),
        Column("property", String(256)),
        Column("incremental", Boolean),
        Column("snapshot_id", String(36)),
        Column("copy_zone", String(128)),
        Column("copy_project", String(128)),
        Column("copy_id", String(36)),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "volume_snapshot": Table("volume_snapshot", metadata,
        Column("id", String(36), primary_key=True),
        Column("snapshot_id", String(36)),
        Column("snapshot_name", String(128)),
        Column("snapshot_timestamp", String(36)),
        Column("volume_id", String(36)),
        Column("volume_backup_id", String(36)))
}

db = None


class DB(DBBase):
    def __init__(self, name):
        super().__init__(name, metadata, table_map)

