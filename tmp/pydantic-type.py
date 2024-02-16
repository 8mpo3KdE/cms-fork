import uuid
from ipaddress import IPv4Address, IPv4Network
from pydantic import BaseModel, UUID4


class Test(BaseModel):
    name: str
    id: UUID4 = None
    network: IPv4Network = "192.168.10.0/24"
    address: IPv4Address = "192.168.10.1"


test = Test(
    name="Type Test",
    id=uuid.uuid4(),
    network="172.16.1.0/24",
    address="172.16.1.1",
)

print(test)
print(str(test.id))
print(str(test.network))
print(str(test.address))

