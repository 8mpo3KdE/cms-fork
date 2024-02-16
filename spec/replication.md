# Replication

# 1 Volume

## 1.1 Action

volume action:
* replicate
* promote
* demote
* resync


### 1.1.1 Replication

* Instant Replication 

It has impact to write performance by double-write to primary OSD and journal. It could be an option for DB type of service, only if performance impact is not an issue.

* One-time Replication

It creates a snapshot and replicate the snapshot.

* Periodic Replication

It creates snapshot and replicate the snapshot, following a given schedule (start and interval).

One-time replication and periodic replication have no performance impact, but there is chance of inconsistence.


### 1.1.2 Promote

### 1.1.3 Demote

### 1.1.4 Resynchronize


## 1.2 Status

Manipulate volume status.
* Once mirror is enabled on a volume, status is "active - primary".
* When the secondary image is being updated, status is "active - updating".
* When the secondary image is not being updated, status is "active - secondary".


## API handling

For now, API GW split volume request to Cinder and CMS. Due to more manipulations need to be injected between client and Cinder, this may need to change to get all volume requests to be handled by CMS.


# 2 Instance

## With record

In case of Terraform or script, records are saved to replay resource deployment. It will be easy to restore in the DR zone.


## Without record

For example, user creates instance on the portal manually, no records to replay the deployment in another zone. It would be easier for user to do the same, mnaully create instance in DR zone.


# 3 Replicate and restore

Volume replication is supported as the base feature. It provides all required blocks to support DR. Instance replication won't be considered untill strong demand from users.

* Create instance on volume(s).
* Enable replication on volume(s), whoes status will be "active - primary".
* Volume with "active - secondary" is created in DR zone.
* TBD: what if primary volume is deleted.
* TBD: how to handle the snapshot on primary volume. Snapshot will be replicated, but how to import snapshots to Cinder?
* Create instance on secondary volume in DR zone. Make it stand-by in shutdown status.

Primary zone goes down.
* Promote secondary volume in DR zone to primary.
* Start the instance in DR zone to restore service.
* After primary zone is restored, need a decision on which zone will be the new primary, and do promote and demote on volume, and resync volume if it's necessary.

Manual failover
* Shutdown primary instance.
* Demote primary volume, promote secondary volume.
* Start secondary instance.


