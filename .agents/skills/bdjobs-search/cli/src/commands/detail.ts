import { DEFAULT_API_URL, formatPlain, writeError, type JobDetail } from "../helpers.js"

export interface DetailOpts {
  id: string
  format: "json" | "plain"
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  // Extract ID if a full URL was passed
  let jobId = opts.id
  const match = opts.id.match(/(?:details\/|id=)(\d+)/)
  if (match) {
    jobId = match[1]
  }

  const url = `${DEFAULT_API_URL}/detail/${jobId}`

  try {
    const res = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(15000),
    })

    if (res.status === 404) {
      writeError(`Job posting ${jobId} not found`, "NOT_FOUND")
      return 1
    }

    if (!res.ok) {
      writeError(`HTTP ${res.status}: ${res.statusText}`, "FETCH_ERROR")
      return 1
    }

    const detail = await res.json() as JobDetail

    if (opts.format === "json") {
      process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
    } else {
      formatPlain(detail)
    }
    return 0
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "NETWORK_ERROR")
    return 1
  }
}
