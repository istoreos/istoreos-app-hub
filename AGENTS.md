# Agent Instructions (istoreos-app-hub)

## App Inventory

- When a task depends on “what apps exist in this repo”, read `docs/apps-catalog.min.md` first.
- If the inventory seems outdated (missing a directory under `apps/`), ask to regenerate it with `make apps-catalog`.
- When referring to an app, use its `id` (matches `app-meta-<id>` and usually `apps/<id>/`).

## Application Registration

- Read `docs/architecture/linkease-app-registration.md` before adding or moving an application entry.
- The only production registry is `/usr/share/linkease/apps.d` for builtin, iframe, and module apps.
- Runtime packages own their manifests and registration symlinks. LuCI-only entries belong to the existing `luci-app-*` package.
- `app-meta-*` packages own software-center metadata, metadata icons and dependencies, never application registrations or their application static assets.
- Do not create companion registration packages or write to the retired desktop registry. Old paths may appear only in precise upgrade/uninstall cleanup and test fixtures.
- Registration migration keeps existing unversioned META_DEPENDS. Publish the owning plugins first; users update those plugins separately. A metadata-only upgrade does not guarantee migration of installed plugins.
- Do not add meta-package minimum-version constraints or expand the scope to shared openwrt-app-meta/meta.mk or metadata CI for this migration.

## App Update Notifications

- When changing shipped app code (including entry scripts, LuCI, runtime recipes, or configuration), increment `PKG_RELEASE` in the corresponding `app-meta-*/Makefile` by one so the software center can offer the update. Updating only a runtime or LuCI package is insufficient.
- Verify the app's actual meta-package mapping, including cases such as `ubuntu2` being delivered through `app-meta-ubuntu`.
- A release increment already included in the same pending update covers that candidate; do not increment it twice. Documentation-only or test-only changes do not require a package release increment.
