# Agent Instructions (istoreos-app-hub)

## App Inventory

- When a task depends on “what apps exist in this repo”, read `docs/apps-catalog.min.md` first.
- If the inventory seems outdated (missing a directory under `apps/`), ask to regenerate it with `make apps-catalog`.
- When referring to an app, use its `id` (matches `app-meta-<id>` and usually `apps/<id>/`).

## LinkEase Desktop Icons

- When adding a LinkEase Desktop icon through an `app-meta-*` package, read `docs/linkease-desktop-app-meta-icons.md` first.
- Prefer the `app-meta-<id>/root/usr/share/linkeasefull/desktop-apps.d/*.json` pattern for simple LuCI-only apps such as DDNSTO.
- Do not add a separate `luci-app-linkeasefull-<id>` companion package when the same desktop manifest is already owned by `app-meta-<id>`.
