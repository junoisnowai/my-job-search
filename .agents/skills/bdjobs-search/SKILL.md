---
name: bdjobs-search
version: 1.0.0
description: >
  Search live job openings on BDjobs.com (Bangladesh).
  Uses dedicated authenticated microservice on Linux (joe@100.86.193.4:19828) for high-speed scraping.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/bdjobs-search/cli/src/cli.ts *)
---

# BDjobs Search Skill (Bangladesh)

Search live job listings from BDJobs.com for **Bangladesh** (Dhaka, Chittagong, Remote, etc.).
Powered by a persistent Linux microservice (`http://100.86.193.4:19828`) running on the remote Linux host.

## When to use this skill
- Search for job openings in Bangladesh across IT, Media, Marketing, Video, and Startup roles.
- Filter by category alias (`it`, `media`, `video`, `marketing`, `creative`, `management`).
- Get full requirements, company details, and salary range for any BDjobs posting.

## Commands

### Search job listings
```bash
bun run .agents/skills/bdjobs-search/cli/src/cli.ts search [flags]
```

Key flags:
- `--query <text>` / `-q <text>` — keyword search (title, skill, role).
- `--category <name>` / `-c <name>` — category alias: `it`, `media`, `video`, `creative`, `marketing`, `management`.
- `--location <text>` / `-l <text>` — city or region (e.g. `Dhaka`).
- `--limit <n>` / `-n <n>` — number of results (default 20).
- `--format json|table|plain` — default `json`.

### Fetch full job detail
```bash
bun run .agents/skills/bdjobs-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

## Usage examples
```bash
# Python & AI roles in IT category
bun run .agents/skills/bdjobs-search/cli/src/cli.ts search -q "python" -c "it" --format table

# Media & Video Editor roles
bun run .agents/skills/bdjobs-search/cli/src/cli.ts search -q "video" -c "media" --format table

# Full detail for a job
bun run .agents/skills/bdjobs-search/cli/src/cli.ts detail 1522795 --format plain
```
