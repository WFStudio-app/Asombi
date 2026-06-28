# Asombi Instances

Each instance is an isolated Alpine Linux environment with its own filesystem.

## Create / enter
```bash
os login asombi-1
```

## List
```bash
os instances
```

## Delete
```bash
os remove asombi-1
```

## Instance data location (on host)
```
~/.asombi/instances/<name>/rootfs/
```

## Multiple instances
```bash
os login dev      # development environment
os login tools    # tools environment
os login test     # testing environment
```

Each is fully isolated — separate packages, files, and config.

© WFWorld
