# Plan Service

Service URL/endpoint.
```
api.<zone>:8118/v1
```


# 1 Snapshot plan

Support the following types of resource.
* volume
* instance


## 1.1 API

Get the list of snapshot plans.
```
GET /snapshot-plan
Response status: 200
Response data:
{
    "snapshot_plans": [
        {...},
        {...},
        {...}
    ]
}
```

Get a specific snapshot plan.
```
GET /snapshot-plan/<id>
Response status: 200, 404
Response data:
{
    "snapshot_plan": {
        ......
    }
}
```

Create a snapshot plan.
```
POST /snapshot-plan
Request data:
{
    "snapshot_plan": {
        <arguments>
    }
}
Response status: 201
Response data:
{
    "snapshot_plan": {
        "id": <id>
    }
}
```

Action on snapshot plan.
```
POST /snapshot-plan/<id>/action
Request data:
{
    "execute": {
        <arguments>
    }
}
Response status: 201
```

Delete a snapshot plan.
```
DELETE /snapshot-plan/<id>
Response status: 201
Response data:
{
    "snapshot_plan": {
        "id": <id>
    }
}
```


## 1.2 API Gateway

Version is included in the URL/endpoint of API gateway and backend service.
```
GET <API gateway>/plan/snapshot-plan
-> GET <plan>/snapshot-plan

GET <API gateway>/plan/snapshot-plan/<id>
-> GET <plan>/snapshot-plan/<id>

POST <API gateway>/plan/snapshot-plan
-> POST <plan>/snapshot-plan

POST <API gateway>/plan/snapshot-plan/<id>/action
-> POST <backup>/snapshot-plan/<id>/action

DELETE <API gateway>/plan/snapshot-plan/<id>
-> DELETE <plan>/snapshot-plan/<id>
```


# 2 Backup plan

## 2.1 API

Get the list of backup plans.
```
GET /backup-plan
Response status: 200
Response data:
{
    "backup_plans": [
        {...},
        {...},
        {...}
    ]
}
```

Get a specific backup plan.
```
GET /backup-plan/<id>
Response status: 200, 404
Response data:
{
    "backup_plan": {
        ......
    }
}
```

Create a backup plan.
```
POST /backup-plan
Request data:
{
    "backup_plan": {
        <arguments>
    }
}
Response status: 201
Response data:
{
    "backup_plan": {
        "id": <id>
    }
}
```

Action on backup plan.
```
POST /backup-plan/<id>/action
Request data:
{
    "execute": {
        <arguments>
    }
}
Response status: 201
```

Delete a backup plan.
```
DELETE /backu-planp/<id>
Response status: 201
Response data:
{
    "backup_plan": {
        "id": <id>
    }
}
```


## 2.2 API Gateway

Version is included in the URL/endpoint of API gateway and backend service.
```
GET <API gateway>/plan/backup-plan
-> GET <plan>/backup-plan

GET <API gateway>/plan/backup-plan/<id>
-> GET <plan>/backup-plan/<id>

POST <API gateway>/plan/backup-plan
-> POST <plan>/backup-plan

POST <API gateway>/plan/backup-plan/<id>/action
-> POST <plan>/backup-plan/<id>/action

DELETE <API gateway>/plan/backup-plan/<id>
-> DELETE <plan>/backup-plan/<id>
```


# 3 Manage resource in plan

## 3.1 API

Get the list of resources in a plan.
```
GET /backup-plan/<plan-id>/resource
GET /snapshot-plan/<plan-id>/resource
Response status: 200
Response data:
{
    "resource": {
        "volumes": [
            {...},
            {...}
        ],
        "instances": [
            {...},
            {...}
        ]
    }
}
```

Add a list of resources in a plan.
```
POST /backup-plan/<plan-id>/resource
POST /snapshot-plan/<plan-id>/resource
Request data:
{
    "resource": {
        "volume_ids": [
            "id1",
            "id2"
        ],
        "instance_ids": [
            "id1",
            "id2"
        ]
    }
}
Response status: 201
```
* For volume plan, only `volume_ids` is accepted.
* For instance plan, only `instance_ids` is accepted.

Remove a resource from a plan.
```
DELETE /backup-plan/<plan-id>/resource/<resource-id>
DELETE /snapshot-plan/<plan-id>/resource/<resource-id>
Response status: 201
```
* For volume plan, `resource-id` is volume ID.
* For instance plan, `resource-id` is instance ID. Backend service will find tagged volumes by instance ID and untag them.


## 3.2 API Gateway

Version is included in the URL/endpoint of API gateway and backend service.
```
GET <API gateway>/plan/snapshot-plan/<plan-id>/resource
-> GET <plan>/snapshot-plan/<plan-id>/resource

POST <API gateway>/plan/snapshot-plan/<plan-id>/resource
-> POST <plan>/snapshot-plan/<plan-id>/resource

DELETE <API gateway>/plan/snapshot-plan/<plan-id>/resource/<resource-id>
-> DELETE <plan>/snapshot-plan/<plan-id>/resource/<resource-id>
```

```
GET <API gateway>/plan/backup-plan/<plan-id>/resource
-> GET <plan>/backup-plan/<plan-id>/resource

POST <API gateway>/plan/backup-plan/<plan-id>/resource
-> POST <plan>/backup-plan/<plan-id>/resource

DELETE <API gateway>/plan/backup-plan/<plan-id>/resource/<resource-id>
-> DELETE <plan>/backup-plan/<plan-id>/resource/<resource-id>
```

