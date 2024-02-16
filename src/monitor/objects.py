"""
The objects of monitor service.
"""
from typing import Union
from pydantic import BaseModel, RootModel


class MonitorClusterObject(BaseModel):
    name: str
    subnet_id: str
    service_address: str = None
    cluster_size: int = 1
    monitor_username: str = None
    monitor_password: str = None


class MonitorClusterPost(BaseModel):
    cluster: MonitorClusterObject


class MonitorClusterPutObject(BaseModel):
    name: str = None
    status: str = None


class MonitorClusterPut(BaseModel):
    cluster: MonitorClusterPutObject


class MonitorClusterAuthObject(BaseModel):
    user_name: str
    expired_time: int = 1


class ActionAuth(BaseModel):
    auth: MonitorClusterAuthObject


class MonitorClusterAttachInterfaceObject(BaseModel):
    subnet_id: str


class ActionAttachInterface(BaseModel):
    attach_interface: MonitorClusterAttachInterfaceObject


class MonitorClusterDetachInterfaceObject(BaseModel):
    interface_id: str
    delete: bool = True


class ActionDetachInterface(BaseModel):
    detach_interface: MonitorClusterDetachInterfaceObject


class MonitorClusterInterfaceSwitchObject(BaseModel):
    new_cluster_id: str
    interface_id: str


class ActionInterfaceSwitch(BaseModel):
    switch_interface: MonitorClusterInterfaceSwitchObject


class MonitorClusterUpgradeObject(BaseModel):
    upgrade_image: str
    keep_old: bool = True


class ActionClusterUpgrade(BaseModel):
    upgrade: MonitorClusterUpgradeObject


class MonitorClusterResizeObject(BaseModel):
    new_spec_id: str


class ActionResize(BaseModel):
    resize: MonitorClusterResizeObject


class MonitorClusterAction(RootModel):
    root: Union[ActionAuth, ActionAttachInterface, ActionDetachInterface,
            ActionInterfaceSwitch, ActionClusterUpgrade, ActionResize]
