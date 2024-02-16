import api
import hmac
import hashlib
from common import config, util
from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import RedirectResponse


router_identity = APIRouter(prefix="/v1/identity", tags=["identity"])


@router_identity.post("/auth/token")
async def post_identity_auth_token(req: Request):
    return await api.api_auth_token(req)


@router_identity.delete("/auth/token")
async def delete_identity_auth_token(req: Request):
    fwd_path = f"/v3/auth/tokens"
    return await api.op_api(req, "delete", "identity", fwd_path)


@router_identity.get("/user/{id}/project")
async def get_identity_user_project(req: Request, id: str):
    fwd_path = f"/v3/users/{id}/projects"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.get("/user")
async def get_users(req: Request):
    fwd_path = f"/v3/users"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.delete("/user/{id}")
async def delete_user(req: Request, id: str):
    fwd_path = f"/v3/users/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)


@router_identity.post("/user")
async def post_user(req: Request):
    fwd_path = f"/v3/users"
    return await api.op_api(req, "post", "identity", fwd_path)


@router_identity.get("/user/{id}")
async def get_user_profile(req: Request, id: str):
    fwd_path = f"/v3/users/{id}"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.put("/user/{id}")
async def put_user_profile(req: Request, id: str):
    fwd_path = f"/v3/users/{id}"
    return await api.op_api(req, "patch", "identity", fwd_path)


@router_identity.post("/user/{id}/password")
async def post_user_password(req: Request, id: str):
    fwd_path = f"/v3/users/{id}/password"
    return await api.op_api(req, "post", "identity", fwd_path)


# identity: application credential
@router_identity.get("/user/{id}/application-credential")
async def get_user_application_credentials(req: Request, id: str):
    fwd_path = f"/v3/users/{id}/application_credentials"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.post("/user/{id}/application-credential")
async def post_user_application_credential(req: Request, id: str):
    fwd_path = f"/v3/users/{id}/application_credentials"
    return await api.op_api(req, "post", "identity", fwd_path)


@router_identity.get("/user/{id}/application-credential/{app_id}")
async def get_user_application_credential(req: Request, id: str, app_id: str):
    fwd_path = f"/v3/users/{id}/application_credentials/{app_id}"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.delete("/user/{id}/application-credential/{app_id}")
async def delete_user_application_credential(req: Request,
                                             id: str, app_id: str):
    fwd_path = f"/v3/users/{id}/application_credentials/{app_id}"
    return await api.op_api(req, "delete", "identity", fwd_path)


# domain
@router_identity.get("/domain")
async def get_identity_domains(req: Request):
    fwd_path = f"/v3/domains"
    return await api.op_api(req, "get", "identity", fwd_path)


@router_identity.get("/domain/{id}")
async def get_identity_domain(req: Request, id: str):
    fwd_path = f"/v3/domains/{id}"
    return await api.op_api(req, "get", "identity", fwd_path)

# projects
@router_identity.get("/project")
async def get_identity_projects(req: Request):
    fwd_path = "/v3/projects"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.get("/project/{id}")
async def get_identity_project(req: Request, id: str):
    fwd_path = f"/v3/projects/{id}"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.post("/project")
async def post_identity_project(req: Request):
    fwd_path = "/v3/projects"
    return await api.op_api(req, "post", "identity", fwd_path)

@router_identity.put("/project/{id}")
async def put_identity_project(req: Request, id: str):
    fwd_path = f"/v3/projects/{id}"
    return await api.op_api(req, "patch", "identity", fwd_path)

@router_identity.delete("/project/{id}")
async def delete_identity_project(req: Request, id: str):
    fwd_path = f"/v3/projects/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)

@router_identity.get("/federation/project")
async def get_identity_federation_projects(req: Request):
    fwd_path = "/v3/OS-FEDERATION/projects"
    return await api.op_api(req, "get", "identity", fwd_path)

# group
@router_identity.post("/group")
async def post_identity_group(req: Request):
    fwd_path = "/v3/groups"
    return await api.op_api(req, "post", "identity", fwd_path)

@router_identity.get("/group/{gid}/user/{uid}")
async def get_identity_group_admin(req: Request, gid: str, uid: str):
    fwd_path = f"/v3/groups/{gid}/users/{uid}"
    return await api.op_api(req, "head", "identity", fwd_path)

@router_identity.get("/group/{id}/user")
async def get_identity_group_users(req: Request, id: str):
    fwd_path = f"/v3/groups/{id}/users"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.get("/group")
async def get_identity_groups(req: Request):
    fwd_path = "/v3/groups"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.get("/group/{id}")
async def get_identity_group(req: Request, id: str):
    fwd_path = f"/v3/groups/{id}"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.put("/group/{id}")
async def update_identity_group(req: Request, id: str):
    fwd_path = f"/v3/groups/{id}"
    return await api.op_api(req, "patch", "identity", fwd_path)

@router_identity.delete("/group/{id}")
async def delete_identity_group(req: Request, id: str):
    fwd_path = f"/v3/groups/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)

@router_identity.put("/group/{gid}/user/{uid}")
async def put_identity_group_user(req: Request, gid: str, uid: str):
    fwd_path = f"/v3/groups/{gid}/users/{uid}"
    return await api.op_api(req, "put", "identity", fwd_path)

@router_identity.delete("/group/{gid}/user/{uid}")
async def delete_identity_group_user(req: Request, gid: str, uid: str):
    fwd_path = f"/v3/groups/{gid}/users/{uid}"
    return await api.op_api(req, "delete", "identity", fwd_path)


# role
@router_identity.get("/role/assignment")
async def get_identity_role_assignment(req: Request):
    fwd_path = "/v3/role_assignments"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.get("/role")
async def get_identity_roles(req: Request):
    fwd_path = "/v3/roles"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.post("/role")
async def post_identity_role(req: Request):
    fwd_path = "/v3/roles"
    return await api.op_api(req, "post", "identity", fwd_path)

@router_identity.get("/role/{id}")
async def get_identity_role(req: Request, id: str):
    fwd_path = f"/v3/roles/{id}"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.put("/role/{id}")
async def put_identity_role(req: Request, id: str):
    fwd_path = f"/v3/roles/{id}"
    return await api.op_api(req, "patch", "identity", fwd_path)

@router_identity.delete("/role/{id}")
async def delete_identity_role(req: Request, id: str):
    fwd_path = f"/v3/roles/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)

@router_identity.get("/role/project/{pid}/user/{uid}")
async def get_identity_role_project_user(req: Request, 
        pid: str, uid: str):
    fwd_path = f"/v3/projects/{pid}/users/{uid}/roles"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.delete("/role/{id}/project/{pid}/user/{uid}")
async def delete_identity_role_project_user(req: Request, 
        pid: str, uid: str, id: str):
    fwd_path = f"/v3/projects/{pid}/users/{uid}/roles/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)

@router_identity.put("/role/{id}/project/{pid}/user/{uid}")
async def put_identity_role_project_user(req: Request, 
        pid: str, uid: str, id: str):
    fwd_path = f"/v3/projects/{pid}/users/{uid}/roles/{id}"
    return await api.op_api(req, "put", "identity", fwd_path)
    
@router_identity.get("/role/project/{pid}/group/{uid}")
async def get_identity_role_project_group(req: Request, pid: str, uid: str):
    fwd_path = f"/v3/projects/{pid}/groups/{uid}/roles"
    return await api.op_api(req, "get", "identity", fwd_path)

@router_identity.delete("/role/{id}/project/{pid}/group/{uid}")
async def delete_identity_role_project_group(req: Request, 
        pid: str, uid: str, id: str):
    fwd_path = f"/v3/projects/{pid}/groups/{uid}/roles/{id}"
    return await api.op_api(req, "delete", "identity", fwd_path)

@router_identity.put("/role/{id}/project/{pid}/group/{uid}")
async def put_identity_role_project_group(req: Request, 
        pid: str, uid: str, id: str):
    fwd_path = f"/v3/projects/{pid}/groups/{uid}/roles/{id}"
    return await api.op_api(req, "put", "identity", fwd_path)


'''
SAML login
'''

@router_identity.post("/auth/saml/login")
async def post_saml_login(req: Request):
    # SP ACS (login) registered in IDP
    fwd_path = "/v1/identity/auth/saml/login"
    return await api.api_auth_saml_login(req, fwd_path)

    
@router_identity.get("/auth/saml/websso")
async def get_saml_redirect(req: Request):
    # For portal, to generate AuthnRequest when login,
    # redirect user to idp login
    idp_name = config.config["DEFAULT"]["idp-name"]
    fwd_path = "/auth/OS-FEDERATION/identity_providers" + \
            f"/{idp_name}/protocols/saml2/websso" + \
            f"?{req.query_params}"
    return await api.api_auth_saml_redirect(req, fwd_path)


@router_identity.post("/auth/saml")
async def post_saml_token(req: Request):
    # for sso_callback_template.html use, it will submit a form contains 
    # federated token and csrf which is added insert_csrf_token @ identity.py
    payload = await req.body()
    payload = payload.decode()
    
    if "&CSRF=" in payload and "token=" in payload:
        token_str = payload.split("token=")[1].split("&CSRF=")[0]
        csrf = payload.split("token=")[1].split("&CSRF=")[1]
    
        # validation
        key = config.config["DEFAULT"]["doc-url"].encode()
        msg = token_str.encode()
        valid_csrf = hmac.new(key, msg, hashlib.sha256).hexdigest()

        if(csrf == valid_csrf):
            # redirect portal to login page, 
            # and pass federated token via cookie.
            redirect = RedirectResponse(url="/login", status_code=302)
            redirect.set_cookie(key="LOGIN_INFO", value=token_str)
            return redirect
    else:
        return util.response(401, data={"message": "Auth token is missing!"})
    
