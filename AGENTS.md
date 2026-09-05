# AGENTS.md

This repository dogfoods Forge Memory-First. These instructions apply to the
whole repository.

## Orientation

At the start of work, read only active `.forge/INTENT.md` and
`.forge/MISSION.md`. If either is missing, run `forge-init`. Do not load
archives, reviews, or `forge.db` by default.

## Default work

The host executes ordinary tasks directly. There is no automatic delegation,
fixed role pipeline, fixed preflight/gate ladder, automatic review artifact,
or automatic Assurance. Clarify consequential ambiguity; record a reasonable
small reversible assumption when useful.

Run targeted checks proportional to the change and report exact evidence and
unchecked boundaries. Only the host writes active control memory.
Use the five checkpoint transitions: user decision, visible delivery, pause,
completion, and mission replacement. Do not checkpoint every step.

Enter Loop or Assurance only when the user explicitly invokes or requests it.
Task-based capability profiles may be selected when available; they are not a
default pipeline.

## 证据纪律
Verification levels（由弱到强）：`unverified → smoke_verified → locally_verified → reviewed → ci_verified`。
`ci_verified` 需要真实 CI 证据；本地测试最高只能标注到 `locally_verified`，不得虚报更高等级。

## Git 使用纪律（强制）
- **未经用户明确指示，禁止执行 `git commit`。**
- **未经用户明确指示，禁止执行 `git push` 或任何将代码推送到远端的操作。**
- 允许在没有明确指示的情况下使用只读/无副作用的 git 命令（如 `git status`、`git diff`、`git log`、`git show`、
  `git branch --list`）来了解当前状态。
- 即使任务看起来「已完成」「已验证」，也不能自行提交或推送；应在回复中说明变更已就绪，等待用户明确要求后再提交/推送。
- 用户的指示必须是针对当次改动的明确授权（例如「帮我提交」「push 一下」），此前的通用授权（如项目约定、历史对话）不构成本次的明确指示。
- **禁止在 commit message 中添加 `Co-authored-by` 之类的署名 trailer。** commit message 只包含变更内容的摘要。

## 其他约束（来自 `.forge/INTENT.md`）
- 跨平台：至少支持 Claude Code + Codex。
- `SKILL.md` 保持 < 500 行；模板需含 frontmatter 以支持 SQLite 解析。
- 永远不做：runtime hooks、block graph、确定性传播引擎、多用户同步、CI 自动化部署。
