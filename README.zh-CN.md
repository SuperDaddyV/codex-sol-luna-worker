# Codex Sol Brain + Luna Daily Best v4.0.0-rc1 Native

状态：`v4.0.0-rc1 — NATIVE RUNTIME PASS`

本候选版本使用 Codex 原生 custom-agent runtime。用户在主会话选择 `gpt-5.6-sol`；Sol 负责规划、架构、编排、歧义处理与最终验收；明确且有边界的执行任务只能通过当天 Daily Profile 选中的原生 Luna agent 委派。

Native Runtime Test 1-5 均为通用 `PASS`。证据记录刻意不包含会话 ID、用户名、绝对路径、rollout ID 或安装 ID。

## Architecture

```text
GPT-5.6 Sol
  -> project AGENTS.md delegation policy
  -> Daily Profile selected role
  -> Native custom Luna agent（native agent_type）
  -> GPT-5.6 Luna / selected effort
  -> Native leaf（[agents] enabled = false）
  -> Sol Acceptance Gate
```

稳定映射为 `low -> luna_low`、`medium -> luna_medium`、`high -> luna_high`、`xhigh -> luna_xhigh`、`max -> luna_max`。Luna 永不使用 `ultra`。只有 native custom agent 配置负责 model/effort 选择，不存在 direct model override。

Sol 始终是唯一的规划者、编排者、歧义处理者和最终复核者。五个正式 Luna custom agent 都是 `[agents] enabled = false` 的原生 leaf，因此 child 不能继续 spawn 或 delegation。

## Explicit non-goals

当前 runtime 不包含 Hook Router、Hook Trust、managed-child registry、daemon、后台 scheduler、database、dashboard、IPC server、plugin framework 或 custom orchestration。唯一的 delegation 机制是 native `agent_type`/custom-agent 选择与项目 `AGENTS.md` policy。

## Runtime status

| Native Runtime Test | 结果 | 通用证据范围 |
| --- | --- | --- |
| 1．项目 custom-agent discovery | `PASS` | fresh project session 能发现五个项目 custom agent。 |
| 2．显式 native spawn | `PASS` | 指定 custom agent 以 GPT-5.6 Luna 及其配置 effort 运行，并返回要求的 sentinel。 |
| 3．`AGENTS.md` policy delegation | `PASS` | Sol 读取当日 Daily Profile，委派给 selected role，并完成验收。 |
| 4．Native leaf | `PASS` | `[agents] enabled = false` 阻止 child 使用 multi-agent/delegation tools。 |
| 5．Parallel native delegation | `PASS` | 两个独立窄检查使用 selected role，由 Sol 汇总并验收。 |

这些测试验证了本候选版本的 native runtime architecture，但不会授予 Luna 规划、架构、编排或最终验收权限。

## Why v4

强制 Hook-enforcement 路线属于历史上的 v3 prototype 路径；在此前观察的 Codex Desktop V2 runtime 中，它无法可靠截获真实 collaboration spawn。因此本候选版本改用原生项目 custom agents 与 `AGENTS.md` delegation policy，当前架构不依赖 Hook。

## 官方能力边界

当前边界已通过 Native Runtime Test 1-5 验证：

- 项目级 custom agents 位于 `.codex/agents/*.toml`，并以 native `agent_type`/custom-agent 名称发现和 spawn。
- Daily Profile 的 `selected_role` 是当天唯一的 Luna role 路由结果。
- custom agent 配置固定 GPT-5.6 Luna 及 `low` 到 `max` 的 selected effort；没有 direct model override。
- 每个正式 custom agent 使用 `[agents] enabled = false`，构成 native leaf。
- Sol 保留全部规划、编排和最终验收权。

官方依据：[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) 、[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference) 、[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 、[GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) 。

## Daily selector

selector 先以 fixtures 验证纯算法，再显式接入在线 source：

- 五档 Luna canonical rows 必须完整且无重复。
- `score` 最高者获胜。
- 同分按 `low < medium < high < xhigh < max` 选择较低 effort。
- source winner 本地不可用时，在本地支持集合中重新择优并写入 `capability_degraded=true`。
- 北京时间自然日内只选择一次；跨日重新选择。
- live snapshot 无效时使用 LKG；首次无 LKG 时 fail closed。
- 项目开发状态可写入被忽略的 `.var/`；正式 global installation 使用显式 `<CODEX_HOME>/sol-luna-v4/state`，其中只有 `daily-profile.json`、`last-good-profile.json` 与 `selector.lock`。
- 稳定 global CLI 为 `python <selector> --state-dir <state> --ensure-daily --print-role`；成功时只输出一个稳定 Luna role，无 profile 时以非零状态返回 `NO_LUNA_PROFILE_AVAILABLE`。
- migration 不转换 v3 Daily Profile/LKG，不联网，也不生成 v4 profile；首次实际使用由 v4 selector 建立自己的 state lifecycle。

2026-08-11 的实测确认 ModelDial 一方 Radar 页面公开声明机器可读 published snapshot。运行时先取严格校验的 JSON；失败后才解析同一一方 Radar HTML 的完整五档 published batch。两条路径只允许 `modeldial.com` 与 `reference.modeldial.com` 的 HTTPS，禁止 credentials、cookies、auth headers 和第三方镜像。在线 source 必须显式使用 `--live`，CI 不联网。

```powershell
python src/selector.py --snapshot fixtures/modeldial/complete.json
python src/selector.py --live
```

第一方来源：[ModelDial Radar](https://modeldial.com/zh-CN/radar) 、[published snapshot JSON](https://modeldial.com/data/reference-snapshots/latest.json) 。

## Local capability probe

默认只生成 dry-run 计划：

```powershell
python scripts/probe_capabilities.py
```

真实 probe 必须显式启用：

```powershell
python scripts/probe_capabilities.py --execute
```

它顺序测试五档 Luna，使用 `--ephemeral` 和 `--ignore-user-config`，分别记录客户端可用性与精确回声行为，只把不含响应正文的结果写入 `.var/capabilities.json`。这项 probe 不修改全局 Codex 配置。

## Installer validation

项目只使用 Python 标准库：

```powershell
python -m unittest discover -s tests -v
python scripts/install.py --dry-run
python scripts/install.py --apply --codex-home .tmp/installer-validation/manual/.codex --validation-sandbox
```

dry-run 仍是默认模式。任何写入模式都必须显式提供 `--codex-home`；repo 内目标还必须使用 `--validation-sandbox`，并位于 `.tmp/installer-validation/` 下。global policy 来自专用 `templates/AGENTS.global.md`，不会安装 repo 根 policy 全文。migration 只精确接受 legacy schema `3.2`，保留不在 ownership 中的 audit bundles，并在所有 pre-commit 验证通过后原子写 v4 manifest 作为 commit marker；旧 manifest 仅在 commit 后清理，失败可幂等重试。clean install、migration、failpoint rollback 与 uninstall 只在隔离 fake home 中验证；本候选版本没有执行或授权真实全局安装。

## Repository layout

```text
.codex/                 project config and five custom Luna agents
fixtures/               offline ModelDial inputs
templates/              dedicated global-safe AGENTS payload
scripts/                sandbox-validated installer and local capability probe
src/selector.py         Daily Profile selection and first-party source adapter
tests/                  standard-library static validation
.var/                   ignored local runtime state
```

## Release boundary

`v4.0.0-rc1` 是 release candidate，不是 stable `v4.0.0`。稳定版之前仍须单独审批全局迁移计划并完成 clean global validation；sandbox installer validation 不授权写入用户真实 Codex home。

完整的 runtime 与架构记录见 [RUNTIME_TESTS.md](RUNTIME_TESTS.md) 和 [ARCHITECTURE.md](ARCHITECTURE.md)。
