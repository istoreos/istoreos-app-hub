# Documentation map

This directory separates current contracts from historical implementation
records:

- `architecture/`: current cross-package architecture and extension contracts;
- `operations/`: repeatable test and troubleshooting runbooks;
- `releases/`: frozen release baselines and version ledgers;
- `archive/`: superseded plans and design records, retained for history only;
- `apps-catalog.*` and `app-diagnostics.jsonl`: generated repository inventory;
- `app-template.md`, `syncapps.md`, and `ai-prompt.md`: repository workflows.

For LinkEase application entry work, start with:

1. [LinkEase Apps integration](architecture/linkease-apps-integration.md)
2. [Application routing test runbook](operations/linkease-app-routing-test.md)

Do not use a document under `archive/` as the current package contract.

应用注册与包归属统一遵循 [应用注册规范](architecture/linkease-app-registration.md)。`app-meta-*` 不安装应用清单或注册链接；实际运行包或已有 LuCI 包负责登记。
