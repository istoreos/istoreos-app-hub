# Agent Instructions (istoreos-app-hub)

## App Inventory

- When a task depends on “what apps exist in this repo”, read `docs/apps-catalog.min.md` first.
- If the inventory seems outdated (missing a directory under `apps/`), ask to regenerate it with `make apps-catalog`.
- When referring to an app, use its `id` (matches `app-meta-<id>` and usually `apps/<id>/`).

## LinkEase Desktop Icons

- When adding a LinkEase Desktop icon through an `app-meta-*` package, read `docs/architecture/linkease-desktop-app-meta-icons.md` first.
- Prefer the `app-meta-<id>/root/usr/share/linkeasefull/desktop-apps.d/*.json` pattern for simple LuCI-only apps such as DDNSTO.
- Do not add a separate `luci-app-linkeasefull-<id>` companion package when the same desktop manifest is already owned by `app-meta-<id>`.

## App Update Notifications

- When changing shipped app code (including entry scripts, LuCI, runtime recipes, or configuration), increment `PKG_RELEASE` in the corresponding `app-meta-*/Makefile` by one so the software center can offer the update. Updating only a runtime or LuCI package is insufficient.
- Verify the app's actual meta-package mapping, including cases such as `ubuntu2` being delivered through `app-meta-ubuntu`.
- A release increment already included in the same pending update covers that candidate; do not increment it twice. Documentation-only or test-only changes do not require a package release increment.
