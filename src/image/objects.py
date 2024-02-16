"""
The objects of image service.
"""
from enum import Enum
from typing import Union
from pydantic import BaseModel, RootModel, HttpUrl


class FileFormat(str, Enum):
    BARE = "bare"
    TGZ = "tgz"
    GZIP = "gzip"
    BZIP = "bzip"


class ImageFormat(str, Enum):
    RAW = "raw"
    QCOW2 = "qcow2"
    VMDK = "vmdk"


class Visibility(str, Enum):
    COMMUNITY = "community"
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"


class ResourceType(str, Enum):
    instance = "instance"
    volume = "volume"


class CopyObject(BaseModel):
    zone_name: str
    project_name: str = ""
    image_name: str = ""


class ImageObject(BaseModel):
    name: str
    project_id: str = ""
    size: int = 0
    visibility: Visibility = Visibility.PRIVATE
    link: HttpUrl = None
    resource_type: ResourceType = None
    resource_id: str = ""
    file_format: FileFormat = FileFormat.BARE
    image_format: ImageFormat = ImageFormat.RAW
    source_zone: str = ""
    usage: int = 0
    copies: list[CopyObject] = []


class ImagePost(BaseModel):
    image: ImageObject


class ImagePutObject(BaseModel):
    name: str = ""
    status: str = ""
    source_zone: str = ""


class ImagePut(BaseModel):
    image: ImagePutObject


class ActionCopy(BaseModel):
    copy: list[CopyObject]


class ImageAction(RootModel):
    root: Union[ActionCopy]

