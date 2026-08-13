# Codex Sol + Luna Worker

[English](README.md)

[![Validation](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml/badge.svg?branch=master)](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml)
[![Stable: v4.0.0](https://img.shields.io/badge/stable-v4.0.0-blue)](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases/tag/v4.0.0)
[![Preview: v4.1.0-rc4](https://img.shields.io/badge/preview-v4.1.0--rc4-orange)](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases/tag/v4.1.0-rc4)
[![License](https://img.shields.io/github/license/SuperDaddyV/codex-sol-luna-worker)](LICENSE)

让 GPT-5.6 Sol 专注于理解、规划、编排、歧义处理与最终验收，让原生 GPT-5.6 Luna worker 承担边界清楚的执行任务。

> [!IMPORTANT]
> 这是独立的社区项目，与 OpenAI、ModelDial 均无隶属、赞助或背书关系。

> [!NOTE]
> `v4.1.0-rc4` 是当前已发布的 Preview prerelease／公开测试版本。RC4 通过 current-task evidence gating 修复 RC3 的 `Luna unavailable` Receipt 误分类。留档的真实 RC3→RC4 Global upgrade 和 Runtime Cases A/B/C/D 均已通过。`v4.0.0` 仍是稳定版本。
>
> RC3 可能在没有 selector、没有 delegation、没有 availability evidence 时错误输出 `Luna unavailable`。RC4 禁止在无证据时使用该原因，只有真实且 parent-visible 的 availability failure evidence 存在时才允许。详细记录见 [RUNTIME_TESTS.md](RUNTIME_TESTS.md)。

```text
GPT-5.6 Sol
      ↓
AGENTS delegation policy
      ↓
Daily Selector
      ↓
Native Luna / daily selected effort
      ↓
Native leaf execution
      ↓
Sol Acceptance Gate
      ↓
Delegation Receipt
```

v4 不需要 Hook Router。Daily Selector 按北京时间每天选择一次 Luna effort，当天重复使用同一结果。准备开始时，直接看[使用 Codex 安装](#使用-codex-安装)。

## 使用 Codex 安装

1. 使用 GPT-5.6 Sol 新建一个 Codex 任务。
2. 先审阅[安装合同](CODEX_SOL_LUNA_SETUP.md)。
3. 复制下面的提示词。
4. 由 Codex 完成环境识别、dry-run、安装器事务备份、安装和验证。
5. 按需完全重新加载 Codex，再新建任务完成 smoke test。已经打开的旧任务不能作为新全局配置的完整验收依据。

```text
请读取并严格执行以下安装规范：

https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/e1967f8fc957904e3f90b0dd6140430f792d9956/CODEX_SOL_LUNA_SETUP.md

根据当前操作系统和 Codex 环境完成环境识别、dry-run、备份、安装与验证。
必须使用项目现有安装器，不要覆盖无关的用户配置。
如果无法安全安装，请停止并报告准确阻塞，不要猜测修复或扩大权限。
安装完成后，请告诉我是否需要重新加载 Codex，并在新任务中验证结果。
```

> [!WARNING]
> 上面的 setup contract 已固定到 immutable RC4 post-release documentation Commit C。RC4 是当前已发布的 Preview prerelease／公开测试版本；不得改用可变 `master`。执行前先审阅合同。安装器只合并已知托管块，ownership 冲突时 fail closed，并在变更前创建事务备份；但任何安装都不能承诺绝对无风险。

## 🚀 这是什么

本项目把 Codex 中两类工作明确分开：

- **GPT-5.6 Sol**：理解需求、思考、规划、架构、编排、处理歧义，并对最终结果负责。
- **GPT-5.6 Luna**：编码执行、定向搜索、文件检查、测试、lint/build、重复性工作，以及范围明确的批量任务。

Sol 始终是唯一主脑。它判断一个任务是否已经足够清楚、是否值得委派；Luna 只执行被明确限定的工作并返回证据，最后仍由 Sol 验收。

## 为什么要这样做

设计目标是把高价值的思考、取舍和验收留给 Sol，把机械且边界清楚的执行交给 Luna。并不是为了让 Sol 退出工作，也不是把所有任务强制交给 Luna。本项目不承诺未经测量的固定成本比例、速度提升或质量数字。

## ✨ 核心功能

- **Sol 唯一主脑**：规划、架构、编排、歧义处理和最终验收不下放。
- **自动判断是否委派**：正常使用时无需手工指定 Luna role；Sol 依据有效的 `AGENTS.md` 与 installed Global selector 返回的北京时间当天 role 决策。
- **Daily Luna effort selection**：在 `low`、`medium`、`high`、`xhigh`、`max` 五档中选择；`ultra` 永久排除在 v4 allowlist 外。
- **北京时间每日一次**：当天复用同一个选择，跨日重新选择。
- **LKG fallback 与 first-use fail closed**：实时来源无效时可使用有效的 last-known-good；首次使用既无有效来源也无 LKG 时返回 `NO_LUNA_PROFILE_AVAILABLE`，Sol 自己完成任务，不猜 effort。
- **Capability degradation**：显式提供本地 supported-effort 集合时，source winner 不可用可降级到最优的受支持档位并记录状态。
- **五个稳定角色**：`luna_low`、`luna_medium`、`luna_high`、`luna_xhigh`、`luna_max`。
- **Native leaf**：五个 Luna 都设置 `[agents] enabled = false`，不能继续创建子 Agent。
- **最多 3 个直属并行 child**：只对彼此独立的任务并行。
- **Sol Acceptance Gate**：Luna 的返回不是最终结论，Sol 必须复核。
- **Context Firewall**：只向 Luna 传递完成限定任务所需的最小上下文。
- **Task Contract**：每次委派明确 Goal、Scope、Constraints、Acceptance Criteria 和 Verification。
- **Delegation Receipt**：对非平凡任务，用最终一行汇总已经发生的 delegated 或 Sol-only 结果；`Luna unavailable` 必须有当前任务 parent-visible availability failure evidence，且绝不是 Sol-only 默认 fallback。Receipt 不降低委派门槛，也不得通过 selector、probe、tool、child、network、state、telemetry 或 repository write 主动创造证据。
- **Global 与 project-scoped usage**：支持全局默认，也尊重项目自己的 Codex 配置层。
- **事务安装器**：显式目标、ownership、原子写入、backup、exact rollback 和安全 uninstall。
- **Legacy `3.2` migration**：只接受精确 schema，未知历史状态 fail closed。
- **三平台仓库 CI**：Windows、Ubuntu、macOS 使用 Python 3.11 验证。

## 🧠 工作原理

```text
用户给 Sol 一个正常任务
          ↓
Sol 理解需求并处理歧义
          ↓
读取 AGENTS policy + 调用 installed Global selector
          ↓
任务是否清楚、独立且值得委派？
       ↙             ↘
     否                 是
Sol 直接完成      选定的 native Luna 执行
       ↘             ↙
         Sol 复核并给出最终结果
```

v3 prototype 曾探索 Hook enforcement。v4 stable 改用已完成真实 runtime validation 的 native custom-agent 路径，结构更小，也不需要 Hook Router。这不是对其它实现的评价，只是本项目当前的冻结边界。

## ✅ 安装后会得到什么

| 能力 | 全局位置 | 作用 |
| --- | --- | --- |
| 五个 Luna roles | `<CODEX_HOME>/agents/luna-{low,medium,high,xhigh,max}.toml` | 五档原生 GPT-5.6 Luna worker |
| Global AGENTS | `<CODEX_HOME>/AGENTS.md` 中的托管块 | Sol/Luna 分工、Task Contract、Context Firewall、验收与 Delegation Receipt 规则 |
| Multi-agent config | `<CODEX_HOME>/config.toml` 中的托管块 | 启用 multi-agent，直属 child 上限为 3 |
| Daily Selector | `<CODEX_HOME>/sol-luna-v4/selector.py` | 解析北京时间当天 Luna role |
| v4 state | `<CODEX_HOME>/sol-luna-v4/state/` | 首次使用时生成 daily profile、LKG 和 lock |
| Install manifest | `<CODEX_HOME>/sol-luna-v4/install-manifest.json` | 记录安装器 ownership，支持升级、回滚和卸载 |

仓库本地 `.var/` 可供 selector 开发命令使用，但它只是非权威开发状态，不是实际 Codex 项目委派的 authority。实际项目委派遵循继承的 Global installed-selector policy。

五个 role 全部使用 `model = "gpt-5.6-luna"`，effort 依次为 `low`、`medium`、`high`、`xhigh`、`max`，且全部是 `[agents] enabled = false` 的 native leaf。

不会安装 Hook Router、`PreToolUse` enforcement、managed-child registry、daemon、database、scheduler、dashboard、plugin framework 或 custom orchestration engine。

## 💻 系统要求

- 当前 Codex 客户端支持 custom agents 与 multi-agent/subagent。
- 主任务可使用 GPT-5.6 Sol，账号可访问 GPT-5.6 Luna 及所需五档 effort。
- Python 3.11 或更高版本，并能导入标准库 `tomllib`。
- 推荐使用 Git 获取与安装合同相同的不可变 commit。
- Windows、Ubuntu/Linux、macOS。WSL 是独立 Linux 环境，不能把 native Windows 的路径和配置直接混用。

RC4 完整仓库测试已通过 `114/114`，其 source 已通过 Windows、Ubuntu、macOS CI。已发布 RC4 prerelease 还通过了留档的真实 RC3→RC4 Global upgrade 和 Runtime Cases A/B/C/D。已发布 RC1、RC2、RC3 的 runtime 记录继续作为历史证据，其中包括 RC2 的 `FRESH_REPO_CONTEXT_DELEGATION_PASS`。**三平台 CI PASS 不等于三个操作系统、所有客户端、所有账号或所有用户都做过真实 runtime 验收。**

Codex 能力事实以 OpenAI 官方文档为准：[AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference) 和 [Models](https://developers.openai.com/api/docs/models)。

## 🎯 日常使用

正常情况下，无需每天写“使用 Luna”，也无需手工填写 `luna_max`。像平时一样把完整目标交给 Sol；Sol 根据有效的 AGENTS policy、当天 Daily Profile 和 bounded-task policy 判断是否委派。以下示例不保证一定创建 child，因为有些任务由 Sol 直接完成更合适。

### 编码

```text
请审查这个项目，修复测试失败，并验证结果。
```

### 检查

```text
请检查这些模块是否存在不一致的配置，并汇总发现。
```

### 独立并行工作

```text
请分别审查前端、后端和测试，最后给我一份统一结论。
```

第三个例子允许 Sol 考虑并行，但只有彼此独立的部分才应并行。安装或更新后第一次使用，应重新加载 Codex 并新建任务，让全局 AGENTS、agents 与 config 重新进入当前运行上下文。

## 怎么判断 Sol + Luna 是否已经生效？

非平凡任务的最后一行会报告一个已经观察到的结果。发生委派时使用 `Sol/Luna: delegated · <role> ×<direct_child_count>`；只有至少两个直属 Luna child 确实重叠执行时才追加 ` · parallel`。Sol-only 任务只给一个高层原因：`task too small`、`reasoning/architecture task`、`no independent bounded work` 或 `Luna unavailable`。最后一类只有在当前任务的正常执行路径已经自然产生 parent-visible selector 或 native-agent availability failure evidence 时才成立；没有委派本身不等于 Luna unavailable。

`0 Luna` 不等于安装失败。简单任务、推理或架构任务、存在歧义的任务以及紧耦合任务本就可能由 Sol 保留。Receipt 只是低噪声执行摘要，不是 runtime attestation；正式验收仍要核对真实 child metadata。

### Basic 只读自测

安装或升级后在新任务中运行。它自然包含边界明确的检查工作，但不要求一定创建 child：

```text
请只读检查 README.md 和 README.zh-CN.md，不要修改文件。比较两者的安装状态与验证边界描述，并报告不一致。正常遵循当前 delegation policy；不要指定 role、model 或 effort。Sol 必须独立复核结果，并在最后附上正常的 Delegation Receipt。
```

## 🔄 Daily Luna 选择

selector 要求完整且无重复的五档发布数据，选择最高 score；同分时偏向较低 effort。显式限制 supported-effort 集合时，如果来源赢家在本地不可用，会选择最优受支持档并记录 `capability_degraded=true`。结果按北京时间自然日加锁，当天复用。

v4.1 的来源顺序为官方 [ModelDial API v1](https://modeldial.com/api/v1/radar/latest.json)、官方 [Full Snapshot JSON](https://modeldial.com/data/reference-snapshots/latest.json)、有效 LKG。API 有效时立即停止获取；v4.1 已移除 Radar HTML runtime fallback。首次使用既无有效来源也无 LKG 时 fail closed，Sol 保留任务，不猜测 effort。installer 本身不访问 ModelDial，也不转换旧版 Daily Profile 或 LKG。某一天的具体 score 不是永久产品事实。

## ⚡ 并行

Sol 最多同时运行 3 个直属 Luna child。并行只用于互不依赖的搜索、检查、测试或分区执行；共享写入、存在顺序依赖或需要统一架构判断的任务不应强行并行。Luna 自己不能继续 spawn。

## 🛡️ 安全与配置保护

- 所有写入模式都要求明确的 `--codex-home`。
- `config.toml` 和 `AGENTS.md` 只合并项目拥有的 marker block，块外用户内容保留。
- 非空 `AGENTS.override.md`、未被 manifest 拥有的同名 agent、被修改的 owned file、无效 TOML 或不支持的 manifest 都会 fail closed。
- 每次有效安装或升级先创建并校验集中 backup，再最后原子写 v4 manifest。
- migration 只接受精确 legacy schema `3.2`，只删除 manifest-owned 内容，并保留无 ownership 的历史审计证据。
- 发布或更新 GitHub 仓库不会自动写入用户的 Codex home。
- Native leaf 是本地工作流边界，不是服务端或密码学安全边界。

完整边界见 [SECURITY.md](SECURITY.md)。

## ↩️ 回滚与卸载

安装或升级成功后，保存 installer 返回的精确 backup path。需要回滚时使用真实 CLI：

```powershell
python scripts/install.py --rollback "<BACKUP_PATH>" --codex-home "<CODEX_HOME>"
```

rollback 校验 installer-owned snapshot，精确恢复安装前状态；成功后该 backup 会被消费。卸载使用 manifest ownership，遇到已修改的 owned content 会停止：

```powershell
python scripts/install.py --uninstall --codex-home "<CODEX_HOME>"
```

uninstall 只移除 v4-owned 文件和 block，保留无关用户内容。完成 rollback 或 uninstall 后重新加载 Codex，并新建任务。执行前请先阅读[安装合同](CODEX_SOL_LUNA_SETUP.md)。

## 🧪 已验证范围

### Repository CI

| Validation | Status |
| --- | --- |
| Native custom Luna | `PASS` |
| Automatic AGENTS delegation | `PASS` |
| Native leaf | `PASS` |
| Native parallel | `PASS` |
| Sol Acceptance | `PASS` |
| Clean installer | `PASS` |
| Legacy migration simulation | `PASS` |
| RC4 source suite | `PASS` |
| RC4 real Global upgrade | `PASS` |
| RC4 Case A | `PASS` |
| RC4 Case B | `PASS` |
| RC4 Case C | `PASS` |
| RC4 controlled Case D | `PASS` |
| RC3 real Global upgrade | `PASS` |
| RC3 Sol-only Receipt | `PASS` |
| RC3 delegated Receipt | `PASS` |
| Windows CI | `PASS` |
| Ubuntu CI | `PASS` |
| macOS CI | `PASS` |

### Real Runtime

已发布 RC4 prerelease 的留档真实 RC3→RC4 Global upgrade 以两项有效变更完成，并通过 second-apply 幂等和 rollback readiness 检查。Case A 验证 Sol reasoning Receipt；Case B 验证 3 个直属 `luna_max` child、native leaf、并行重叠、0 个孙级 child 和 Sol acceptance；Case C 直接回归 no-selector、no-delegation、no-evidence 误分类；受控 Case D 只在真实 availability evidence 存在时允许 `Luna unavailable`，无证据时禁止。RC3 继续作为历史 prerelease 证据。以上结果只适用于实际观察所用的留档环境，不扩大为所有操作系统、账号、客户端或用户均已通过真实 runtime 验收。详细边界见 [RUNTIME_TESTS.md](RUNTIME_TESTS.md) 和 [ARCHITECTURE.md](ARCHITECTURE.md)。

## ❓ FAQ

### 为什么不用全部任务都让 Sol 做？

Sol 可以自己完成任务，也会保留简单、模糊或不值得委派的工作。对边界清楚的执行进行委派，是为了让 Sol 把注意力放在需求、取舍、编排和验收上。

### 为什么不是所有任务都交给 Luna？

Luna 被明确限制为执行 worker。架构决策、未解决歧义、范围扩张和最终验收必须由 Sol 负责。

### 我需要手工选择 Luna effort 吗？

通常不需要。Daily Selector 为北京时间当天返回一个稳定 role，Sol 只在值得委派时使用它。

### ModelDial 访问失败怎么办？

当天已有 profile 会继续复用；跨日选择依次尝试官方 API、官方完整快照和有效 LKG。首次使用没有有效来源和 LKG 时 fail closed，Sol 自己执行，不猜 effort。

### 为什么不用 Ultra？

冻结的 v4 policy 只定义并验证了 `low` 到 `max` 五档。`ultra` 不属于这个稳定选择与验证合同。

### Luna 可以继续创建子 Agent 吗？

不可以。五个正式 Luna role 都设置 `[agents] enabled = false`，是 native leaf。

### 安装后旧 Codex 会话能生效吗？

不应依赖。Codex 在一次 run 或任务开始时构建 instruction chain。安装或更新全局 AGENTS、agents、config、selector 后，应按需重新加载 Codex Desktop/App Server，并新开任务做完整验证；不需要因为本项目重启 Windows。

### 项目自己的 `.codex/agents` 会怎样？

全局 agent 提供个人默认，项目级 agents 和项目 `AGENTS.md` 会在项目上下文中共同参与有效配置。不要假设全局文件会覆盖项目拥有的定义或指令；遇到同名或语义冲突应检查当前项目的有效配置并 fail closed。

### 需要 Hook 吗？

v4 core 不需要。历史 Hook 文件可能作为旧证据存在，但不是当前 runtime dependency 或安装前提。

### 可以卸载或回滚吗？

可以，前提是 v4 manifest 与相关 backup 完整。必须使用 installer 的 `--rollback` 和 `--uninstall`，不要手工编辑 TOML 模拟回滚或卸载。

## Advanced / Manual

普通用户优先使用 Codex 安装。人工审阅时，应获取不可变 commit，检查合同与源码，并先执行只读步骤：

```powershell
git clone https://github.com/SuperDaddyV/codex-sol-luna-worker.git
cd codex-sol-luna-worker
git checkout --detach <APPROVED_40_HEX_COMMIT>
python scripts/install.py --help
python scripts/install.py --dry-run --codex-home "<CODEX_HOME>"
python -m unittest discover -s tests -v
```

真实 global installation 不使用 `--validation-sandbox`；这个参数只允许仓库 `.tmp/installer-validation/` 下的测试目标。apply、migration、rollback 和 uninstall 见 [CODEX_SOL_LUNA_SETUP.md](CODEX_SOL_LUNA_SETUP.md)。

### 可选并行自测

在新任务中提出两到三个彼此独立、边界明确的只读检查，并要求 Sol 给出一份经过复核的统一结论。不要强制 spawn，也不要指定 role。只有 parent-visible runtime evidence 证明至少两个直属 Luna child 确实重叠执行时，才接受 ` · parallel`；Receipt 文本本身不是证明。

## 📚 技术文档

- [Codex 可执行安装合同](CODEX_SOL_LUNA_SETUP.md)
- [架构说明](ARCHITECTURE.md)
- [Runtime 验证](RUNTIME_TESTS.md)
- [安全边界](SECURITY.md)
- [变更记录](CHANGELOG.md)
- [MIT License](LICENSE)

## License

[MIT](LICENSE)

`fixtures/modeldial/` 下由 ModelDial 数据派生的测试 fixture 依 CC BY 4.0 在[独立说明](fixtures/modeldial/README.md)中署名；项目源码许可证仍为 MIT。
