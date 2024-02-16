import os
import logging
import json

from common import util
from common.resource_base import ResourceBase

log = logging.getLogger("uvicorn")


class ResourceBaseTF(ResourceBase):
    def __init__(self, token_pack, res_name):
        super().__init__(token_pack, res_name)
        self.res_name = res_name
        self.token_pack = token_pack
        self.token = token_pack["token"]
        self.project_id = token_pack["project"]["id"]
        self.role_admin = False
        self.cluster_path = None
        self.build_log = None
        self.tf_path = None
        self.tf_path_svc = None
        self.data = None
        self.res_path = None
        self.j2_env = None
        self.data_svc = None
        for role in token_pack["roles"]:
            if role["name"] == "admin":
                self.role_admin = True
                break

    async def get(self, id):
        if not os.path.exists(f"{self.cluster_path}/{id}"):
            return {"status": 404}
        with open(f"{self.cluster_path}/{id}/cluster.data") as fd:
            data = json.load(fd)
        return {"status": 200, "data": {self.res_name: data}}

    async def get_list(self, query={}):
        objs = []
        if (not self.role_admin) or ("all_projects" not in query):
            query["project_id"] = self.project_id
        for id in os.listdir(self.cluster_path):
            with open(f"{self.cluster_path}/{id}/cluster.data") as fd:
                data = json.load(fd)
            for key in query.keys():
                if query[key] and (data[key] != query[key]):
                    break
            else:
                objs.append(data)
        return {"status": 200, "data": {self.res_name + "s": objs}}

    async def init_tf_plugin(self, path):
        provider = "registry.terraform.io/" \
                "terraform-provider-openstack/openstack/" \
                "1.49.0/linux_amd64"
        plugin_file = "terraform-provider-openstack_v1.49.0"
        cmd = f"mkdir -p {path}/.provider/{provider}"
        await util.exec_cmd(cmd)
        cmd = f"curl http://depot/{provider}/{plugin_file}" \
                f" -o {path}/.provider/{provider}/{plugin_file}"
        await util.exec_cmd(cmd)
        cmd = f"chmod +x {path}/.provider/{provider}/{plugin_file}"
        await util.exec_cmd(cmd)
        cmd = f"terraform -chdir={path} init -no-color" \
                f" -plugin-dir={path}/.provider"
        with open(self.build_log, "a") as fd:
            fd.write(f"ID: {self.data['id']}\n")
            rc = await util.exec_cmd(cmd, output_file=fd)
        if rc:
            log.error(f"Terraform init failed!")
            return rc

    async def init_tf(self):
        log.info(f"Check {self.tf_path}.")
        if not os.path.exists(f"{self.tf_path}/version.tf"):
            t = self.j2_env.get_template("version.tf.j2")
            with open(f"{self.tf_path}/version.tf", "w") as fd:
                fd.write(t.render(self.data))
        if not os.path.exists(f"{self.tf_path}/.terraform"):
            rc = await self.init_tf_plugin(self.tf_path)
            if rc:
                return rc
        if not os.path.exists(f"{self.tf_path}/data.tf"):
            t = self.j2_env.get_template("data.tf.j2")
            with open(f"{self.tf_path}/data.tf", "w") as fd:
                fd.write(t.render(self.data))

    async def init_tf_service(self):
        log.info(f"Check {self.tf_path_svc}.")
        if not os.path.exists(f"{self.tf_path_svc}/version.tf"):
            t = self.j2_env.get_template("version.tf.j2")
            with open(f"{self.tf_path_svc}/version.tf", "w") as f:
                f.write(t.render(self.data_svc))
        if not os.path.exists(f"{self.tf_path_svc}/.terraform"):
            rc = await self.init_tf_plugin(self.tf_path_svc)
            if rc:
                return rc

    async def update_tf_token(self, token):
        log.info("Update Terraform token.")
        version = f"{self.tf_path}/version.tf"
        cmd = f"sed -i 's/^.*token.*/    token = \"{token}\"/g' {version}"
        await util.exec_cmd(cmd)

    def update_cluster_data(self, update):
        with open(f"{self.res_path}/cluster.data") as fd:
            cluster_data = json.load(fd)
        for key in update.keys():
            cluster_data[key] = update[key]
        cluster_data["time_update"] = util.get_time()
        with open(f"{self.res_path}/cluster.data", "w") as fd:
            json.dump(cluster_data, fd)

    async def terraform_apply(self, tf_path, extra_args = ""):
        log.info(f"Terraform plan {tf_path}.")
        cmd = f"terraform -chdir={tf_path} plan -no-color -out=tfplan" \
                f" {extra_args}"
        with open(self.build_log, "a") as fd:
            fd.write(f"ID: {self.data['id']}\n")
            rc = await util.exec_cmd(cmd, output_file=fd)
        if rc:
            log.error(f"Create Terraform plan {tf_path} failed!")
            return rc
        log.info(f"Terraform apply {tf_path}.")
        cmd = f"terraform -chdir={tf_path} apply -parallelism=1" \
                " -no-color tfplan"
        with open(self.build_log, "a") as fd:
            fd.write(f"ID: {self.data['id']}\n")
            rc = await util.exec_cmd(cmd, output_file=fd)
        if rc:
            log.error(f"Apply Terraform plan {tf_path} failed!")
            return rc

    async def terraform_destroy(self, tf_path, extra_args=""):
        if not os.path.exists(f"{tf_path}/terraform.tfstate"):
            return
        cmd = f"terraform -chdir={tf_path} apply -no-color -destroy" \
                f" -auto-approve {extra_args}"
        with open(self.build_log, "a") as fd:
            fd.write(f"ID: {self.data['id']}\n")
            rc = await util.exec_cmd(cmd, output_file=fd)
        if rc:
            log.error(f"Terraform destory {tf_path} failed!")
            return rc

