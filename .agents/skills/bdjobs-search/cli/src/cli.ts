#!/usr/bin/env bun
// BDJobs Search CLI for Hamim Ahmed (Sayed Johon)
// Queries the remote BDJobs API microservice hosted on Linux (joe@100.86.193.4:19828)

import { runSearch, type SearchOpts } from "./commands/search.js"
import { runDetail, type DetailOpts } from "./commands/detail.js"
import { DEFAULT_API_URL, writeError } from "./helpers.js"

interface Flags {
  _: string[]
  [k: string]: string | boolean | string[]
}

const ALIAS: Record<string, string> = {
  q: "query",
  c: "category",
  l: "location",
  n: "limit",
  p: "page",
}

function parseFlags(argv: string[]): Flags {
  const flags: Flags = { _: [] }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (!a.startsWith("-")) {
      ;(flags._ as string[]).push(a)
      continue
    }
    const name = a.replace(/^-+/, "")
    const key = ALIAS[name] ?? name
    const next = argv[i + 1]
    let value: string | boolean = true
    if (next !== undefined && !next.startsWith("-")) {
      value = next
      i++
    }
    flags[key] = value
  }
  return flags
}

const HELP = `bdjobs-search-cli — search BDjobs.com via the Linux microservice

USAGE
  bun run src/cli.ts search [-q "<keywords>"] [-c "<category>"] [-l "<location>"] [--format json|table|plain]
  bun run src/cli.ts detail <id|url> [--format json|plain]

SEARCH FLAGS
  --query, -q <text>       Keywords (e.g. "python", "video", "marketing")
  --category, -c <name>    Category alias (it, media, marketing, creative, etc.)
  --location, -l <text>    Location (Dhaka, Chittagong, Remote, etc.)
  --jobage <days>          Posted within N days
  --limit, -n <n>          Number of results (default 20, max 50)
  --page, -p <n>           Page number (1-indexed)
  --format <fmt>           json (default) | table | plain

DETAIL
  <id|url>                 BDjobs Job ID or full job details URL

EXAMPLES
  bun run src/cli.ts search -q "python" -c "it" --limit 10 --format table
  bun run src/cli.ts search -q "video editor" -c "media" --format table
  bun run src/cli.ts detail 1522795 --format plain

Microservice endpoint: ${DEFAULT_API_URL}
`

async function main(): Promise<number> {
  const argv = process.argv.slice(2)
  const flags = parseFlags(argv)
  const cmd = (flags._ as string[])[0]

  if (!cmd || flags.help || flags.h) {
    process.stdout.write(HELP)
    return cmd ? 0 : 1
  }

  if (cmd === "search") {
    const fmt = (flags.format as string) || "json"
    const opts: SearchOpts = {
      query: typeof flags.query === "string" ? flags.query : undefined,
      category: typeof flags.category === "string" ? flags.category : undefined,
      location: typeof flags.location === "string" ? flags.location : undefined,
      limit: flags.limit ? parseInt(flags.limit as string, 10) : 20,
      page: flags.page ? parseInt(flags.page as string, 10) : 1,
      jobage: flags.jobage ? parseInt(flags.jobage as string, 10) : undefined,
      format: (["json", "table", "plain"].includes(fmt) ? fmt : "json") as SearchOpts["format"],
    }
    return runSearch(opts)
  }

  if (cmd === "detail") {
    const id = (flags._ as string[])[1]
    if (!id) {
      writeError("detail requires a <id|url>", "NO_ID")
      return 1
    }
    const fmt = (flags.format as string) || "json"
    const opts: DetailOpts = { id, format: fmt === "plain" ? "plain" : "json" }
    return runDetail(opts)
  }

  writeError(`Unknown command "${cmd}"`, "BAD_CMD")
  return 1
}

main()
  .then((code) => process.exit(code))
  .catch((e) => {
    writeError(e instanceof Error ? e.message : String(e), "INTERNAL_ERROR")
    process.exit(1)
  })
