from fastapi import APIRouter
from fastapi.requests import Request

import api

router_compute = APIRouter(prefix="/v1/compute", tags=["compute"])


# quota
@router_compute.get("/limit")
async def get_compute_limit(req: Request):
    fwd_path = "/limits"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.get("/quota-set/{id}")
async def get_compute_quota_sets(req: Request, id: str):
    fwd_path = f"/os-quota-sets/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.put("/quota-set/{id}")
async def put_compute_quota_set(req: Request, id: str):
    fwd_path = f"/os-quota-sets/{id}"
    return await api.op_api(req, "put", "compute", fwd_path)

@router_compute.get("/usage/{id}")
async def get_compute_usage(req: Request, id: str):
    fwd_path = f"/os-simple-tenant-usage/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)

# compute:instance
@router_compute.get("/instance/detail")
async def get_compute_instance_detail(req: Request):
    fwd_path = "/servers/detail"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.get("/instance")
async def get_compute_instances(req: Request):
    fwd_path = "/servers"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.get("/instance/{id}")
async def get_compute_instance(req: Request, id: str):
    fwd_path = f"/servers/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.put("/instance/{id}")
async def put_compute_instance(req: Request, id: str):
    fwd_path = f"/servers/{id}"
    return await api.op_api(req, "put", "compute", fwd_path)


@router_compute.delete("/instance/{id}")
async def delete_compute_instance(req: Request, id: str):
    fwd_path = f"/servers/{id}"
    return await api.op_api(req, "delete", "compute", fwd_path)


@router_compute.post("/instance")
async def post_compute_instance(req: Request):
    fwd_path = "/servers"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.get("/instance/{id}/list-action")
async def get_compute_instance_list_action(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-instance-actions"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.post("/instance/{id}/action")
async def post_compute_instance_action(req: Request, id: str):
    fwd_path = f"/servers/{id}/action"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.get("/instance/{id}/metadata")
async def get_compute_instance_meta(req: Request, id: str):
    fwd_path = f"/servers/{id}/metadata" 
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.put("/instance/{id}/metadata")
async def put_compute_instance_meta(req: Request, id: str):
    fwd_path = f"/servers/{id}/metadata"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.get("/instance/{id}/metadata/{key}")
async def get_compute_instance_meta_key(req: Request, id: str, key: str):
    fwd_path = f"/servers/{id}/metadata/{key}" 
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.put("/instance/{id}/metadata/{key}")
async def put_compute_instance_meta_key(req: Request, id: str, key: str):
    fwd_path = f"/servers/{id}/metadata/{key}"
    return await api.op_api(req, "put", "compute", fwd_path)


@router_compute.delete("/instance/{id}/metadata/{key}")
async def delete_compute_instance_meta_key(req: Request, id: str, key: str):
    fwd_path = f"/servers/{id}/metadata/{key}"
    return await api.op_api(req, "delete", "compute", fwd_path)


@router_compute.post("/instance/{id}/console")
async def post_compute_instance_console(req: Request, id: str):
    fwd_path = f"/servers/{id}/remote-consoles"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.post("/instance/{id}/interface")
async def post_compute_instance_interface(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-interface"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.get("/instance/{id}/interface")
async def get_compute_instance_interface(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-interface"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.get("/instance/{id}/interface/{port_id}")
async def get_compute_instance_interface_port(req: Request,
        id: str, port_id: str):
    fwd_path = f"/servers/{id}/os-interface/{port_id}"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.delete("/instance/{id}/interface/{port_id}")
async def delete_compute_instance_interface_port(req: Request,
        id: str, port_id: str):
    fwd_path = f"/servers/{id}/os-interface/{port_id}"
    return await api.op_api(req, "delete", "compute", fwd_path)


@router_compute.get("/instance/{id}/volume")
async def get_compute_instance_volumes(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-volume_attachments"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.post("/instance/{id}/volume")
async def post_compute_instance_volume(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-volume_attachments"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.get("/instance/{id}/volume/{vol_id}")
async def get_compute_instance_volume(req: Request, id: str, vol_id: str):
    fwd_path = f"/servers/{id}/os-volume_attachments/{vol_id}"
    return await api.op_api(req, "get", "compute", fwd_path)


# NOTE:cannot be used as attach new vol.
@router_compute.put("/instance/{id}/volume/{vol_id}")
async def put_compute_instance_volume(req: Request, id: str, vol_id: str):
    fwd_path = f"/servers/{id}/os-volume_attachments/{vol_id}"
    return await api.op_api(req, "put", "compute", fwd_path)


@router_compute.delete("/instance/{id}/volume/{vol_id}")
async def delete_compute_instance_volume(req: Request, id: str, vol_id: str):
    fwd_path = f"/servers/{id}/os-volume_attachments/{vol_id}"
    return await api.op_api(req, "delete", "compute", fwd_path)


@router_compute.get("/instance/{id}/security-group")
async def get_compute_instance_security_group(req: Request, id: str):
    fwd_path = f"/servers/{id}/os-security-groups"
    return await api.op_api(req, "get", "compute", fwd_path)


# compute:availability zone
@router_compute.get("/availability-zone")
async def get_compute_availability_zone(req: Request):
    fwd_path = "/os-availability-zone"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.get("/availability-zone/detail")
async def get_compute_availability_zone_detail(req: Request):
    fwd_path = "/os-availability-zone/detail"
    return await api.op_api(req, "get", "compute", fwd_path)

# compute: spec
@router_compute.get("/spec")
async def get_compute_specs(req: Request):
    fwd_path = "/flavors"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.get("/spec/detail")
async def get_compute_specs_detail(req: Request):
    fwd_path = "/flavors/detail"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.get("/spec/{id}")
async def get_compute_spec(req: Request, id: str):
    fwd_path = f"/flavors/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)


# compute: server group
@router_compute.get("/server-group")
async def get_compute_server_group(req: Request):
    fwd_path = "/os-server-groups"
    return await api.op_api(req, "get", "compute", fwd_path)


# compute:keypair
@router_compute.get("/keypair")
async def get_keypairs(req: Request):
    fwd_path = "/os-keypairs"
    return await api.op_api(req, "get", "compute", fwd_path)


@router_compute.post("/keypair")
async def post_keypair(req: Request):
    fwd_path = "/os-keypairs"
    return await api.op_api(req, "post", "compute", fwd_path)


@router_compute.delete("/keypair/{key}")
async def delete_keypairs_key(req: Request, key: str):
    fwd_path = f"/os-keypairs/{key}"
    return await api.op_api(req, "delete", "compute", fwd_path)


# compute:snapshot
@router_compute.get("/snapshot")
async def get_compute_snapshots(req: Request):
    fwd_path = "/instance/snapshot"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_compute.post("/snapshot")
async def post_compute_snapshot(req: Request):
    fwd_path = "/instance/snapshot"
    return await api.op_api(req, "post", "cms-backup", fwd_path)


@router_compute.post("/snapshot/{id}/action")
async def post_compute_snapshot_action(req: Request, id: str):
    fwd_path = f"/instance/snapshot/{id}/action"
    return await api.op_api(req, "post", "cms-backup", fwd_path)


@router_compute.get("/snapshot/{id}")
async def get_compute_snapshot(req: Request, id: str):
    fwd_path = f"/instance/snapshot/{id}"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_compute.delete("/snapshot/{id}")
async def delete_compute_snapshot(req: Request, id: str):
    fwd_path = f"/instance/snapshot/{id}"
    return await api.op_api(req, "delete", "cms-backup", fwd_path)


# compute:backup
@router_compute.get("/backup")
async def get_compute_backups(req: Request):
    fwd_path = "/instance/backup"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_compute.post("/backup")
async def post_compute_backup(req: Request):
    fwd_path = "/instance/backup"
    return await api.op_api(req, "post", "cms-backup", fwd_path)


@router_compute.get("/backup/{id}")
async def get_compute_backup(req: Request, id: str):
    fwd_path = f"/instance/backup/{id}"
    return await api.op_api(req, "get", "cms-backup", fwd_path)


@router_compute.put("/backup/{id}")
async def put_compute_backup(req: Request, id: str):
    fwd_path = f"/instance/backup/{id}"
    return await api.op_api(req, "put", "cms-backup", fwd_path)


@router_compute.delete("/backup/{id}")
async def delete_compute_backup(req: Request, id: str):
    fwd_path = f"/instance/backup/{id}"
    return await api.op_api(req, "delete", "cms-backup", fwd_path)

@router_compute.post("/backup/{id}/action")
async def post_compute_backup_action(req: Request, id: str):
    fwd_path = f"/instance/backup/{id}/action"
    return await api.op_api(req, "post", "cms-backup", fwd_path)

# hypervisor
@router_compute.get("/hypervisor")
async def get_compute_hypervisors(req: Request):
    fwd_path = "/os-hypervisors/detail"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.get("/hypervisor/{id}")
async def get_compute_hypervisors(req: Request, id: str):
    fwd_path = f"/os-hypervisors/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)

# aggregation
@router_compute.get("/aggregate")
async def get_compute_aggregates(req: Request):
    fwd_path = "/os-aggregates"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.post("/aggregate")
async def post_compute_aggregate(req: Request):
    fwd_path = "/os-aggregates"
    return await api.op_api(req, "post", "compute", fwd_path)

@router_compute.get("/aggregate/{id}")
async def get_compute_aggregate(req: Request, id: str):
    fwd_path = f"/os-aggregates/{id}"
    return await api.op_api(req, "get", "compute", fwd_path)

@router_compute.put("/aggregate/{id}")
async def put_compute_aggregate(req: Request, id: str):
    fwd_path = f"/os-aggregates/{id}"
    return await api.op_api(req, "put", "compute", fwd_path)

@router_compute.delete("/aggregate/{id}")
async def delete_compute_aggregate(req: Request, id: str):
    fwd_path = f"/os-aggregates/{id}"
    return await api.op_api(req, "delete", "compute", fwd_path)

@router_compute.post("/aggregate/{id}/action")
async def post_compute_aggregate_action(req: Request, id: str):
    fwd_path = f"/os-aggregates/{id}/action"
    return await api.op_api(req, "post", "compute", fwd_path)

