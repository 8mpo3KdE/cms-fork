from setuptools import find_namespace_packages, setup

setup(
    name="cloudms",
    description="Cloud Managed Service",
    author="contributor",
    author_email="contributor@cloud.svc",
    url="https://github.com/cms",
    version="__version__",
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "api.static": ["*"],
        "api.static.assets": ["*"],
        "builder": ["*"],
        "builder.nfs-template": ["*"],
        "builder.mariadb-template": ["*"],
        "builder.postgresql-template": ["*"],
        "builder.redis-template": ["*"],
        "builder.kafka-template": ["*"],
        "builder.rabbitmq-template": ["*"],
        "builder.harbor-template": ["*"],
        "builder.k8s-template": ["*"],
        "builder.k8s-template.ingress": ["*"],
        "builder.k8s-template.resource": ["*"],
        "builder.k8s-template.cloud-provider-openstack.cinder-csi-plugin": ["*"],
        "builder.k8s-template.cloud-provider-openstack.controller-manager": ["*"],
        "client": ["*"],
        "cloudshell.static": ["*"],
        "cloudshell.static.css": ["*"],
        "cloudshell.static.js": ["*"],
        "monitor.monitor-template": ["*"]
    },
    include_package_data=True
)

