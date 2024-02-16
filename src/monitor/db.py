"""
DB model for Monitor Service
"""
from datetime import datetime
from sqlalchemy import Table, Column, String, Boolean, MetaData, Integer, \
        Text, DateTime

from common.database import DBBase

metadata = MetaData()

table_map = {
    "cluster": Table("cluster", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("project_id", String(36)),
        Column("internal_address", String(128)),
        Column("external_address", String(128)),
        Column("external_id", String(36)),
        Column("internal_id", String(36)),
        Column("security_group", String(36)),
        Column("cluster_size", Integer),
        Column("time_create", DateTime, default=datetime.utcnow),
        Column("time_update", DateTime, onupdate=datetime.utcnow),
        Column("deleted", Boolean, default=False),
        Column("status", String(24))),
    "cluster_instance": Table("cluster_instance", metadata,
        Column("id", String(36), primary_key=True),
        Column("reservation_id", String(36)),
        Column("cluster_id", String(36)),
        Column("port_id", String(36)),
        Column("port_address", String(128)),
        Column("fixed_address", String(128))),
    "cluster_interface": Table("cluster_interface", metadata,
        Column("id", String(36), primary_key=True),
        Column("cluster_id", String(36)),
        Column("instance_id", String(36)),
        Column("virtual_address", String(128)),
        Column("virtual_port_id", String(36)),
        Column("interface_address", String(128)))
}

db = None


class DB(DBBase):
    def __init__(self, name):
        super().__init__(name, metadata, table_map)

