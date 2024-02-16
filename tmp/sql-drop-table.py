from sqlalchemy import create_engine
from sqlalchemy import Table, MetaData


metadata = MetaData()
database = "backup"
table = Table("task", metadata)

engine = create_engine("mysql://{}:{}@{}/{}".format(
        "service", "Service1234", "127.0.0.1", database))

metadata.drop_all(bind=engine, tables=[table])

