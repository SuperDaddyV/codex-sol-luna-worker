# Sol/Luna 安装协助合同（中文审阅版）

> [!IMPORTANT]
> 本文件只用于中文审阅，不是可执行安装权威，也不会成为第二份安装合同。
> Codex 必须读取并执行英文 `CODEX_SOL_LUNA_INSTALL_ASSIST.md`；公开安装入口
> 还必须固定到该英文文件的
> exact commit，不能执行可变 `master` 上的中文译文。

中文审阅版版本：`4`。

## 1．当前 Stable 的不可变目标

当前 Stable 目标为 `v4.1.4`：

- Stable runtime Source Commit A：
  `6a537b445ad6f17a9600c05e655f51a2844bfcc8`；
- Stable setup contract documentation commit：
  `bf01c438eae66f5ef9a27d401c6ee845f89d5d59`；
- Stable setup contract：
  `https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/bf01c438eae66f5ef9a27d401c6ee845f89d5d59/CODEX_SOL_LUNA_SETUP.md`。

不得替换为 `master`、其他分支、`target_commitish`、归档文件或其他
Release。`v4.1.3` 继续作为上一版不可变 Stable，`v4.1.2`、`v4.1.1` 和
`v4.1.0` 继续作为更早的不可变 Stable，`v4.1.0-rc6` 继续作为
不可变的历史 Prerelease／Preview／Public Beta；不移动、不改写任何 tag 或
Release。

## 2．权限与成功边界

用户复制安装提示词，只授权：

- 一次性只读诊断；
- 英文合同明确列出的会话级安全恢复；
- 在全部前置条件通过后，按照 exact-SHA setup contract 执行安装器。

下列动作必须先展示精确方案，并得到用户对该方案的明确批准：

- 安装软件包；
- 提升管理员权限；
- 持久修改环境或 `PATH`；
- 产生其他操作系统级持久变更。

初始安装请求不等于上述批准。安装助手不能修改认证、凭据、代理、证书
信任、Codex sandbox、approval policy、组织策略、安全软件或无关用户配置。

只有安装和新任务 smoke 都通过，才能报告 `COMPLETE`。否则必须以
`NEEDS_USER_ACTION` 或 `BLOCKED` 结束，并给出一个准确的下一步。

## 3．一次性只读诊断

在 clone、创建临时目录、写入 probe 状态或调用 installer 前，一次性检查：

1. 操作系统、shell、WSL 和当前 Codex 任务环境；
2. 通过正常命令解析运行 `codex --version`；
3. 当前 Python 是否为 3.11+，并含标准库 `tomllib`；
4. `git --version`；
5. Git 可用时，对公开仓库执行只读 `git ls-remote`；
6. 硬依赖缺失时，是否存在受支持且可信的包管理器；
7. installer ownership manifest 是缺失、当前、旧版、新版还是无效。

不得递归搜索文件系统，也不得从 Codex Desktop 内部目录提取可执行文件。
不能在发现第一个问题后停止；独立问题应一起报告，依赖项无法检查时标记为
`NOT_CHECKED`。

环境摘要必须包含：

```text
Sol/Luna Assisted Installation
Target: <version>
OS / WSL: <platform> / YES|NO
Approval policy: <caller-supplied value>
Sandbox mode: <caller-supplied value>
Administrator required: YES / NO / MAY_PROMPT / UNKNOWN
Codex CLI: PASS <version> / MISSING_OR_UNUSABLE
Python: PASS <version> / MISSING_OR_UNSUPPORTED
Git: PASS <version> / MISSING
GitHub HTTPS: PASS / BLOCKED / NOT_CHECKED
Installed Sol/Luna: ABSENT / CURRENT / OLDER / NEWER / INVALID
Recovery: NONE / AWAITING_APPROVAL / NEEDS_USER_ACTION
Ready: YES / NO
```

`approval_policy` 和 `sandbox_mode` 仅作为调用方提供的展示上下文。安装助手
不读取或输出用户的 `config.toml`，也不能给自己授权。

## 4．无需新增批准的安全恢复

只允许以下只读或会话级动作：

- 通过正常 launcher 选择已经安装且受支持的 Python；
- 选择已经通过正常命令解析暴露的 Git 或 Codex CLI；
- 让当前进程重新读取用户或官方安装器已经持久化的环境值，但不新建
  `PATH` 项；
- 修正命令引用、shell 语法和已有可执行文件选择；
- 对可能为瞬时故障的 GitHub HTTPS 检查进行最多三次有界重试。

每个确定性恢复命令最多执行一次，随后只做一次只读证明。失败的软件包、
提权或持久变更命令不能自动重复。

## 5．需要批准的恢复计划

恢复计划必须列出：

```text
Blockers: <标准 reason codes>
Commands: <准确参数向量>
Sources: <官方 HTTPS 来源>
Scope: current-user / system / package-manager-prefix
Administrator elevation: YES / NO / MAY_PROMPT
Persistent changes: <准确影响>
Proof: <一次只读证明>
Rollback: <准确卸载或回滚路径>
Plan ID: sha256:<64hex>
```

用户只能批准已展示的同一个 `Plan ID`。命令、来源、作用范围、影响、证明、
回滚、阻塞原因或平台发生任何变化，都会产生新的 ID；旧批准必须以
`RECOVERY_PLAN_CHANGED` 失败关闭。

恢复命令必须以参数向量执行，不能使用 shell 字符串、管道、重定向、命令
替换或 `curl | sh`。批准只覆盖展示过的命令，不覆盖后续新动作。

## 6．必须由用户处理的情况

以下情况返回 `NEEDS_USER_ACTION`：

- Codex 登录、账户、模型或 multi-agent capability；
- 企业代理、证书、防火墙、终端策略或软件包 allowlist；
- 不受支持的操作系统、Linux 发行版或包管理器；
- 无法确认的官方安装指南；
- 用户拒绝批准、提权被拒绝或包管理器不可用；
- 需要凭据、密钥、billing 或组织管理员决定。

只给一个下一步、一个证明和一个脱敏续接块：

```text
SOL_LUNA_ASSIST_RESUME
Target: <version>
Phase: PREREQUISITE_RECHECK / CAPABILITY_PRECHECK / SELECTOR_INITIALIZATION / FRESH_TASK_SMOKE
Pending blocker: <one reason code>
Next proof: <one read-only proof or user action>
```

前置阶段不创建状态文件，进度保存在对话及上述自包含续接块中。

## 7．P3 排除边界

本次不实现独立签名 bootstrap。Python 脚本不能在没有 Python 时运行；仓库
脚本也不能在 Git 和 immutable source acquisition 完成前运行。因此：

- Python／Git 缺失阶段，由 Codex 按英文合同诊断、展示方案并请求批准；
- Python 3.11+、Git 和 exact source 就绪后，才由确定性
  `scripts/install_assist.py` 接管；
- 不得宣传脚本能独立修复「完全没有 Python／Git」的机器。

## 8．`v4.1.4` 确定性 Stable 安装助手

以下命令只供审阅；实际执行必须以 README 通过 exact commit 固定的英文合同
为准：

```text
<PYTHON> scripts/install_assist.py check --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py plan --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py recover --codex-home <CODEX_HOME> --approve <PLAN_ID>
<PYTHON> scripts/install_assist.py install --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
<PYTHON> scripts/install_assist.py install --apply --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
<PYTHON> scripts/install_assist.py report --codex-home <CODEX_HOME> --format json
```

状态机只允许以下 phase：

```text
CHECKING
SAFE_RECOVERY
AWAITING_APPROVAL
RECHECKING
CAPABILITY_PRECHECK
DRY_RUN
INSTALLING
RELOAD_REQUIRED
SELECTOR_INITIALIZATION
FRESH_TASK_SMOKE
COMPLETE
NEEDS_USER_ACTION
BLOCKED
```

### 8.1 官方恢复目录

唯一命令目录为 `scripts/install_recovery_catalog.json`。首批范围：

- Windows：WinGet；
- macOS：Homebrew；
- Ubuntu／Debian：APT 的 Git 恢复；
- Ubuntu／Debian Python：由于发行版版本差异，只提供官方指引和证明，
  不自动替换系统 Python；
- Codex CLI：只引导用户使用 OpenAI 官方安装与交互式登录路径，不自动
  执行下载管道或修改认证。

每条可执行动作都必须有稳定 action ID、官方来源、准确命令、持久影响、
一次证明和回滚路径。缺少任一项即以 `RECOVERY_CATALOG_INVALID` 停止。

### 8.2 已安装版本 fast path

先检查 manifest 元数据。新版本拒绝自动降级；无效 manifest 直接
`BLOCKED`。当前版本仍必须先通过 capability precheck，再由 installer
dry-run 验证 ownership 和字节一致性。只有 dry-run 返回
`IDEMPOTENT_PASS`，才能进入零写入、零备份 fast path；之后仍要显式取得
Daily selection 证明，再进入新任务 smoke。

### 8.3 Capability 前置门禁

在任何真实 `CODEX_HOME` dry-run 或写入前，必须从 exact checkout 运行五个
Luna effort：`low`、`medium`、`high`、`xhigh`、`max`。调用必须为
ephemeral、忽略用户配置，并使用 `read-only` sandbox；不能复制认证、写入
probe 状态或扩大权限。

任何 effort 不可用、超时、账户限制或证据不完整，都在 installer 前返回
`NEEDS_USER_ACTION`。

### 8.4 Installer 唯一写入权威

`scripts/install_assist.py` 不能自己合并或修补托管文件。只有
`scripts/install.py` 可以执行 ownership 检查、事务备份、apply、rollback、
migration 和 uninstall。

无 `--apply` 的 `install` 只运行 capability 和 installer dry-run，然后停在
`DRY_RUN`。只有用户明确授权 apply 后，才能调用事务安装器。

### 8.5 Selector 初始化门禁

apply 成功后先进入 `RELOAD_REQUIRED`；完成 Codex 重新加载后进入
`SELECTOR_INITIALIZATION`。`IDEMPOTENT_PASS` fast path 不执行 installer 写入或
备份，但同样必须经过此门禁。只运行以下标准命令一次：

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-selection
```

只有退出码为 `0`、`selected_role` 是 `luna_low`、`luna_medium`、
`luna_high`、`luna_xhigh` 或 `luna_max`，且 `selected_effort` 与角色一致，才算
证明完整。该命令是显式的正常 selector state 初始化／复用操作，不是安装助手
擅自修补；续接块必须记录
`Pending blocker: DAILY_SELECTION_PROOF_REQUIRED`。若失败或证据不完整，立即
停止，不自动重试；若通过，再开另一个全新
任务运行唯一一次 compatibility smoke。smoke 保持 status-only，只读检查，不能
自行添加 `--ensure-daily` 或初始化 Daily selection。

## 9．脱敏支持报告

支持报告只允许输出：schema、target、phase、标准 reason code、系统分类、
WSL、调用方提供的权限标签、工具状态和版本、包管理器名称、已安装版本、
严格 40-hex source commit、action ID、plan ID 和 `<CODEX_HOME>` 符号位置。

不得包含真实路径、环境变量、配置内容、认证、命令 stdout／stderr、日志、
异常文本、任意 URL、session／rollout 标识符或 secrets。Markdown 与 JSON
必须从同一份白名单数据生成。

## 10．结果卡

### 重新加载

```text
Reload Required
Version: <version>
Source: <40HEX>
Backup: <symbolic location or NONE>
Next: reload Codex, then initialize the Daily selection
Resume: <sanitized SELECTOR_INITIALIZATION continuation block>
```

### Selector 初始化

```text
Selector Initialization Required
Version: <version>
Reason: DAILY_SELECTION_PROOF_REQUIRED
Action: <canonical --ensure-daily --print-selection command>
Proof: <allowed selected_role and matching selected_effort>
Next: start a new task for the one-run compatibility smoke
```

### 安装完成

```text
Installation Complete
Version: <version>
Source: <40HEX>
Repairs: <action IDs or NONE>
Approved system changes: <action IDs or NONE>
Backup: <symbolic location or NONE>
Configuration preserved: YES
Next: installation and fresh-task smoke are complete
```

### 需要用户操作

```text
Needs User Action
Phase: <phase>
Reason: <one reason code>
Action: <one bounded action>
Proof: <one read-only proof>
Resume: <sanitized SOL_LUNA_ASSIST_RESUME block>
```

### 阻塞

```text
Blocked
Phase: <phase>
Reason: <one reason code>
Writes performed: NO / UNKNOWN / ROLLED_BACK
Next: stop; do not patch managed state or retry automatically
```

## 11．Fresh-task 验收与安全底线

安装后必须完全重新加载 Codex，先按 `SELECTOR_INITIALIZATION` 门禁取得上述
Daily selection 证明；只有通过后，才能在另一个新任务中从 verified exact
checkout 运行：

```text
<PYTHON> scripts/compatibility_smoke.py --codex-home <CODEX_HOME>
```

只有 CLI、Luna capability、Selector、Delegation、Protected state、Runtime
contract 以及最终 Compatibility 全部明确 `PASS`，才能报告安装完成。30 秒无
输出不能直接判定产品失败，应给原命令充分完成时间。

不得使用 `--dangerously-bypass-approvals-and-sandbox`，也不得为了安装成功
要求用户切换到 `danger-full-access`。任何 ownership 冲突、source 不一致、
`BLOCKED`、`FAIL`、`REVIEW REQUIRED`、超时或证据不完整，都必须停止，不能
手工修补托管文件或自动重试。
