# DSH for iStoreOS

This application runs DeepSeek Harness in a hardened Docker container and
publishes its native root-path Web workbench on a dedicated port. The
`/apps/dsh/` route is only a request-host-aware launcher; it never proxies or
rewrites DSH HTML, assets, manifests, APIs or WebSockets.

## Runtime profiles

The configuration stores a stable profile ID instead of an arbitrary image
name. The runtime owns the mapping from profile to reviewed image, ports and
security settings.

| Profile | Status | Image | Capabilities |
| --- | --- | --- | --- |
| `standard` | supported | `ghcr.io/omdsh-dev/dsh-container:0.2.1-rc.2` pinned by manifest digest | DSH Web, tools, sessions and plugins |
| `advanced` | reserved | `runzhliu/deepseek-harness:0.2.3-alpha.2-r1` | Future Chromium/noVNC profile; not selectable yet |

Adding `advanced` needs its own browser/noVNC ports, shared-memory allocation,
resource checks, health probes and security review; it is not merely a second
image string.

## Access and authentication

- Docker publishes `<configured port>:3080` on all host interfaces, matching
  the usual iStoreOS Docker-plugin convention. Firewall and interface access
  remain user policy.
- DSH's `DSH_CONTAINER_KEY` authentication is mandatory. The runtime generates
  an initial key at `/etc/dsh/admin.key`, owned by root with mode `0600`.
- LuCI can replace the key without reading it back. Restart recreates the
  container so port and key changes take effect transactionally.
- `/apps/dsh/` returns a temporary redirect to
  `http://<current-request-host>:<configured-port>/`. DSH then displays its own
  administrator-key login.
- The key is not stored in UCI, shown in status output or copied into test logs.
- `extra_trusted_hosts=*` is the default iStoreOS automatic mode. It expands to
  the device's current IPv4 addresses and router hostname; the raw wildcard is
  not passed to DSH because the upstream relay accepts only exact authorities.
  Replace `*` with exact comma-separated names when using custom DNS.

Because DSH stays at origin root, upstream paths such as `/auth-bootstrap.js`,
`/manifest.webmanifest`, `/api/...` and WebSockets work unchanged. There is no
patched `index.html` or compatibility bind mount.

## Container boundaries

- The container is non-root, read-only, drops all capabilities, enables
  `no-new-privileges` and does not receive the Docker socket.
- DSH runs in `danger-full-access` mode inside the container. Host access is
  limited to the two selected bind mounts.
- The container relay performs DSH's browser-session exchange internally after
  administrator-key authentication.

## Persistent data

Two separate host directories are required:

- `data_path` -> `/home/node/.dsh`: credentials, settings, sessions and plugins;
- `workspace_path` -> `/home/node`: files the Agent may read and modify.

New directories are created as UID/GID 1000. Existing directories are accepted
only when already owned by UID 1000; the installer never recursively changes
ownership of an existing repository. Removing the container or package leaves
both directories intact.

## Replacement and rollback

Install, repair, restart and upgrade use the same transaction:

1. validate the profile, port, administrator key and storage paths;
2. pull the pinned image reference;
3. stop and rename the current container;
4. create the authenticated replacement with persistent mounts;
5. wait for the image health check;
6. remove the old container only after the replacement is healthy.

If creation or health checking fails, the replacement is removed and the
previous container is restored and started.
