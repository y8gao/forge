import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { BUNDLED_SKILL_RANK } from '@deepseek-ai/dsh-skill'

const PROVIDER_NAME = 'forge-memory-first'
const INVOCATION = { modelInvocable: true, userInvocable: true }
const SKILLS_ROOT = new URL('./skills/', import.meta.url)
const SHARED_RESOURCE_BASE = {
  kind: 'directory',
  path: fileURLToPath(SKILLS_ROOT),
}
const SKILLS = {
  'forge-core': 'Forge Memory-First default behavior for orientation, ordinary execution, checkpoints, proportional checks, and explicit Loop or Assurance entry.',
  'forge-memory': 'Forge Memory-First control memory, mission state, checkpoints, compaction, archives, and deferred external recall.',
  'forge-init': 'Initialize Forge Memory-First control memory in an existing project.',
  'forge-status': 'Show the current Forge Memory-First mission from active project memory.',
  'forge-loop': 'Explicit prompt-only bounded delivery loop with visible deltas, falsifying checks, and host-owned checkpoints.',
  'forge-assurance': 'Explicit claim-driven independent checking with compact evidence, exact gaps, and honest verification boundaries.',
  'forge-scout': 'Temporary read-only discovery and research profile selected by the host when a task needs focused investigation.',
  'forge-builder': 'Temporary implementation profile selected by the host for a declared write scope and targeted checks.',
  'forge-checker': 'Temporary read-only checking and attack profile selected by the host for explicit claims.',
}

function candidate(name, description) {
  const skillRoot = new URL(`./skills/${name}/`, import.meta.url)
  return {
    name,
    description,
    invocation: INVOCATION,
    provider: PROVIDER_NAME,
    source: 'bundled',
    resourceBase: SHARED_RESOURCE_BASE,
    rank: BUNDLED_SKILL_RANK,
    locator: new URL('SKILL.md', skillRoot),
  }
}

const CANDIDATES = Object.entries(SKILLS).map(([skillName, description]) =>
  candidate(skillName, description),
)
const CANDIDATES_BY_NAME = new Map(
  CANDIDATES.map((entry) => [entry.name, entry]),
)

const provider = {
  name: PROVIDER_NAME,
  list: () => Promise.resolve(CANDIDATES),
  async get(requested) {
    const entry = CANDIDATES_BY_NAME.get(requested.name)
    if (!entry) return undefined
    return {
      name: entry.name,
      description: entry.description,
      invocation: entry.invocation,
      provider: entry.provider,
      source: entry.source,
      resourceBase: entry.resourceBase,
      content: await readFile(entry.locator, 'utf8'),
    }
  },
}

export const name = 'forge-memory-first-skills'
export const inject = ['skills']

export function apply(ctx) {
  ctx.skills.registerProvider(() => provider)
}
