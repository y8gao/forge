---
format: "forge-memory-v1"
mission_id: "per-checkout-mission"
state: "working"
checkpointed_at: "2026-11-25T03:00:00Z"
---
# Current Mission

## Outcome
- Statement: 让 Forge 与 Superpowers 共存且各自更强：活动任务改成每个 checkout 一份（MISSION.md 退出 git），forge-guard 用统一解析模型在 checkout 边界与记忆故障时 fail closed，并把两套流程的权威划分与交棒规则写成可执行的 bridge 政策（M1–M10）。

## Scope
- In: `forge-guard` 的解析模型；`forge-init` 的 bridge 政策与忽略规则；`docs/specs/` 的设计文档；三份 host 拷贝同步；两侧测试。
- Out: `.forge/decisions/` 残留清理；`Last Check` 的 `Ran`/`Boundary` 结构化；把 sentence-pinning 测试换成生命周期测试；改 Superpowers 本身；tsn-scheduler 的 git 操作（归用户）。
- Constraints: 不引入锁、注册表、daemon、集成层或新状态源；复用 `forge-compact --replace-from` 作为投影接口；bridge 措辞避开 `preflight` / `gate` / `reviewer`。

## Success Criteria
- [x] 无 MISSION.md 的新 worktree 被明确拦下并提示 forge-init，不借用主库任务（含反向用例：本树 done 而父 ready 仍被拦）。
- [x] 损坏（读不过）的 MISSION 被拦下而不是静默放行，且 `.forge/` 内仍可修复；带回归测试。
- [x] 共存契约（M1–M10）落进 bridge，经 AGENTS.md / CLAUDE.md 的优先级生效。
- [x] `forge-init` 自动写入并保持 `.forge/MISSION.md` 的忽略规则（幂等；符号链接只告警不中断）。
- [x] 三份 host 拷贝与 portable 副本同步且内容校验通过。
- [x] forge 侧 `validate-content`、`forge-memory-validate` 与全量测试全绿。
- [ ] tsn-scheduler 执行 `git rm --cached .forge/MISSION.md` + `forge-init` 后回归全绿（待用户执行 git）。

## Latest Delivery
- 2026-11-25：guard 重写为六态解析模型（active / done / paused / blocked / initial / no-memory / invalid），记忆故障 fail closed、机制故障 fail open，checkout 边界统一覆盖链接工作树、嵌套 repo 与 submodule；`forge-init` 的 bridge 扩为 24 行政策（Memory-First + M1–M10）；`forge-init` 自动维护 `.gitignore` 忽略规则；测试增至 guard 18 例、init 14 例；设计文档 491 行（新增 §15 撰写规范、§16 复盘）。未提交（两侧 AGENTS.md 均要求授权）。

## Next Action
- 用户在 tsn-scheduler 执行 `git rm --cached .forge/MISSION.md`，再跑 `forge-init .`；随后两侧各跑一遍全量测试；提交需用户明确授权。

## Blockers
- None.

## Last Check
- Ran: `validate-content` PASS；`forge-memory-validate .` PASS；`unittest discover -s tests` 全绿；`git diff --check` 干净；guard 10 个合成场景与 init 4 条路径实跑；`sync-portable-skills.py` PASS。
- Boundary: 未做真实 harness 的端到端演练（建树 → init → 工作 → `--complete` → 合并）；未验证 Codex / Cursor 对 bridge 的反应；tsn-scheduler 侧未动（git 归用户）；已知缺口 P8 与仅契约项 P10 / P11 / P12。

## Resume
- Read: `.forge/INTENT.md`、`.forge/MISSION.md`、`docs/specs/2026-11-24-forge-superpowers-coexistence-design.md`。
- Do: 等用户在 tsn-scheduler 执行两行命令并授权提交。
