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
| `advanced` | experimental | `ghcr.io/runzhliu/deepseek-harness:0.2.3-alpha.2-r1` pinned per architecture | Visible Chromium/noVNC, Playwright Browser Use and human takeover |

`advanced` allocates a 1 GiB `/dev/shm`, a 512 MiB temporary filesystem and a
separate protected gateway. Its compressed image is about 1.08 GiB and expands
to several GiB in Docker storage, so `standard` remains the default.

## Access and authentication

- The selected profile publishes one configured port on all host interfaces,
  matching the usual iStoreOS Docker-plugin convention. Firewall and interface
  access remain user policy.
- A fixed administrator key is mandatory for both profiles. The runtime generates
  an initial key at `/etc/dsh/admin.key`, owned by root with mode `0600`.
- LuCI can replace the key without reading it back. Restart recreates the
  container so port and key changes take effect transactionally.
- Browser enhanced keeps DSH `3080`, noVNC `6080` and Chromium CDP `9222`
  inside a dedicated Docker network. Only its same-origin gateway is published.
  The gateway asks DSH to validate the authority-bound browser session before
  forwarding any `/novnc-*` asset or WebSocket.
- Browser enhanced has no upstream administrator-key option, so its gateway adds
  fixed-key authentication. Sign in as `dsh`; after successful gateway authentication,
  the gateway exchanges the current per-process launch token internally and never
  exposes it in the browser URL, UCI, status output or test logs.
- The dedicated port currently uses plain HTTP, so the key and session are not
  encrypted on the network. Interface exposure remains a user firewall/TLS policy.
- On router boot, the `dsh` init service waits for Docker and refreshes only the
  enhanced gateway so it receives the new DSH process token; the core data and
  workspace containers are not reset by this refresh.
- `/apps/dsh/` returns a temporary redirect to
  `http://<current-request-host>:<configured-port>/`. Both profiles then display
  their administrator-key authentication flow.
- The administrator key is not stored in UCI, shown in status output or copied into test logs.
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
- Standard's container relay and the enhanced gateway perform their respective
  DSH browser-session exchanges only after administrator-key authentication.

## Persistent data

The selected base paths produce three persistent host directories:

- `data_path` -> `/home/node/.dsh` in standard: credentials, settings, sessions and plugins;
- `${data_path}-advanced` -> `/home/node/.dsh` in browser enhanced: isolated
  advanced state so an alpha upgrade cannot make standard rollback unsafe;
- `workspace_path` -> `/home/node` in standard or `/workspace` in browser
  enhanced: files the Agent may read and modify, intentionally shared.

New directories are created as UID/GID 1000. Existing directories are accepted
only when already owned by UID 1000; the installer never recursively changes
ownership of an existing repository. Removing the container or package leaves
both directories intact.

## Replacement and rollback

Install, repair, restart and upgrade use the same transaction:

1. validate the profile, port, administrator key and storage paths;
2. pull the pinned image reference;
3. stop and rename the current core and optional gateway containers;
4. disconnect rollback containers from the private enhanced network;
5. create the authenticated replacement with persistent mounts;
6. verify DSH, Chromium, noVNC, CDP and the public authentication boundary;
7. remove the old deployment only after the replacement is healthy.

If creation or health checking fails, the replacement is removed and the
previous container is restored and started.
