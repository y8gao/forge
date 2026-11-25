# Forge × Superpowers 共存设计（含「每 checkout 一份活动任务」）

- 日期：2026-11-24
- 状态：**已落地**（`forge-guard` / `forge-init` / bridge / 测试；未提交）
- 修订：2026-11-25 按实现结果重写 §7、§9、§13、§14，新增 §15 撰写规范、§16 复盘
- 覆盖仓：`forge`（本文档 + guard/bridge 改动）、`tsn-scheduler`（两行 git 命令 + 协议）
- 对应活动任务：`per-checkout-mission`

## 1. 动机

Forge 与 Superpowers 同时在线。两者各自都成立，问题出在交集：

1. **默认路径相反** —— Forge 说"单点可逆改动直接做完并报证据"，Superpowers 说"任何创造性工作之前先写设计文档并等批准"。每一件小事都要选边，而两边都是 skill，同一命名空间里没有仲裁规则。
2. **连续性有两个权威** —— Forge 说 `.forge/MISSION.md` 是唯一活动连续性权威（连 archive 都不算）；Superpowers 把 spec/plan 落到 `docs/superpowers/specs/`、`docs/superpowers/plans/`（tsn-scheduler 里两者都在）。"我们到哪了"有两个答案。
3. **worktree 约定相乘出 bug** —— Superpowers 默认用 worktree 隔离，而 Forge 的 MISSION.md 在 git 里 → 每棵新工作树继承一份别人的死任务。这就是本次报的 bug。
4. **成本模型默认不同** —— Forge 的 Loop 有硬上界且 Loop/Assurance 只在显式请求时启动；Superpowers 的并行派发与独立检查是流程的默认零件。

本次既修 3（bug），也把 1/2/4 定成契约，让两者从"抢默认"变成"分工"。

## 2. 现状证据（可复验）

- 六个 checkout 实跑 `forge-guard`：**五个 exit=2**（Mission 为 `done` → 拦全部 `Edit|Write`），补救指引是 `forge-compact --replace-from` 去写 MISSION.md——而它是被跟踪文件，写回去就在合并时冲突。闭环。
- `.worktrees/portal-shell/.forge/MISSION.md` **读不过**（Last Check 里多了一个非 `Ran:`/`Boundary:` 的子弹）→ `MemoryValidationError` → guard `return 0`：**既不设防，又挡住了往上找到真正的任务**。
- 主库与 `.claude/worktrees/portal-home-global` 同为 `mission_id: sanwang-align`、内容不同（07:20 vs 04:05）：同一任务两份分叉。
- 历史 churn：213 个提交里 **71 个动 `.forge/MISSION.md`（33%）**，`INTENT.md` 只有 2 个。
- `merge=union` 探针（临时仓实测）：合并把 frontmatter 变成重复 `mission_id` 字段 → loader 拒绝 → guard 静默失效。故"挂个 merge 属性"是陷阱。

## 3. 目标 / 非目标 / 反目标

**目标**
1. 并发 agent 各自拥有一份活动任务，不共享同一个可变文件。
2. guard 在「本 checkout 没有活动任务」与「任务损坏」时明确拦下，而不是静默放行或借用别人的任务。
3. 定出 Forge 与 Superpowers 的权威划分，并按可执行的方式落到 bridge，使两者互补。

**非目标**
- 嵌套 repo（`.git` 是**目录**）的边界处理。
- `Last Check` 的 `Ran`/`Boundary` 结构化；把 sentence-pinning 测试换成生命周期测试；清理 `.forge/decisions/` 残留。

**反目标**
- 任何锁 / 租约 / 注册表 / daemon / 集成层（`validate-content.py` 禁止 lock/concurrency；`INTENT.md` 反目标含多用户同步）。
- 让 Forge 去提供工程流程（那是 Superpowers 的职责）。
- 改 Superpowers 本身。

## 4. 约束

- **三份 host 拷贝 + portable 副本必须同步**（`scripts/sync-portable-skills.py`）。但 `forge-guard` **不在**同步清单里（它是 Claude Code hook 专属，非 portable），所以 guard 的改动无需同步任何副本。
- **bridge 文本被 `tests/test_forge_init.py` 钉着**：新增内容不得包含子串 `preflight` / `gate` / `reviewer` / `thin protocol`（`gate` 是子串匹配 → 连 `delegate` 也不能出现）。
- **`.forge/` 的条目被测试固定**：每次 init 后 `decisions` / `expectations` / `reviews` / `designs` / `verification` / `forge.db` / `review.md` 都不得存在 → 本文档因此放在 `docs/specs/`，不放 `.forge/decisions/`。
- **tsn-scheduler 的 git 归用户**：只交付命令，不代为执行。

## 5. 方案选择

| | 方案 | 取舍 | 结论 |
|---|---|---|---|
| **A** | **契约式共存**：权威划分写进 Forge 的 bridge（即 AGENTS.md/CLAUDE.md），集成点复用已存在的 `forge-compact --replace-from`，不新增机制 | 零新代码；靠 bridge 的既有优先级生效；代价是契约本身是散文（但 Forge 本来就建立在散文契约 + 一个 hook 上） | **选它** |
| B | 集成层 / 路由器：一个脚本读 Superpowers 的 spec 自动生成 MISSION | 多一个状态源、多一处要同步；直接踩 Forge 的反目标 | 否 |
| C | 二选一：只留一个 | 放弃的正是各自的独有能力（Forge 的门禁与跨 session 记忆，或 Superpowers 的工艺 recipe） | 否，但保留为退路 |
| D | 把 Superpowers 的 recipe 重写进 Forge skill | 27 份拷贝已是本仓最贵的部分，再复制一遍是负收益 | 否 |

## 6. 共存契约

### 6.1 权威划分（每个关注点只有一个权威）

| 关注点 | 权威 | 另一方的角色 |
|---|---|---|
| 做什么 / 到哪了 / 怎么续 | `.forge/MISSION.md` | Superpowers 的 spec/plan 是**输入** |
| 耐久的项目级决策 | `.forge/INTENT.md`（经 `forge-intent`） | brainstorm 的 Decisions 是候选来源 |
| 怎么做出一份好产物（流程） | Superpowers 的 recipe | Forge 不提供流程，也不覆盖它 |
| 验过什么 / 边界在哪 | MISSION 的 `Last Check` | Superpowers 的验证步骤**产生**其内容 |
| 隔离与并行 | git worktree + 每 checkout 一份活动任务 | 两侧的 worktree 约定合并成一条 |
| 成本 / 迭代上界 | MISSION 的 Scope + Loop 上界 | Superpowers 的并行派发必须落在其中 |

### 6.2 四条规则

- **R1 设计文档门槛按影响面判定**：触碰公共行为或接口、不可逆操作、跨多个子系统、或需要跨 session 接力 → 走 Superpowers 的
  「设计文档 + 批准」；单点、可逆、单文件 → 按 Forge 默认直接做完并报证据。Forge 的 "material ambiguity" 就是这条判据的上界。
- **R2 连续性唯一权威是 MISSION**：Superpowers 的 spec/plan 只有在投影之后才生效——outcome → 新 MISSION（`forge-compact --replace-from`）、
  耐久决策 → `INTENT.md`（`forge-intent`）、判据 → MISSION 的 Success Criteria。**未投影的 plan 只是草稿，不能当作「我们到哪了」的依据。**
- **R3 隔离与并行**：一个并发 agent 一个 worktree；新 worktree 先跑 `forge-init`；每棵树用自己的 `mission_id`；
  树被删除之前跑 `forge-compact --complete`（否则记录随树消失）；一个 worktree 只跑一个 agent。
- **R4 验证与成本**：独立检查只在用户显式要求时启动（沿用 Forge 的 doctrine），因此 Superpowers 的独立检查 agent 不自动派发；
  Superpowers 的并行派发必须落在 MISSION 的 Scope 内，并计入 Forge 的 Loop 上界（"Each parallel agent counts separately"）。

### 6.3 生效机制（为什么不是空话）

Superpowers 自己声明：**"User instructions (CLAUDE.md, AGENTS.md, GEMINI.md, etc, direct requests) take precedence over skills"**。
而 `forge-init` 正是往 `AGENTS.md` 与 `CLAUDE.md` 追加带标记的块（tsn-scheduler 里两个文件都已有该块）。
把契约写进 bridge，就**按 Superpowers 自己的优先级规则压过其 "you MUST invoke brainstorming"**。
这是本方案可行的关键：不需要新代码，只要把话说在对的位置。

## 7. 第一部分：每 checkout 一份活动任务

### 7.1 项目侧（每个 checkout 一次）

`forge-init` **自动**把忽略规则写进 `.gitignore`（幂等；已存在则不动；`.gitignore` 是符号链接时只告警、不中断初始化）：

```
# Forge active Mission: one per checkout, never shared
.forge/MISSION.md
```

用户只需做 `forge-init` 不能替你做的那一半——解除对旧文件的跟踪（Forge 不执行 git 写操作）：

```bash
git rm --cached .forge/MISSION.md      # 只解除跟踪，文件留在磁盘
```

保留跟踪：`.forge/INTENT.md`（耐久、共享，历史只动过 2 次）与 `.forge/archive/**`（文件名按 `mission_id` 唯一，跨分支是纯 add、不冲突）。
MISSION.md 不进合并之后，合并**完全不再触碰主库的活动任务**。

**为什么不用 `.git/info/exclude`**：它也能实现"本地忽略"且不改任何被跟踪文件；但它对队友、CI、新克隆都不可见——而"每个 checkout 一份活动任务"是**项目约定**，应当随仓库传播。`.gitignore` 赢在共享。

**协议补丁（本次 bug 的代价）**：archive 从此是该树任务的唯一 git 记录，所以工作树的最后一步必须是
`forge-compact --complete`；否则「MISSION.md 未跟踪 + archive 未生成」= 一删两空（见 14.6）。

### 7.2 `forge-guard`：活动记忆解析模型

guard 不再"找一个 `_project_root` 再读它"，而是显式解析**这段路径受哪份活动记忆治理**，并返回一个状态：

| 状态 | 含义 | 结果 |
|---|---|---|
| `active` | `mission_id` 非 initial，且 `state ∈ {ready, working}` | 放行 |
| `done` / `paused` / `blocked` | 已关闭 / 需恢复 / 受阻 | 拦下，各自给出下一步 |
| `initial` | 仍是占位任务 | 拦下，要求先激活 |
| `no-memory` | 到 checkout 边界，有 `INTENT.md` 但无 `MISSION.md` | 拦下，要求跑 `forge-init` |
| `invalid` | `MISSION.md` 在但读不过 | 拦下，要求修复 |
| `not-forge` | 边界内没有 `.forge/` | 放行（不干预） |

**两条原则**：
- **记忆故障 fail closed，机制故障 fail open。** 记忆读不过 → 拦；hook 收到坏 JSON/坏 payload → 放行（否则会卡死一切）。
- **活动记忆不跨 checkout 边界。** 查找顺序：先看本目录的 `.forge/MISSION.md`，再看本目录是不是 checkout 根（`.git` 存在即可——目录＝主 checkout，文件＝链接工作树或 submodule）。边界处有 `INTENT.md` 无 `MISSION.md` → `no-memory`；边界内压根没有 `.forge/` → `not-forge`。

一条统一规则同时覆盖链接工作树、嵌套 repo 与 submodule。`.forge/` 内写入始终豁免，保留修复通道。

### 7.3 bridge 文本：24 行的协作政策

bridge 仍是同一个标记块（写进 `AGENTS.md` 与 `CLAUDE.md`），但分为三段：Memory-First 核心 + 两个政策小节（M1–M10）。
写两份是刻意的——无论宿主读哪个文件都能看到政策；内容来自**同一个常量**且 `forge-init` 每次重写，所以不会互相漂移。

- **### One active Mission per checkout**：M1 不提交、不借用；M2 新 checkout/worktree 先 `forge-init`、一树一 agent；M3 删树前归档或替换。
- **### Design workflow collaboration**：M4 按影响面决定要不要设计文档；M5 文档落点由 INTENT 记录、不用工具私有路径；M6 设计批准后先投影再计划；M7 每个计划步骤对应一条 Success Criterion；M8 只报观察到的证据、本地测试不超过 `locally_verified`；M9 独立检查只在用户要求时；M10 未经授权不提交/推送/合并。

措辞约束（被 `tests/test_forge_init.py` 钉着）：不得含子串 `preflight` / `gate` / `reviewer`（`gate` 是子串匹配，所以连 `delegate` 都不能出现）。

### 7.4 测试

`tests/test_forge_guard.py` 新增 6 例：checkout 边界无任务被拦且**不借用父 checkout**；worktree 用自己那份（父放行而自己 `done` 仍拦）；worktree 自己 `ready` 可放行；缺失任务在 `.forge/` 内仍可修；嵌套 checkout 无记忆即停；**损坏任务 fail closed 且可修**（替换原先把 fail open 固化成契约的用例）。

`tests/test_forge_init.py`：新增忽略规则幂等用例；bridge 断言加入 M1–M10 与两个小节标题；精确 stdout 断言更新。
同步：`python3 scripts/sync-portable-skills.py`——`forge-guard` **不在**同步清单内（只服务 Claude hook），`forge-init` 在，故三份拷贝各更新一次。

## 8. 1+1>2 的具体收益

1. **设计文档不再是孤儿**：它的决策进 `INTENT.md`、outcome 变成 MISSION、判据被 guard 守着、下个 session 能续。Superpowers 单独给不出这条链路。
2. **"done 有代价" × "verification before completion"**：Success Criteria 未全 `[x]` 就到不了 `done`。Forge 单独只有判据没有方法，Superpowers 单独只有方法没有终点。
3. **验证边界有了载体**：验证步骤的产物填进 `Last Check`，跨 session 不丢（本轮已在 MISSION 里实践）。
4. **并行 agent 各自有可续的上下文**：worktree × 每 checkout 一份活动任务——任何一方单独都给不出。

## 9. 裁定结果（原 Q1–Q2，已定）

- **Q1（R1 门槛）→ 按影响面判定**：公共行为 / 不可逆 / 跨子系统 / 需跨 session 接力才写设计文档并等批准；其余直接做完并报证据。理由：Forge 的 `material ambiguity` 本来就是这条判据的上界，两套规则因此不再打架。
- **Q2（R2 力度）→ 强制投影**：spec/plan 必须投影进 MISSION/INTENT 才算生效。理由：漂移正是这次 bug 的一部分；且投影已有机制兜底（旧任务 `done` 时 guard 拦，投影前改不了码）。

## 10. 验证边界

- 已做：静态读码 + 六个 checkout 实跑 guard + `merge=union` 临时仓探针 + 各拷贝/测试约束的实测（本文件即在本仓写成）。
- 未做：guard 修复后的行为（含 Codex / Cursor 侧对 bridge 改动的反应）；`docs/specs/` 作为长期文档面是否与该仓「不留过程文档」的取向相容；一条完整的 `worktree → forge-init → 工作 → --complete → 合并` 端到端演练。

---

# 11. 架构说明（层级关系与共赢机制）

## 11.1 机制层级：谁真的会"动手"

| 层 | 内容 | 性质 |
|---|---|---|
| **L0 项目自己的文件** | `AGENTS.md` / `CLAUDE.md` ← 共存契约 | 优先级最高（Superpowers 自己声明其高于任何 skill） |
| **L1 契约层** | Forge 的 memory contract + Superpowers 的 process recipes | **都是散文，约束的是 host，不是对方** |
| **L2 机制层** | Forge：`PreToolUse` guard（能拦动作）+ 6 个写 `.forge/` 的脚本<br>Superpowers：**无机制** | 唯一会真正执行的东西 |
| **L3 执行层** | host（读文件、改代码、跑测试、派子代理） | 一切实际动作 |

**结构性结论（后续所有边界的根据）**：
- 两个插件**都不是执行者**。真正干活的是 host。
- **Superpowers 没有机制层**：它的"强制"完全靠 host 采纳，模型可以不理。
- **Forge 有一处真强制**：guard 拦的是动作。
- 因此：**任何"必须发生"的事，只能挂在 Forge 的机制上；Superpowers 只能建议。** 这是设计约束，不是偏好。

## 11.2 宏观形状：框 ⊃ 引擎

```
        ┌──────────── 项目自己的文件（优先级最高）────────────┐
        │  AGENTS.md / CLAUDE.md ← 共存契约（权威划分 + R1–R4）│
        └──────┬──────────────────────────────┬─────────────┘
               │ 读                            │ 读
  ┌────────────▼─────────────────┐   ┌─────────▼──────────────────────┐
  │ 外环 · Forge（慢，跨 session）│   │ 内环 · Superpowers（快，按任务）│
  │ 做什么 / 边界 / 判据 /        │   │ brainstorm→设计→计划→TDD→验证   │
  │ 证据 / 怎么续                 │   │                                │
  │ 有状态：.forge/               │   │ 无状态：产物就是文件           │
  │ 能动性：PreToolUse —— 能拦    │   │ 能动性：SessionStart —— 只能注入│
  │ 缺：没有工艺内容              │   │ 缺：没有生命周期、没有守卫      │
  └───────────────┬───────────────┘   └─────────┬──────────────────────┘
                  └──────── 框住（外环定框，内环在里面干活）────────┘
```

不是上下级：**外环定义"盒子"，内环在盒子里生产产物。** 只在三个维度上重叠，且每个维度恰好一个老大（见 6.1）。

## 11.3 一个任务周期里谁在什么时候出手

```
会话开始 ─────────────────────────────────────────────────────────────────────►
 S 注入取向          F 读 MISSION；bridge 定契约
      │               │
      │               ├── R1：要不要设计文档？（按影响面判定）
      │               │       要 ──► S：brainstorm → 设计 → 你批准
      │               │                      │
      │               ├── 设计投影 ◄─────────┘   ← 唯一的序列化接口（见 12.3 I4）
      │               │   F: forge-compact --replace-from
      │               │      → 活动任务（outcome / scope / 判据 落定）
      │               │
      │               │   ┌──── 内环，反复多轮 ────┐
      │               ├───┤ S：计划 → TDD → 验证   │──► F 只在 5 个真实转变点采样：
      │               │   └───────────────────────┘    用户决策/可见交付/暂停/完成/任务替换
      │               │                                 F: forge-checkpoint
      │               │
      │               └── 收尾：判据全 [x] → done → F: forge-compact --complete（归档）
      │
      └── 全程：F 的 guard 在每次 Edit/Write 上把准入关 —— 唯一的机械强制点
```

## 11.4 共赢的结构性理由：各自的固有缺陷正是对方的长处

| 单独使用时的固有缺陷 | 谁补上 |
|---|---|
| **S**：设计/计划是孤儿——无生命周期、无人守、context 一清就丢 | **F**：变成有状态、有准入、可续的活动任务 |
| **S**：「完成前必须验证」靠自觉，拦不住没验完就宣布完成 | **F**：`done` 要求判据全 `[x]`，而判据来自设计 |
| **S**：默认流程重，小改动也要写设计文档 | **F**：以 `material ambiguity` 当准入阈值（R1） |
| **F**：只有判据、没有方法；判据本身可能拍脑袋 | **S**：判据来自设计与计划的推演 |
| **F**：没有并行语汇与工艺，派发/TDD 不在它范围 | **S**：补方法；R4 把派发纳入 Loop 预算 |
| 两者都没有跨 checkout 的任务身份 | worktree × 每 checkout 一份活动任务（本次修复） |

**Forge 管质量的下限与连续性，Superpowers 管质量的上限。** 这也是方案 D（合并）必然失败的原因：要合并就得让一方违反自己的架构——Forge 的边界禁止它长出流程引擎，Superpowers 作为 skill 包天生无状态。

## 11.5 三行裁决程序

1. 是**状态 / 准入**问题 → Forge。
2. 是**"怎么做好"**问题 → Superpowers。
3. 两者都不涉及 → 用户偏好；未表态时**取更轻的一侧**（更少步骤 / 更少不可逆）。

---

# 12. 分解：边界、责任、实施方法

**角色**：`用户` / `host`（真正动手的执行者）/ `Forge`（外环 = 契约 + 少量机制）/ `Superpowers`（内环 = 纯工艺契约）。

## 12.1 边界（各自明确**不做**的事）

**Forge 不做**
- 不提供任何工程流程 recipe；不判断"这个改动该怎么设计"。
- 不代替 host 做技术决策。
- 不自动派发子代理、不自动启动独立检查。
- 不把 `.forge/archive/` 当权威读取（历史不是权力）。
- 不给自己加锁 / 租约 / 注册表 / 跨 checkout 协调（反目标）。

**Superpowers 不做**
- 不定义、不持有、不修改活动任务或任何生命周期状态。
- 不跨 session 记录"我们到哪了"。
- 不拦任何工具动作。
- 不写 `.forge/`。
- 不决定"是否允许开工"、不决定归档与任务替换。

**越界信号（必须交棒）**
- Forge 侧识别出"这需要设计推演" → 交棒 Superpowers（R1）。
- Superpowers 侧产出 outcome / 判据 / 耐久决策 → **必须交棒 Forge 落盘**（R2），否则产物不算生效。
- 任一方发现冲突且 11.5 裁决不了 → 交用户（Forge doctrine 原文：`expose the conflict and ask the user to adopt, adapt, or discard`）。

## 12.2 责任矩阵（R 执行 / A 最终担责 / C 被咨询 / I 被告知）

| 产物 | 用户 | host | Forge | Superpowers |
|---|---|---|---|---|
| 设计文档 | **A**（批准） | **R**（撰写） | I（只管存放位置与状态约定） | C（提供流程方法） |
| `MISSION.md` | **A**（内容确认） | R（写入） | **R/A**（持有 + 校验 + 守门） | I |
| `INTENT.md` | **A**（耐久决策确认） | R（经 `forge-intent`） | R/A | I |
| plan | A | **R** | I（**且只能是输入，不得当权威**） | C（方法） |
| 证据（evidence） | **A**（是否采信） | **R**（采集） | R（存储 + 等级字段） | C（验证方法） |
| worktree | **A**（git 归用户） | R（创建/删除） | R（边界守门） | C（建议使用） |
| 提交 / patch | **A**（授权） | R（产出） | —（不碰 git） | C（收尾流程） |

**最重要的边界声明（本方案的明确非保证）**：两个插件**都不为"内容是否真实"负责**。
Forge 只保证**格式合法 + 状态机自洽**——它明确不知道 MISSION 里写的是不是真的；Superpowers 只保证**流程被走过**。
**真实性的最终责任人是 host + 用户，不可外包。** 这就是"证据等级不得虚报"只能靠人守的结构原因。

## 12.3 实施方法（逐接口：时机 / 权威 / 动作 / 失败处理）

| # | 接口 | 时机 | 权威 | 具体动作 | 失败/未做时 |
|---|---|---|---|---|---|
| **I1** | 会话开始 | 每次进场 | F | 读 `.forge/INTENT.md` + `.forge/MISSION.md`（bridge 指定）；S 的取向由 SessionStart 自动注入 | MISSION 是 `initial` 或读不过 → guard 拦下 |
| **I2** | 是否走设计流程 | 需求进入时 | F（阈值） | 按 R1 四条判据（公共行为 / 不可逆 / 多子系统 / 跨 session）判定 | 不需要设计 → 直接做完并在 MISSION 反映，**不额外 checkpoint** |
| **I3** | 设计文档 | I2 判定为"要"时 | 用户（批准） | 位置 `docs/specs/YYYY-MM-DD-<topic>-design.md`；带状态行（待确认/已确认/已实现） | 本仓**不适用** Superpowers 默认的 `docs/superpowers/`（测试禁名） |
| **I4** | **设计 → 任务投影**（核心接缝） | 批准之后、实现之前 | F | 见 12.4 字段映射；`forge-compact --replace-from` + `forge-intent` | 不投影 → 该文档只是草稿，**不得作为接续依据** |
| **I5** | 计划 → 判据 | 写计划时 | S（方法）/ F（载体） | plan 的每一步要在 Success Criteria 里能对应到至少一条 | 若 plan 变动改变 outcome/scope/判据 → 重走 I4；仅步骤细分 → 不动 MISSION |
| **I6** | checkpoint | 5 个真实转变点 | F | `forge-checkpoint`；完成后 `forge-compact --complete` | 不 checkpoint：读、编辑、测试、叙述 |
| **I7** | 证据 | 有可报的验证时 | host（真实性）/ F（载体） | 填 `Last Check` 的 `Ran:` / `Boundary:`；等级 `unverified → smoke_verified → locally_verified → reviewed → ci_verified` | 本地测试最高只能标 `locally_verified` |
| **I8** | 独立检查 | **仅用户显式要求** | 用户（授权） | 走 Forge 的 Assurance **或** Superpowers 的独立检查，**二者取一，不重复派** | 不由复杂度或风险自动触发（R4） |
| **I9** | 完成与归档 | 判据全 `[x]` | F | `done` → `forge-compact --complete`；**worktree 删除前必做** | 未 done 就删树 → 记录丢失（已知代价，见 7.1） |
| **I10** | 隔离与并行 | 起并发 agent 时 | 用户（git）/ F（守门） | 一个并发 agent 一个 worktree；新树先 `forge-init`；每树自己的 `mission_id`；一树一 agent；派发计入 Loop 上界 | 忘了 `forge-init` → guard 明确拦下（本次修复后） |
| **I11** | 中断与漂移 | 受阻或计划与任务不一致 | F | `blocked` 必须写真实 blocker；`paused` 必须写 `Resume.Read/Do`；不一致时**以 MISSION 为准** | 差异按"用户决策或任务替换"重新投影（重走 I4） |
| **I12** | 交接 | 跨 session / 跨 agent | F | 读 `INTENT.md` + `MISSION.md` +（若 Next Action 指向）设计文档 | 不读 archive（除非用户要史）；plans 只作输入 |

## 12.4 投影字段映射（I4 的细则）

| 设计文档 | → | 目标 |
|---|---|---|
| Outcome | → | MISSION `## Outcome / Statement` |
| 非目标 / 反目标 | → | MISSION `## Scope / Out` + INTENT `## Non-goals` |
| 约束 | → | MISSION `## Scope / Constraints` |
| 验收 / 成功判据 | → | MISSION `## Success Criteria` |
| Approaches 与否决理由 | → | INTENT `## Decisions`（`D-xxx`，经 `forge-intent`） |
| 未决问题 | → | 阻断则进 `## Next Action`；不阻断则留文档，不入 MISSION |

## 12.5 不变量（**并标注哪些有机制、哪些只靠契约**）

| # | 不变量 | 兜底 |
|---|---|---|
| 1 | 一个 checkout 恰好一个活动任务；archive 不是权威 | **机制**（已存在） |
| 2 | 活动任务属于该 checkout，不跨树借用 | **机制**（本次修复后成立） |
| 3 | 非 `ready` / `working` 状态下不得实质修改项目文件 | **机制**（已存在） |
| 4 | `done` 要求所有判据 `[x]` | **机制**（已存在） |
| 5 | 作为接续依据的 plan/spec 必须有投影 | **仅契约**（不可机检） |
| 6 | 证据等级不得高于其来源 | **仅契约**（不可机检） |
| 7 | 一个 worktree 同时只有一个 agent | **仅契约** |
| 8 | 提交必须由用户授权 | **仅契约**（两侧 AGENTS.md 都写了） |

**读法**：1–4 可以信任（有人守）；5–8 只能靠 host 与用户守。**这张表告诉你哪里能省心、哪里不能。**

## 12.6 两侧实施清单

**Forge 侧（必须发生的事只能挂在这儿）**
1. 进场读 INTENT + MISSION；`initial` 先激活。
2. R1 判定；要设计则等设计批准。
3. 投影（`forge-compact --replace-from` + `forge-intent`）。
4. 5 个转变点 `forge-checkpoint`；完成时 `forge-compact --complete`。
5. 每次写入都经过 guard（准入 + 本次新增的边界与损坏态拦截）。

**Superpowers 侧（只能建议，因此必须放在对的时机）**
1. 仅在 R1 判定为"要"时启用设计与计划流程。
2. 设计与计划的产物**按 12.4 投影**，否则视为草稿。
3. 验证方法与证据分级的建议，产物交给 Forge 的 `Last Check`。
4. 独立检查只在用户显式要求时启动（且与 Forge Assurance 二者取一）。
5. 收尾流程不自行提交——提交是用户授权的事。

---

# 13. 裁定结果（原 Q3–Q4，已定）

- **Q3（设计文档位置）→ 由项目在 `.forge/INTENT.md` 记录，默认 `docs/specs/`。** 推翻初稿写死 `docs/specs/` 的做法：tsn-scheduler 的 `docs/superpowers/` 是既有事实，而 forge 仓的测试对该路径禁名；写死任一路径都会在一个仓里出错。政策只规定"落点由 INTENT 记录、工具私有路径不算项目记录"。
- **Q4（独立检查）→ 走 Forge Assurance**：产物落在 `Last Check` 里可续，Superpowers 的只产出一份报告。二者取一，不重复派。

# 14. 交棒微调（M1–M10）：用政策桥接接口

## 14.1 为什么需要，以及写成什么形式

需要。理由在 11.1 已经给出：**Superpowers 没有机制层，Forge 的 guard 是唯一能拦动作的地方**；而在交棒处，Superpowers 的 skill 有一批**刚性默认**（强制路径、`HARD-GATE`、自动触发的默认动作），它们与 Forge 的契约在若干具体点上直接碰撞。散文是唯一能改这些默认的手段——所以 Forge 必须把政策写进 bridge。

**形式原则（重要）**：这些条文是**本项目的政策**，由 `forge-init` 经用户同意写入 `AGENTS.md` / `CLAUDE.md`，措辞用「本项目规定……」。
**不是**「让 Forge 去命令 Superpowers」，也**不是**覆盖对方的安全门。区别在措辞与内容：可以调整**落点、时机、交付物**；不可以取消**需要用户批准**这类安全约束——那既越界，也不稳定。

## 14.2 微调清单（已落地进 bridge）

钉住的版本：**superpowers 7.0.2**（行号见 14.5）。分组即 bridge 的两个小节。

| # | 触发点 | Superpowers 的默认 | 本项目政策 | 兜底 |
|---|---|---|---|---|
| **M1** | 状态归属 | 逐字复制 MISSION.md 是常见做法 | `.forge/MISSION.md` 是本 checkout 的活动任务，不提交、不借用别树的 | 散文 + M2 机制 |
| **M2** | 新 checkout / worktree | `using-git-worktrees`：已在链接工作树内则 "Skip to Step 2 (Project Setup)" | 在**它自己的 Step 2** 跑 `forge-init`（挂既有步骤，不另立仪式）；一树一 agent | **机制**：无 MISSION → guard 拦 |
| **M3** | 工作树清理 | `finishing-a-development-branch:176+`：只在「未跟踪文件」存在时拦人 | 删除前先 `forge-compact --complete` | 仅契约，且**失败静默**（14.6） |
| **M4** | 会话开始 | `using-superpowers:3` 要求任何回应前先调用相关 skill；`brainstorming:3` 要求任何创造性工作前 **MUST** 用它 | 按影响面分流：小、可逆、单面 → 直接做完并报证据；否则先设计并等批准 | 散文 |
| **M5** | 设计文档落点 | `brainstorming:246` 强制 `docs/superpowers/specs/…` **且 committed**；`writing-plans:16` 强制 `docs/superpowers/plans/…` | 落点由 `.forge/INTENT.md` 记录；工具私有路径不算项目记录 | **硬需求**（forge 仓测试禁名该路径） |
| **M6** | 设计批准之后 | `brainstorming` HARD-GATE（269–283）：下一步是 `writing-plans`，**"no other skill"** | 先投影（`forge-compact --replace-from` + `forge-intent`），再进计划 | **硬需求**；**已有机制**（旧任务 done → guard 拦） |
| **M7** | 计划 → 判据 | `writing-plans` 自带格式 | 每个计划步骤对应一条 Success Criterion | 散文 |
| **M8** | 验证 | `verification-before-completion:3`：提交/开 PR 前自动启用 | 只报观察到的证据；本地测试不超过 `locally_verified` | 散文（不可机检） |
| **M9** | 独立检查 | `requesting-code-review:3`：完成任务/合并前找独立检查 | 只在用户显式要求时；与 Forge Assurance 二者取一 | 散文 |
| **M10** | 提交 | `finishing-a-development-branch:3` 决定如何整合 | 未经用户明确授权，不提交、不推送、不合并 | 散文（两侧 AGENTS.md 已有） |

**M4 窄化的只是流程**（要不要写设计文档），**不是确认义务**：不可逆、公共行为、破坏性动作照样要用户批准——那是两侧共同的安全底线。

## 14.3 三条是硬的，一条会无声失败

- **M5（路径碰撞，硬）**：Superpowers 强制 `docs/superpowers/…` 且要求提交；forge 仓的 `validate-content.py` + `test_archive_boundary.py` 把该路径列为禁用。不微调 = 设计文档写在违规路径上。
- **M6（HARD-GATE 的 "no other skill"，硬）**：它明确禁止设计批准后调用别的 skill，而投影正是"别的 skill"。**这是本次共存里最直接的接口冲突。**
- **M2（边界，有机制兜底）**：修复后，新 worktree 无 `MISSION.md` 会被 guard 直接拦下——"忘跑 forge-init"不再是静默失败。
- **M3（会无声失败）**：见 14.6。

## 14.4 有牙 vs 没牙

- **有机制**：M2（guard 拦）、M6（`done` 态 guard 拦）。
- **纯散文**：M1、M3、M4、M5、M7、M8、M9、M10。
- §12.5 的不变量表因此补第 9 条：**「工作树删除前必须归档」——仅契约，且失败无声**（静默失败比硬失败更危险，因为它不留痕迹）。

## 14.5 版本钉住与维护义务

每条 M 规则都写明它覆盖的是**哪一条原文（文件:行）**。Superpowers 升级后措辞可能变，规则会**静默失效**。因此：
- 本设计以 **7.0.2** 为准；
- 升级 Superpowers 时，把 M1–M10 逐条对一遍（这是一次真实的维护成本，必须承认）；
- bridge 里每条用 `M1`…`M10` 编号，便于复核与测试断言（`tests/test_forge_init.py` 可断言这些编号存在）。

## 14.6 工作树清理：ignored 文件会被静默删除（D1，已实现）

`finishing-a-development-branch` 的清理只在**未跟踪**文件存在时拦人。实测（临时仓）：

```
ignored 文件：  git status --porcelain -uall → 空（看不见）
                git worktree remove → exit=0，树被删掉
untracked 文件：git worktree remove → exit=128 "contains modified or untracked files"
```

**ignored 的 MISSION.md 不拦、也不显示——工作树被静默删掉，未归档的任务记录随之消失。**

- **D1（选）** 忽略，并把"先归档"放进**完成**步骤（I8）而不是**删除**步骤：归档时机本来就在完成；删除那一步没有提醒时机，就别指望它。零噪声、无新风险。
- **D2（否）** 不忽略：`?? .forge/MISSION.md` 成为可见信号且清理会拦住——但保护只覆盖 Superpowers 驱动的清理（harness 自己删树同样静默），却引入 `git add -A` 把文件重新跟踪、**原 bug 复活**的真实风险。
- **D3（否）** 加 `Bash` 匹配的 hook 拦 `git worktree remove`：有机制，但 Forge 会长出一个 git 卫生检查器，超出它的角色（12.1）。

## 14.7 三条不要写

1. **不要写"忽略 Superpowers"。** 要写项目政策。取消对方"需要用户批准"这类安全门，既越界也不稳定。
2. **不要在 SessionStart 再加一个声音。** 那里已经有 Superpowers 与 ponytail 两个注入；仲裁放进 `AGENTS.md`/`CLAUDE.md` 就够——它按 Superpowers 自己的规则本来就压过所有 skill。
3. **不要用散文去追求硬保证。** 能做成机制的只有 guard；其余必须诚实列为"仅契约"。

---

# 15. 撰写规范（角色与口吻）

插件里每种产物服务**一个**读者。混着写就会两头都不合用。

| 产物 | 读者 | 口吻 | 规则 |
|---|---|---|---|
| `AGENTS.md` / `CLAUDE.md` 的 bridge | 任何宿主 agent（Claude / Codex / Cursor） | **项目政策**：陈述句、无第一人称、不写"某工具要求" | 只写"本项目规定 / 不做"；可操作到命令级；不写"忽略某个插件"；措辞避开测试钉住的子串 |
| `SKILL.md` | 被调用时的模型 | 面向执行者：条件 → 动作；`description:` 用第三人称 "Use when…" | 单一职责；≤500 行；不复制可执行逻辑（脚本负责） |
| agent 定义（builder / checker / scout） | 被派发的子代理 | 角色边界：能做什么、不能做什么、回报格式 | 不复述 skill；只写差异与禁止项 |
| 脚本的错误信息 | 正被卡住的 agent | **下一步指令**，不是诊断报告 | 名称 + 一句原因 + 一条可执行命令（`forge-guard` 的 `NEXT_STEP` 是范式） |
| 设计文档（`docs/specs/`） | 未来的实现者 | 决策 + 理由 + 边界；不写叙事 | 必须有 Approaches（含否决项）、目标/非目标/反目标、验证边界 |
| `CHANGELOG.md` | 使用者 | 变更动词开头，一节一类 | 只记行为变化 |

**三条 best practice**

1. **一个文件只服务一个读者。** 政策给 agent、错误给卡住的人、设计给实现者。
2. **不要在一个产物里同时"描述"和"执行"。** skill 描述、脚本执行；让散文承担保证是本次最大的教训——散文会静默失效。
3. **每条会被机器复核的条文都要有稳定标识**（`M1–M10`、`I1–I12`、不变量编号），否则升级后无法审计。

---

# 16. 审核与复盘（按使用场景走 输入 / 过程 / 输出）

## 16.1 场景

| # | 场景 | 输入 | 过程 | 输出 | 结论 |
|---|---|---|---|---|---|
| S1 | 新项目初始化 | 空目录 / 有代码无 `.forge` | `forge-init`：校验 → 建 `.forge/` → 写 bridge → 自动加忽略规则 → 打印 NEXT | 占位任务 + 政策 + 忽略规则 | 闭合；见 P5 |
| S2 | 小改动（单点可逆） | "改个日志措辞" | M4 分流 → guard 放行 → 改完报证据 → **不** checkpoint | diff + evidence；MISSION 不变 | 闭合；见 P9 |
| S3 | 大改动 | 影响面命中 4 条判据 | M4 走设计 → 用户批准 → **M6 投影** → 计划 → TDD → M8 证据 → M7 判据 | 设计文档 + 新 MISSION + 实现 + `Last Check` | 闭合；见 P11 |
| S4 | 就地续接（跨 session） | 同一 checkout 新 session | 读 `INTENT.md` + `MISSION.md` → 按 `Resume.Read/Do` | 继续 | 闭合；见 P12 |
| S5 | 并行 agent / worktree | 2 个独立任务 | 各建 worktree → 各自 `forge-init` → 各自 `mission_id` → guard 各看各的 | 互不触碰对方任务 | 闭合；见 P8 |
| S6 | 记忆损坏 | 手改坏 `MISSION.md` | guard `invalid` → 拦 → 指向 `forge-memory-validate` → `.forge/` 豁免可修 | 修复后恢复 | 闭合（P7 已修） |
| S7 | 工作树收尾 | 任务完成 | `done` → `forge-compact --complete` → 删树 | archive（唯一 git 记录）+ 合并 | 有静默失败面；见 P3 / P10 |
| S8 | Superpowers 升级 | 7.0.2 → 7.x | M1–M10 覆盖的原文可能变 | 政策仍在，但可能不再对准对方步骤 | **无自动检测**；见 P12 |

## 16.2 复盘发现与处置

| # | 发现 | 处置 | 状态 |
|---|---|---|---|
| P1 | 初稿把设计文档路径写死 `docs/specs/`，在 tsn-scheduler 与既有 `docs/superpowers/` 冲突，在 forge 仓又必须避开它 | 改为"落点由 `.forge/INTENT.md` 记录，工具私有路径不算项目记录" | 已修（§13） |
| P2 | 初稿建议先只上 4 条规则，与"设计要完整"矛盾 | 全量 M1–M10，代价约 13 行 | 已修 |
| P3 | ignored 的 `MISSION.md` 让工作树被**静默删除**，未归档即丢失 | D1：忽略 + 归档提醒放进**完成**步骤；残余风险写进不变量第 9 条 | 已定，残余可接受 |
| P4 | guard 原先把损坏记忆 **fail open**，且既有测试把这个行为固化成了契约 | 改 fail closed，替换该用例 | 已修 |
| P5 | 新 checkout 必须先 `forge-init` 才能开工——硬停 | 接受；错误信息直接给出命令，一步可解 | 设计如此 |
| P6 | 一度以为 guard 也要同步三份 portable 拷贝 | 实测：`forge-guard` 不在 `sync-portable-skills.py` 清单内（只服务 Claude hook），零拷贝 | 已确认 |
| P7 | `invalid` 只说"修"，没说怎么知道错在哪 | 复盘后立即补 `forge-memory-validate` 指引 + 测试断言 | 已修 |
| P8 | 工作树基线常是 `origin/main`（落后本地 main），新树里的 `INTENT.md` 可能错过最新耐久决策 | **未解决**：投影前先确认 INTENT 是主线版本（属人工责任，`git` 归用户） | 已知缺口 |
| P9 | forge-core 允许"单轮可逆的附带改动直接做"，而 guard 在 `done` 时一律拦 | **裁决：机制优先**（散文无法覆盖 hook）。要保持可干活，就让 MISSION 停在 active 直到真的无事可做 | 已裁决 |
| P10 | 两个工作树用同一个 `mission_id` 且都归档 → 合并时 add/add 冲突 | 要求 `mission_id` 唯一到工作流（仅契约） | 仅契约 |
| P11 | **投影（M6 / I4）是全流程最易错的一步**：要手写一份 ≤60 行、字段严格的 `ready` 任务，而 Superpowers 的 plan 格式完全不管 Forge 字段 | 不新增生成器（会多一个状态源）；保留 §12.4 的字段映射表，并把它标为最高频出错点 | 接受 |
| P12 | Superpowers 升级后 M1–M10 可能静默失效；`Last Check.Boundary` 是自由文本，可能写空话 | 升级时人工复核 §14.2 的行号/短语；Boundary 结构化在非目标里（后续任务） | 已知成本 |

**一致性结论**：输入（用户需求 + 仓库状态）→ 过程（政策 + guard + 投影）→ 输出（有状态的 Mission + 制品 + 证据）在每个场景都闭合；不闭合的地方只有两类，且都已点明——**静默失败面**（P3、P10）与**人工责任项**（P8、P11、P12）。

## 16.3 本次实际执行的验证

- `forge-guard` 解析模型：10 个合成场景逐一实跑（含"worktree 自己 `done`、父 `ready` 仍被拦"这一关键反向用例）。
- `forge-init`：新建 / 重跑幂等 / 既有 `.gitignore` 无尾换行 / 符号链接 `.gitignore` 只告警 —— 四条实跑。
- `python3 scripts/validate-content.py` PASS；`forge-memory-validate .` PASS；`python3 -m unittest discover -s tests` 全绿；`git diff --check` 干净。
- **未验证**：真实 harness 建树 → `forge-init` → 工作 → `--complete` → 合并 的端到端；Codex / Cursor 侧对 bridge 改动的反应；tsn-scheduler 侧两行 git 命令执行后的回归。
