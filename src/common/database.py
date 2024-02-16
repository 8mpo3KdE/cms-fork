import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine

from common.config import config
import logging


log = logging.getLogger("uvicorn")


class DBBase(object):
    def __init__(self, db_name, metadata, table_map):
        self.db_name = db_name
        self.metadata = metadata
        self.table_map = table_map
        self.engine = None
        self.url = "mysql+aiomysql://{}:{}@{}/{}".format(
                config["mysql"]["username"],
                config["mysql"]["password"].replace("@", "%40"),
                config["mysql"]["host"], self.db_name)

    async def create_engine(self):
        try:
            self.engine = create_async_engine(self.url)
        except Exception as e:
            log.error(e)

    async def recreate_engine(self):
        log.info("Re-create engine.")
        if self.engine:
            await self.engine.dispose()
        await self.create_engine()

    async def check_table(self):
        log.info("Check all tables.")
        try:
            async with self.engine.begin() as conn:
                #await conn.run_sync(self.metadata.drop_all)
                await conn.run_sync(self.metadata.create_all)
            return
        except Exception as e:
            log.error(e)
            #await self.recreate_engine()
            return -1

    def rows_to_dicts(self, table_name, rows):
        table = self.table_map[table_name]
        keys = [str(i.key) for i in table.columns]
        dicts = []
        for row in rows:
            d = {}
            for i in range(len(keys)):
                if type(row[i]) == datetime:
                    d[keys[i]] = row[i].isoformat(timespec='seconds')
                else:
                    d[keys[i]] = row[i]
            dicts.append(d)
        return dicts
        #return [{keys[i]: vs[i] for i in range(len(keys))} for vs in rows]

    async def exec(self, statement, args = {}):
        #log.debug(f"DB execute statement {statement} args {args}.")
        output = None
        count = 2
        while count > 0:
            try:
                #async with self.engine.connect() as conn:
                async with self.engine.begin() as conn:
                    output = await conn.execute(statement, args)
                break
            except Exception as e:
                log.error(e)
                await self.recreate_engine()
            count -= 1
        return output

    async def get(self, table, query):
        rows = await self.exec(
                self.table_map[table].select().filter_by(**query))
        if rows:
            list = self.rows_to_dicts(table, rows.fetchall())
            return list
        else:
            return []

    async def add(self, table, row):
        if "id" not in row:
            row["id"] = str(uuid.uuid4())
        await self.exec(self.table_map[table].insert(), row)

    async def update(self, table, id, update):
        await self.exec(self.table_map[table].update().where(
                self.table_map[table].c.id == id), update)

    async def delete(self, table, id):
        await self.exec(self.table_map[table].delete().where(
                self.table_map[table].c.id == id))

