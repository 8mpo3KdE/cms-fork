# API

# 1 Provider

API can be provided by a single interface (API Gateway) or by each service individually. To support web portal, a portal API gateway is required to avoid CORS. As the API client, using service API directly would be a better option.


## 1.1 API Gateway

Provide the following supports to portal.

* For browser to download the portal.
```
portal.zone/
```

* Utilities for the portal.
```
portal.zone/health
portal.zone/config
```

* Portal route from browser (page refresh)
```
portal.zone/<portal route>

portal.zone/login
portal.zone/compute/instance
```

* API for portal to access backend services without CORS.
```
portal.zone/<version>/<service>/<resource>

portal.zone/v1/compute/instance
```


## 1.2 Service API

The API provided by each service, separated by port or address. This is the backend of API gateway.

Separated by port.
```
api.zone:<service-port>/version/<resource>
```

Separated by address.
```
compute.api.zone/version/<resource>
network.api.zone/version/<resource>
```


# 2 REST API

```
/
/health
/config
/<version>/<service>/<resource>
/<version>/<service>/<resource>/<id>/action
/<version>/<service>/<resource>/<id>/<child>
```

Delimiter in resource name in API path is `-`.
Delimiter in resource name in request or response data is `_`.


## 2.1 Resource

### 2.1.1 GET

Get the list of resource.
```
GET /<version>/<service>/<resource>
Response status: 200
Response data:
{
    "<resource>s": [
        {
            <resource data>
        },
        {
            <resource data>
        },
        ...
    ]
}
```

Get the specific resource.
```
GET /<version>/<service>/<resource>/<id>
Response status: 200
Response data:
{
    "<resource>": {
        <resource data>
    }
}
```


### 2.1.2 POST

Create a resource.
```
POST /<version>/<service>/<resource>
Request data:
{
    "<resource>": {
        <argument1>,
        <argument2>,
        ...
    }
}
Response status: 201
Response data:
{
    "<resource>": {
        "id": "<resource id>"
    }
}
```


### 2.1.3 PUT

Update the specific resource.
```
PUT /<version>/<service>/<resource>/<id>
Request data:
{
    "<resource>": {
        <argument>,
        <argument>,
        ...
    }
}
Response status: 201
Response data:
{
    "<resource>": {
        <resource data>
    }
}
```


### 2.1.4 DELETE

Delete the specific resource.
```
DELETE /<version>/<service>/<resource>/<id>
Response status: 201
Response data:
{
    "<resource>": {
        "id": "<resource id>"
    }
}
```


## 2.2 Action

Execute an action on the specific resource.
```
POST /<version>/<service>/<resource>/<id>/action
Request data:
{
    "<action_name>": {
        <argument1>,
        <argument2>,
        ...
    }
}
Response status: 201
Response data:
{
    "<resource>": {
        "id": "<resource id>"
    }
}
```
The same URL for all actions. The specific action name is in request data.


## 2.3 Resource property

In case resource property needs to be CRUDed, like metadata, instance interface, instance block device, etc., do that as manage resource.

Get the list of property items.
```
GET /<version>/<service>/<resource>/<id>/<property>
```

Get a specific property item.
```
GET /<version>/<service>/<resource>/<id>/<property>/<key/id>
```

Add one or multiple property items.
```
POST /<version>/<service>/<resource>/<id>/<property>
```

Update property items.
```
PUT /<version>/<service>/<resource>/<id>/<property>
```

Update a specific property item.
```
PUT /<version>/<service>/<resource>/<id>/<property>/<key/id>
```

Delete a specific property item.
```
DELETE /<version>/<service>/<resource>/<id>/<property>/<key/id>
```

Here is an example of instance metadata.
```
GET /v1/compute/instance/<id>/metadata
GET /v1/compute/instance/<id>/metadata/<key>
POST /v1/compute/instance/<id>/metadata
PUT /v1/compute/instance/<id>/metadata
PUT /v1/compute/instance/<id>/metadata/<key>
DELETE /v1/compute/instance/<id>/metadata/<key>
```

Here is an example of instance interface.
```
GET /v1/compute/instance/<id>/interface
GET /v1/compute/instance/<id>/interface/<id>
POST /v1/compute/instance/<id>/interface
PUT /v1/compute/instance/<id>/interface
PUT /v1/compute/instance/<id>/interface/<id>
DELETE /v1/compute/instance/<id>/interface/<id>
```


## 2.4 Return code

```
400: bad request (invalid parameter)
401: unauthorized
404: not found (resource not found)
409: conflict (no reuqired resource status or dependency)
```


# 3 Example

```
/v1/identity/auth/token

/v1/compute/spec
/v1/compute/instance

/v1/image/image

/v1/network/network
/v1/network/subnet
/v1/network/port
/v1/network/security-group

/v1/block/volume

/v1/backup/volume
/v1/backup/instance

/v1/snapshot/volume
/v1/snapshot/instance

/v1/plan/volume-backup
/v1/plan/volume-backup/<id>/volume
/v1/plan/volume-snapshot
/v1/plan/volume-snapshot/<id>/volume
/v1/plan/instance-backup
/v1/plan/instance-backup/<id>/instance
/v1/plan/instance-snapshot
/v1/plan/instance-snapshot/<id>/instance
POST data: {"instance_snapshot": {......}}

/v1/kubernetes/cluster
POST data: {"cluster": {......}}

/v1/nfs/cluster
POST data: {"cluster": {......}}

/v1/monitor/cluster
POST data: {"cluster": {......}}

```

Resource name is unique under each service, not necessary to be unique globally.

