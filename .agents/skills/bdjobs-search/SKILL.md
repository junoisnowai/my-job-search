---
name: bdjobs-search
version: 1.0.0
description: >
  Search live job openings on BDjobs.com (Bangladesh).
  Uses authenticated browser session via OpenCLI on Linux to bypass cookie gatekeeping.
context: fork
enabled: true
allowed-tools: Bash(bun run .agents/skills/bdjobs-search/cli/src/cli.ts *)
---

# BDjobs Search Skill (Bangladesh)

> 📌 **Architecture Note**: BDjobs uses session cookies and anti-bot checks. This skill routes requests through the logged-in Brave browser profile (`ch93aym8`) via OpenCLI (Port 19825) on the Linux server (`joe@100.86.193.4`).

## Planned Capabilities
- Search Bangladeshi software, AI, media, and marketing jobs.
- Filter by location (Dhaka, Chittagong, Remote).
- Fetch full job description, deadline, salary range, and company details.
