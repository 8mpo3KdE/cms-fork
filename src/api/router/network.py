from fastapi import APIRouter
from fastapi.requests import Request

import api

router_network = APIRouter(prefix="/v1/network", tags=["network"])


# quota
@router_network.get("/{project_id}/limit")
async def get_network_limit(req: Request, project_id: str):
    fwd_path = f"/v2.0/quotas/{project_id}/details.json"
    return await api.op_api(req, "get", "network", fwd_path)

@router_network.get("/quota-set/{id}")
async def get_network_quota_sets(req: Request, id: str):
    fwd_path = f"/v2.0/quotas/{id}"
    return await api.op_api(req, "get", "network", fwd_path)

@router_network.put("/quota-set/{id}")
async def put_network_quota_set(req: Request, id: str):
    fwd_path = f"/v2.0/quotas/{id}"
    return await api.op_api(req, "put", "network", fwd_path)

# network:network
@router_network.get("/network")
async def get_network_networks(req: Request):
    fwd_path = "/v2.0/networks"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.get("/network/{id}")
async def get_network_network(req: Request, id: str):
    fwd_path = f"/v2.0/networks/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/network")
async def post_network_network(req: Request):
    fwd_path = "/v2.0/networks"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.put("/network/{id}")
async def put_network_network(req: Request, id: str):
    fwd_path = f"/v2.0/networks/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/network/{id}")
async def delete_network_network(req: Request, id: str):
    fwd_path = f"/v2.0/networks/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:subnet
@router_network.get("/subnet")
async def get_network_subnets(req: Request):
    fwd_path = "/v2.0/subnets"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.get("/subnet/{id}")
async def get_network_subnet(req: Request, id: str):
    fwd_path = f"/v2.0/subnets/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/subnet")
async def post_network_subnet(req: Request):
    fwd_path = "/v2.0/subnets"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.put("/subnet/{id}")
async def put_network_subnet(req: Request, id: str):
    fwd_path = f"/v2.0/subnets/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/subnet/{id}")
async def delete_network_subnet(req: Request, id: str):
    fwd_path = f"/v2.0/subnets/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:port
@router_network.get("/port")
async def get_network_ports(req: Request):
    fwd_path = f"/v2.0/ports"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.get("/port/{id}")
async def get_network_port(req: Request, id: str):
    fwd_path = f"/v2.0/ports/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/port")
async def post_network_network(req: Request):
    fwd_path = "/v2.0/ports"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.put("/port/{id}")
async def put_network_port(req: Request, id: str):
    fwd_path = f"/v2.0/ports/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/port/{id}")
async def delete_network_port(req: Request, id: str):
    fwd_path = f"/v2.0/ports/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:security group
@router_network.get("/security-group")
async def get_network_security_group(req: Request):
    fwd_path = "/v2.0/security-groups"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/security-group")
async def post_network_security_group(req: Request):
    fwd_path = "/v2.0/security-groups"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.delete("/security-group/{id}")
async def delete_network_security_group(req: Request, id: str):
    fwd_path = f"/v2.0/security-groups/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


@router_network.post("/security-group-rule")
async def post_network_security_group_rules(req: Request):
    fwd_path = "/v2.0/security-group-rules"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.delete("/security-group-rule/{id}")
async def delete_network_security_group_rules(req: Request, id: str):
    fwd_path = f"/v2.0/security-group-rules/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:floating-ip
@router_network.get("/floating-ip")
async def get_network_floating_ips(req: Request):
    fwd_path = "/v2.0/floatingips"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.get("/floating-ip/{id}")
async def get_network_floating_ip(req: Request, id: str):
    fwd_path = f"/v2.0/floatingips/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/floating-ip")
async def post_network_floating_ip(req: Request):
    fwd_path = "/v2.0/floatingips"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.put("/floating-ip/{id}")
async def put_network_floating_ip(req: Request, id: str):
    fwd_path = f"/v2.0/floatingips/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/floating-ip/{id}")
async def delete_network_floating_ip(req: Request, id: str):
    fwd_path = f"/v2.0/floatingips/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# port-forwarding
@router_network.get("/floating-ip/{fip_id}/port-forward")
async def get_fip_port_forwards(req: Request, fip_id: str):
    fwd_path = f"/v2.0/floatingips/{fip_id}/port_forwardings"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.post("/floating-ip/{fip_id}/port-forward")
async def post_fip_port_forward(req: Request, fip_id: str):
    fwd_path = f"/v2.0/floatingips/{fip_id}/port_forwardings"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.get("/floating-ip/{fip_id}/port-forward/{id}")
async def get_fip_port_forward(req: Request, fip_id: str, id: str):
    fwd_path = f"/v2.0/floatingips/{fip_id}/port_forwardings/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.put("/floating-ip/{fip_id}/port-forward/{id}")
async def put_fip_port_forward(req: Request, fip_id: str, id: str):
    fwd_path = f"/v2.0/floatingips/{fip_id}/port_forwardings/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/floating-ip/{fip_id}/port-forward/{id}")
async def delete_fip_port_forward(req: Request, fip_id: str, id: str):
    fwd_path = f"/v2.0/floatingips/{fip_id}/port_forwardings/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:router
@router_network.get("/router")
async def get_router_networks(req: Request):
    fwd_path = "/v2.0/routers"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.get("/router/{id}")
async def get_router_network(req: Request, id: str):
    fwd_path = f"/v2.0/routers/{id}"
    return await api.op_api(req, "get", "network", fwd_path)


@router_network.put("/router/{id}")
async def put_router_network(req: Request, id: str):
    fwd_path = f"/v2.0/routers/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.post("/router")
async def post_router_network(req: Request):
    fwd_path = "/v2.0/routers"
    return await api.op_api(req, "post", "network", fwd_path)


@router_network.post("/router/{id}/action")
async def post_router_network_action(req: Request, id: str):
    fwd_path = f"/v2.0/routers/{id}"
    return await api.op_api(req, "put", "network", fwd_path)


@router_network.delete("/router/{id}")
async def delete_router_network(req: Request, id: str):
    fwd_path = f"/v2.0/routers/{id}"
    return await api.op_api(req, "delete", "network", fwd_path)


# network:load balancer
@router_network.get("/load-balancer")
async def get_network_load_balancers(req: Request):
    fwd_path = "/v2/lbaas/loadbalancers"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer")
async def post_network_load_balancer(req: Request):
    fwd_path = "/v2/lbaas/loadbalancers"
    return await api.op_api(req, "post", "load-balancer", fwd_path)

@router_network.put("/load-balancer/{id}")
async def put_network_load_balancer(req: Request, id: str):
    fwd_path = f"/v2/lbaas/loadbalancers/{id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/{id}")
async def delete_network_load_balancer(req: Request, id: str):
    fwd_path = f"/v2/lbaas/loadbalancers/{id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


# network load balancer flavors/spec
@router_network.get("/load-balancer/spec")
async def get_network_load_balancer_specs(req: Request):
    fwd_path = "/v2.0/lbaas/flavors"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.get("/load-balancer/spec/{id}")
async def get_network_load_balancer_spec(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/flavors/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


# network load balancer flavors/availability-zone
@router_network.get("/load-balancer/availability-zone")
async def get_network_load_balancer_availability_zones(req: Request):
    fwd_path = "/v2.0/lbaas/availabilityzones"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.get("/load-balancer/availability-zone/{id}")
async def get_network_load_balancer_availability_zone(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/availabilityzones/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


# network load balancer listener
@router_network.get("/load-balancer/listener")
async def get_network_load_balancer_listener(req: Request):
    fwd_path = "/v2.0/lbaas/listeners"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/listener")
async def post_network_load_balancer_listeners(req: Request):
    fwd_path = "/v2.0/lbaas/listeners"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/listener/{id}")
async def get_network_load_balancer_listener(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/listeners/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/listener/{id}")
async def delete_network_load_balancer_listener(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/listeners/{id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/listener/{id}")
async def put_network_load_balancer_listener(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/listeners/{id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


# network load balancer pool
@router_network.get("/load-balancer/pool")
async def get_network_load_balancer_pools(req: Request):
    fwd_path = "/v2.0/lbaas/pools"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/pool")
async def post_network_load_balancer_pool(req: Request):
    fwd_path = "/v2.0/lbaas/pools"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/pool/{id}")
async def get_network_load_balancer_pool(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/pool/{id}")
async def delete_network_load_balancer_pool(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/pool/{id}")
async def put_network_load_balancer_pool(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


# network load balancer pool member
@router_network.get("/load-balancer/pool/{id}/member")
async def get_network_load_balancer_pool_members(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}/members"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/pool/{id}/member")
async def post_network_load_balancer_pool_member(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}/members"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/pool/{id}/member/{m_id}")
async def get_network_load_balancer_pool_member(req: Request,
        id: str, m_id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}/members/{m_id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/pool/{id}/member/{m_id}")
async def delete_network_load_balancer_pool_member(req: Request,
        id: str, m_id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}/members/{m_id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/pool/{id}/member/{m_id}")
async def put_network_load_balancer_pool_member(req: Request,
        id: str, m_id: str):
    fwd_path = f"/v2.0/lbaas/pools/{id}/members/{m_id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


# network load balancer l7policies
@router_network.get("/load-balancer/l7policies")
async def get_network_load_balancer_l7policies(req: Request):
    fwd_path = "/v2.0/lbaas/l7policies"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/l7policies")
async def post_network_load_balancer_l7policies(req: Request):
    fwd_path = "/v2.0/lbaas/l7policies"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/l7policies/{id}")
async def get_network_load_balancer_l7policy(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/l7policies/{id}")
async def delete_network_load_balancer_l7policies(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/l7policies/{id}")
async def put_network_load_balancer_l7policies(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


# network load balancer l7policies rules
@router_network.get("/load-balancer/l7policies/{id}/rule")
async def get_network_load_balancer_l7policies_rules(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}/rules"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/l7policies/{id}/rule")
async def post_network_load_balancer_l7policies_rule(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}/rules"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/l7policies/{id}/rule/{rule_id}")
async def get_network_load_balancer_l7policies_rule(req: Request,
        id: str, rule_id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}/rules/{rule_id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/l7policies/{id}/rule/{rule_id}")
async def delete_network_lb_l7_rule(req: Request, id: str, rule_id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}/rules/{rule_id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/l7policies/{id}/rule/{rule_id}")
async def put_network_lb_l7_rule(req: Request, id: str, rule_id: str):
    fwd_path = f"/v2.0/lbaas/l7policies/{id}/rules/{rule_id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


# network load balancer health monitor
@router_network.get("/load-balancer/health-monitor")
async def get_network_load_balancer_healthmonitor(req: Request):
    fwd_path = "/v2.0/lbaas/healthmonitors"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.post("/load-balancer/health-monitor")
async def post_network_load_balancer_healthmonitors(req: Request):
    fwd_path = "/v2.0/lbaas/healthmonitors"
    return await api.op_api(req, "post", "load-balancer", fwd_path)


@router_network.get("/load-balancer/health-monitor/{id}")
async def get_network_load_balancer_healthmonitor(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/healthmonitors/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)


@router_network.delete("/load-balancer/health-monitor/{id}")
async def delete_network_load_balancer_healthmonitor(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/healthmonitors/{id}"
    return await api.op_api(req, "delete", "load-balancer", fwd_path)


@router_network.put("/load-balancer/health-monitor/{id}")
async def put_network_load_balancer_healthmonitor(req: Request, id: str):
    fwd_path = f"/v2.0/lbaas/healthmonitors/{id}"
    return await api.op_api(req, "put", "load-balancer", fwd_path)


@router_network.get("/load-balancer/{id}")
async def get_network_load_balancer(req: Request, id: str):
    fwd_path = f"/v2/lbaas/loadbalancers/{id}"
    return await api.op_api(req, "get", "load-balancer", fwd_path)

