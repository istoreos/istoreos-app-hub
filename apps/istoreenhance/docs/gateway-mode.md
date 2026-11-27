# KSpeeder gateway DNS mode

The iStoreEnhance package ships one typed domain manifest at
`/usr/share/kspeeder/gateway-domains.conf`. KSpeeder generates it from the
same catalog used by the admin API, and the init script consumes it.

## KSpeeder runs on the gateway

Enable **Gateway mode** in LuCI. When KSpeeder is enabled, the init script:

1. reads the active LAN IPv4 address;
2. writes the manifest's `gateway` entries to
   `/tmp/kspeeder-gateway.hosts`;
3. registers that file in `dhcp.@dnsmasq[0].addnhosts`; and
4. reloads dnsmasq.

Disabling Gateway mode, disabling KSpeeder, or stopping the service removes
both the generated file and its UCI registration.

## KSpeeder runs on another LAN node

Keep Gateway mode disabled. The KSpeeder management page lists every `gateway`
domain that the gateway DNS administrator must resolve to the KSpeeder node's
LAN IP. Use the LuCI link to open `/#/gateway-dns` on the KSpeeder management
port, or run `ks-cli gateway domains --admin-url http://<node-ip>:5003`.

The management page also generates ready-to-copy hosts and dnsmasq/OpenWrt
configuration. On a router it pre-fills the IPv4 address detected from
`br-lan`; for a remote KSpeeder node, replace it with that node's LAN IPv4 and
the generated content updates immediately.

The manifest also lists two `loopback` domains:

- `registry-relay.linkease.net`
- `ghcr-relay.linkease.net`

These names belong to ks-cli's per-client Docker relay. They must continue to
resolve to `127.0.0.1` on each client and must never be mapped to the gateway
or to a remote KSpeeder node.
