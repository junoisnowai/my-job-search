# 🤖 Sub-Project Log: AI Job Search

## 🧭 Architecture & Execution Flow Map

```mermaid
graph TD
    User["👤 Sayed Johon"]
    Setup["⚙️ /setup<br>(Profile & Target Roles)"]
    Scraper["🔍 /scrape<br>(BDJobs, LinkedIn, etc. via Bun CLI)"]
    LinuxService["⚡ BDJobs Microservice<br>(Linux host:19828 / PM2)"]
    Apply["📝 /apply &lt;URL&gt;<br>(Drafter Agent -> Reviewer Agent)"]
    Compile["📄 LaTeX Engine<br>(lualatex / xelatex -> Tailored PDF CV & Letter)"]
    Interview["🎯 /interview<br>(Roleplay & Salary Benchmarking)"]

    User --> Setup
    Setup --> Scraper
    Scraper --> LinuxService
    Scraper --> Apply
    Apply --> Compile
    Apply --> Interview
```

### ⚡ Sub-Project Profile & Workload Assessment

* **Compute Intensity**: **Lightweight (Low Workload)**.
  - Consists of lightweight CLI scraping (via `bun`), LaTeX template compilation (`lualatex`/`xelatex`), Python salary data lookups, and LLM text generation.
  - Can easily run 100% on the local macOS host without burdening CPU/GPU.
  - **Remote Linux Offload**: BDJobs scraping runs on a high-speed authenticated REST microservice (`http://100.86.193.4:19828`) managed via PM2 on the Linux server (`joe@100.86.193.4`).

### 🗂️ Component Directory Map

* **Candidate Profile Source of Truth**: [`CLAUDE.md`](../CLAUDE.md) & [`.claude/skills/job-application-assistant/`](../.claude/skills/job-application-assistant/)
* **Portal Search Skills**:
  - `bdjobs-search`: [`.agents/skills/bdjobs-search/`](../.agents/skills/bdjobs-search/) (BDJobs Bangladesh API/Microservice client)
  - `linkedin-search`: [`.agents/skills/linkedin-search/`](../.agents/skills/linkedin-search/) (LinkedIn public guest API)
  - `freehire-search`: [`.agents/skills/freehire-search/`](../.agents/skills/freehire-search/) (Tech/AI jobs)
* **Microservices**: [`tools/bdjobs_service.py`](../tools/bdjobs_service.py) (FastAPI + Session Manager on port `19828`)
* **CV & Cover Letter Templates**: [`templates/`](../templates/), [`cv/`](../cv/), [`cover_letters/`](../cover_letters/)
* **Salary Benchmark Tool**: [`salary_lookup.py`](../salary_lookup.py)
* **Testing Suite**: [`tests/`](../tests/)

---

## 📜 Sub-Project Change Log

- **2026-08-20**: Implemented BDJobs Scraping Engine & Microservice (`bdjobs-api` on PM2, `http://100.86.193.4:19828`). Added `bdjobs-search` Bun CLI skill mapped to Sayed Johon's 4 Persona Tracks.
- **2026-08-20**: Initialized and cloned `ai-job-search` from upstream `MadsLorentzen/ai-job-search`. Completed compute-workload assessment (Lightweight/local Mac capable) and established sub-app project log.
