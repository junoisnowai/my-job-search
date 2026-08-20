import { DEFAULT_API_URL, formatTable, writeError, type JobCard } from "../helpers.js"

export interface SearchOpts {
  query?: string
  category?: string
  location?: string
  limit: number
  page: number
  jobage?: number
  sort?: "latest" | "match" | "deadline"
  format: "json" | "table" | "plain"
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  const url = new URL(`${DEFAULT_API_URL}/search`)
  if (opts.query) url.searchParams.set("q", opts.query)
  if (opts.category) url.searchParams.set("category", opts.category)
  if (opts.location) url.searchParams.set("location", opts.location)
  url.searchParams.set("limit", String(opts.limit))
  url.searchParams.set("page", String(opts.page))
  if (opts.jobage) url.searchParams.set("jobage", String(opts.jobage))
  if (opts.sort) url.searchParams.set("sort", opts.sort)

  try {
    const res = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(15000),
    })

    if (!res.ok) {
      writeError(`HTTP ${res.status}: ${res.statusText}`, "FETCH_ERROR")
      return 1
    }

    const data = await res.json() as { results: JobCard[] }
    const results = data.results || []

    if (opts.format === "json") {
      process.stdout.write(JSON.stringify(results, null, 2) + "\n")
    } else if (opts.format === "table") {
      formatTable(results)
    } else {
      for (const j of results) {
        console.log(`\n[${j.id}] ${j.title} @ ${j.company} (Match: ${j.matchScore}%)`)
        console.log(`  📍 Location: ${j.location} | 💰 Salary: ${j.salary || 'Negotiable'}`)
        console.log(`  ⏰ Deadline: ${j.deadline} | 🎯 Track: ${j.personaTrack}`)
        if (j.featuredProject) console.log(`  ⭐ Match Highlight: ${j.featuredProject}`)
        console.log(`  🔗 ${j.url}`)
      }
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "NETWORK_ERROR")
    return 1
  }
}
