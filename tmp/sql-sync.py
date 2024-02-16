#!/usr/bin/python3

import datetime
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, String, MetaData


def get_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


metadata = MetaData()
table_snapshot = Table("snapshot", metadata,
        Column("id", String(36), primary_key=True),
        Column("name", String(128)),
        Column("source_type", String(24)),
        Column("source_id", String(36)),
        Column("time_create", String(24), default=get_time),
        Column("time_update", String(24), onupdate=get_time),
        Column("status", String(24)))

engine = create_engine("mysql://service:Service1234@127.0.0.1/backup")

metadata.create_all(engine)

row = {"id": "deadbeef2", "name": "test2", "source_type": "instance",
        "source_id": "1234", "status": "running"}

update = {"status": "available"}

#with engine.begin() as conn:
    #conn.execute(table_snapshot.insert(), row)

    #conn.execute(table_snapshot.update().
    #        where(table_snapshot.c.id == "deadbeef"), update)

    #conn.execute(table_snapshot.delete().
    #        where(table_snapshot.c.id == "deadbeef"))

with engine.connect() as conn:
    rows = conn.execute(table_snapshot.select().
            where(table_snapshot.c.source_id == "1234"))
    l = rows.fetchall()
    print(l)
    for row in l:
        print(row)

