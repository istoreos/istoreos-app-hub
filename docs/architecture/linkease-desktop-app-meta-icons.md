# Application registration ownership — superseded document

The former recommendation to ship desktop manifests from `app-meta-*` is retired.
The sole current standard is [LinkEase application registration](linkease-app-registration.md).

Use `/usr/share/linkease/apps.d`; the runtime or existing LuCI package owns the
manifest and its application assets. The software-center package retains only
metadata, metadata icons, and dependencies. DDNSTO is the LuCI-owned example;
FastNet is the runtime-owned example. Do not copy the former app-meta layout.
