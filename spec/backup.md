# Backup Service

Service URL/endpoint.
```
api.<zone>:8110/v1
```


# 1 Volume

## 1.1 Volume snapshot

Volume snapshot is handled by Cinder. Cinder needs to be aware of volume snapshot so a volume won't be deleted if any snapshot is on it.


## 1.2 Volume backup

Due to some limitation from Cinder Backup service, volume backup is handled by backup service.

Get the list of volume backup.
```
GET /volume/backup
Response status: 200
Response data:
{
    "backups": [
        {...},
        {...},
        {...}
    ]
}
```

Get a specific volume backup.
```
GET /volume/backup/<id>
Response status: 200, 404
Response data:
{
    "backup": {
        ......
    }
}
```

Create a volume backup.
```
POST /volume/backup
Request data:
{
    "backup": {
        <arguments>
    }
}
Response status: 201
Response data:
{
    "backup": {
        "id": <id>
    }
}
```

Action on volume backup.
```
POST /volume/backup/<id>/action
Request data:
{
    "update": {
        <arguments>
    }
}
Response status: 201
```

Delete a volume backup.
```
DELETE /volume/backup/<id>
Response status: 201
Response data:
{
    "backup": {
        "id": <id>
    }
}
```


## 1.3 Volume

To support create volume from a backup, backup service takes the POST request and handles thoes two cases. For all others, backup services forwards the request to Cinder.
```
POST /volume
Request data:
{
    "volume": {
        "backup_id": <id>
    }
}
Response status: 201
```

Cinder revert action requires volume to be available (detached). This is not necessary, volume can be rolled back when instance is power-off. Also, Cinder revert action doesn't support boot volume, which can not be detached.

Given that, rollback/revert action is handled by backup service. To support rollback action to volume, backup service takes all action requests, handles the rollback action. For all other actions, backup service forwards the request to Cinder.
```
POST /volume/<id>/action
Request data:
{
    "rollback": {
        "snapshot_id": <id>
    }
}
Response status: 201
```


## 1.4 API Gateway

Version is included in the URL/endpoint of API gateway and backend service.
```
GET <API gateway>/block/snapshot
-> GET <Cinder>/snapshots

GET <API gateway>/block/snapshot/<id>
-> GET <Cinder>/snapshots/<id>

POST <API gateway>/block/snapshot
-> POST <Cinder>/snapshots

DELETE <API gateway>/block/snapshot/<id>
-> DELETE <Cinder>/snapshots/<id>
```

```
GET <API gateway>/block/backup
-> GET <backup>/volume/backup

GET <API gateway>/block/backup/<id>
-> GET <backup>/volume/backup/<id>

POST <API gateway>/block/backup
-> POST <backup>/volume/backup

POST <API gateway>/block/backup/<id>/action
-> POST <backup>/volume/backup/<id>/action

DELETE <API gateway>/block/backup/<id>
-> DELETE <backup>/volume/backup/<id>
```

```
GET <API gateway>/block/volume
-> GET <Cinder>/volumes

GET <API gateway>/block/volume/<id>
-> GET <Cinder>/volumes/<id>

POST <API gateway>/block/volume
-> POST <Cinder>/volumes
-> POST <backup>/volume

POST <API gateway>/block/volume/<id>/action
-> POST <Cinder>/volumes/<id>/action
-> POST <backup>/volume/<id>/action

DELETE <API gateway>/block/volume/<id>
-> DELETE <Cinder>/volumes/<id>
```


# 2 Instance

The following status are accepted for instance snapshot or backup.
* ACTIVE
* SHUTOFF
* SUSPENDED
* PAUSED


## 2.1 Instance snapshot

Get the list of instance snapshot.
```
GET /instance/snapshot
Response status: 200
Response data:
{
    "snapshots": [
        {...},
        {...},
        {...}
    ]
}
```

Get a specific instance snapshot.
```
GET /instance/snapshot/<id>
Response status: 200, 404
Response data:
{
    "snapshot": {
        ......
    }
}
```

Create an instance snapshot.
```
POST /instance/snapshot
Request data:
{
    "snapshot": {
        <arguments>
    }
}
Response status: 201
Response data:
{
    "snapshot": {
        "id": <id>
    }
}
```

Delete an instance snapshot.
```
DELETE /instance/snapshot/<id>
Response status: 201
Response data:
{
    "snapshot": {
        "id": <id>
    }
}
```


## 2.2 Instance backup

Get the list of instance backup.
```
GET /instance/backup
Response status: 200
Response data:
{
    "backups": [
        {...},
        {...},
        {...}
    ]
}
```

Get a specific instance backup.
```
GET /instance/backup/<id>
Response status: 200, 404
Response data:
{
    "backup": {
        ......
    }
}
```

Create an instance backup.
```
POST /instance/backup
Request data:
{
    "backup": {
        <arguments>
    }
}
Response status: 201
Response data:
{
    "backup": {
        "id": <id>
    }
}
```

Action on an instance backup.
```
POST /instance/backup/<id>/action
Request data:
{
    "update": {
        <arguments>
    }
}
Response status: 201
```

Delete an instance backup.
```
DELETE /instance/backup/<id>
Response status: 201
Response data:
{
    "backup": {
        "id": <id>
    }
}
```


## 2.3 Instance

Don't support creating instance from instance backup. User will need to create volume from volume backup, then create instance on volume.

To rollback an instance, user will need to stop the instance, rollback volume, then restart the instance.


## 2.4 API Gateway

Version is included in the URL/endpoint of API gateway and backend service.
```
GET <API gateway>/compute/snapshot
-> GET <backup>/instance/snapshot

GET <API gateway>/compute/snapshot/<id>
-> GET <backup>/instance/snapshot/<id>

POST <API gateway>/compute/snapshot
-> POST <backup>/instance/snapshot

DELETE <API gateway>/compute/snapshot/<id>
-> DELETE <backup>/instance/snapshot/<id>
```

```
GET <API gateway>/compute/backup
-> GET <backup>/instance/backup

GET <API gateway>/compute/backup/<id>
-> GET <backup>/instance/backup/<id>

POST <API gateway>/compute/backup
-> POST <backup>/instance/backup

POST <API gateway>/compute/backup/<id>/action
-> POST <backup>/instance/backup/<id>/action

DELETE <API gateway>/compute/backup/<id>
-> DELETE <backup>/instance/backup/<id>
```


