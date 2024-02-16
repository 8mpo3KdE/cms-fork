import asyncio
import datetime
import uuid
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import Table, Column, String, MetaData


def get_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


metadata = MetaData()
table_test = Table("test", metadata,
        Column("id", String(36), primary_key = True),
        Column("name", String(128)),
        Column("source_type", String(24)),
        Column("source_id", String(36)),
        Column("time_create", String(24), default = get_time),
        Column("time_update", String(24), onupdate = get_time),
        Column("status", String(24)))

row1 = {"id": uuid.uuid4(),
        "name": "test1",
        "source_type": "instance",
        "source_id": "1234",
        "status": "running"}
row2 = {"id": uuid.uuid4(),
        "name": "test2",
        "source_type": "volume",
        "source_id": "5678",
        "status": "active"}
update = {"status": "error"}


async def test_begin(engine):
    async with engine.begin() as conn:
        await conn.execute(table_test.insert(), row1)
        await conn.execute(table_test.insert(), row2)

        await conn.execute(table_test.update().
                where(table_test.c.name == "test1"), update)

        await conn.execute(table_test.delete().
                where(table_test.c.name == "test2"))

async def test_connect(engine):
    async with engine.connect() as conn:
        await conn.execute(table_test.insert(), row1)
        #rows = await conn.execute(table_test.select().
        #        where(table_test.c.source_id == "1234"))
        #query = {"source_id": "1234", "status": "running"}
        #rows = await conn.execute(table_test.select().filter_by(**query))
        #for row in rows:
        #    print(row)
        await conn.commit()
        #print(result.fetchall())

async def main_task():
    conn_str = "mysql+aiomysql://cms:Cms%401234@127.0.0.1/test"
    engine = create_async_engine(conn_str, echo=True)

    async with engine.begin() as conn:
        #await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)

    #await test_begin(engine)
    await test_connect(engine)

    await engine.dispose()

evloop = asyncio.get_event_loop()
evloop.run_until_complete(main_task())
evloop.close()

