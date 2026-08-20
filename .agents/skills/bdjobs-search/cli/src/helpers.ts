// Helpers and API client for BDJobs Search & Detail CLI

export const DEFAULT_API_URL = process.env.BDJOBS_API_URL || "http://100.86.193.4:19828"

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  deadline: string | null
  deadlineDB?: string | null
  publishDate?: string | null
  salary: string | null
  experience?: string | null
  education?: string | null
  url: string
  personaTrack?: string | null
}

export interface JobDetail extends JobCard {
  companyAddress?: string | null
  companyWeb?: string | null
  companyBusiness?: string | null
  vacancies?: string | null
  jobNature?: string | null
  workplace?: string | null
  otherBenefits?: string | null
  description: string | null
  requirements: string | null
  skillsRequired?: string | null
  suggestedSkills?: string | null
}

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

export function formatTable(results: JobCard[]): void {
  if (results.length === 0) {
    console.log("No job postings found matching criteria.")
    return
  }
  const idW = 10
  const titleW = 34
  const compW = 24
  const deadW = 14
  const salW = 25

  console.log(
    "ID".padEnd(idW) + " | " +
    "TITLE".padEnd(titleW) + " | " +
    "COMPANY".padEnd(compW) + " | " +
    "DEADLINE".padEnd(deadW) + " | " +
    "SALARY"
  )
  console.log("-".repeat(idW + titleW + compW + deadW + salW + 12))

  for (const j of results) {
    const id = (j.id || "").slice(0, idW).padEnd(idW)
    const title = (j.title || "").slice(0, titleW).padEnd(titleW)
    const company = (j.company || "").slice(0, compW).padEnd(compW)
    const deadline = (j.deadline || "--").slice(0, deadW).padEnd(deadW)
    const salary = j.salary || "--"
    console.log(`${id} | ${title} | ${company} | ${deadline} | ${salary}`)
  }
}

export function formatPlain(detail: JobDetail): void {
  console.log(`=======================================================`)
  console.log(`📌 ${detail.title} — ${detail.company}`)
  console.log(`=======================================================`)
  console.log(`🏢 Location: ${detail.location || 'Dhaka, Bangladesh'} (${detail.workplace || 'Office'})`)
  console.log(`💰 Salary: ${detail.salary || 'Not disclosed'} | 🎯 Persona: ${detail.personaTrack || 'Track D'}`)
  console.log(`⏰ Deadline: ${detail.deadline || '--'} | Published: ${detail.publishDate || '--'}`)
  console.log(`👥 Vacancies: ${detail.vacancies || '1'} | Nature: ${detail.jobNature || 'Full Time'}`)
  if (detail.companyWeb) console.log(`🌐 Company Web: ${detail.companyWeb}`)
  
  if (detail.description) {
    console.log(`\n--- 📝 JOB DESCRIPTION ---`)
    console.log(detail.description)
  }
  if (detail.requirements) {
    console.log(`\n--- 🎓 REQUIREMENTS & EXPERIENCE ---`)
    console.log(detail.requirements)
  }
  if (detail.skillsRequired) {
    console.log(`\n--- 🛠️ REQUIRED SKILLS ---`)
    console.log(detail.skillsRequired)
  }
  if (detail.otherBenefits) {
    console.log(`\n--- 🎁 BENEFITS ---`)
    console.log(detail.otherBenefits)
  }
  console.log(`\n🔗 Apply URL: ${detail.url}\n`)
}
