# cms-cli

```
cms volume list
cms volume show <ID/name>
cms volume create \
    --size <size in G> \
    <name>
cms volume delete <ID/name>

cms volume create \
    --backup <ID/name> \
    <name>
cms volume rollback \
    --snapshot <ID/name> \
    <ID/name>

cms volume-snapshot list
cms volume-snapshot show <ID/name>
cms volume-snapshot create \
    --volume <ID/name> \
    <name>
cms volume-snapshot delete <ID/name>

cms volume-backup list
cms volume-backup show <ID/name>
cms volume-backup create \
    --volume <ID/name> \
    --incremental \
    --copy-zone <zone> \
    --copy-project <project> \
    <name>
cms volume-backup update <ID/name>
cms volume-backup delete <ID/name>
```

```
cms instance list
cms instance show <ID/name>
cms instance create ...
cms instance delete <ID/name>

cms instance-snapshot list
cms instance-snapshot show <ID/name>
cms instance-snapshot create \
    --volume <ID/name> \
    <name>
cms instance-snapshot delete <ID/name>

cms instance-backup list
cms instance-backup show <ID/name>
cms instance-backup create \
    --volume <ID/name> \
    --incremental \
    --copy-zone <zone> \
    --copy-project <project> \
    <name>
cms instance-backup update <ID/name>
cms instance-backup delete <ID/name>
```

```
cms snapshot-plan list
cms snapshot-plan show <ID/name>
cms snapshot-plan create \
    --resource-type <type> \
    --schedule <cron expr> \
    --retention <number> \
    --credential-name <name> \
    --credential-secret <secret> \
    <name>
cms snapshot-plan execute <ID/name>
cms snapshot-plan delete <ID/name>
```

```
cms backup-plan list
cms backup-plan show <ID/name>
cms backup-plan create \
    --resource-type <type> \
    --schedule <cron expr> \
    --retention <number> \
    --credential-name <name> \
    --credential-secret <secret> \
    --incremental \
    --copy-project \
    --copy-zone \
    <name>
cms backup-plan execute <ID/name>
cms backup-plan delete <ID/name>
```

