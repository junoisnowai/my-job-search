// Helpers and API client for BDJobs Search & Deep Research CLI

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
  personaTrack: string
  matchScore: number
  matchedKeywords?: string[]
  featuredProject?: string
}

export interface JobDossier {
  id: string
  title: string
  company: string
  companyWebsite?: string | null
  companyAddress?: string | null
  companyOverview?: string | null
  location: string
  workplace: string
  jobNature: string
  postedOn: string
  deadline: string
  deadlineDB?: string
  vacancies: string
  compensation: {
    salaryRange: string
    minSalary?: string | null
    maxSalary?: string | null
    benefits: string
  }
  contacts: {
    applicationMethod: "direct_email" | "online" | "external_url" | "walk_in" | "hard_copy"
    primaryEmail?: string | null
    allEmails: string[]
    phoneNumbers: string[]
    applicationInstructions?: string | null
    applyUrl: string
  }
  requirements: {
    education: string
    experience: string
    additionalRequirements: string
    hardSkills: string[]
    suggestedSkills: string[]
    ageLimit?: string | null
    gender?: string | null
  }
  description: string
  aiPersonaMatching: {
    bestPersonaTrack: string
    matchScore: number
    matchedKeywords: string[]
    featuredProjects: string[]
    cvTailoringAdvice: string
  }
  url: string
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
  const titleW = 32
  const compW = 22
  const matchW = 7
  const deadW = 12
  const salW = 24

  console.log(
    "ID".padEnd(idW) + " | " +
    "TITLE".padEnd(titleW) + " | " +
    "COMPANY".padEnd(compW) + " | " +
    "MATCH".padEnd(matchW) + " | " +
    "DEADLINE".padEnd(deadW) + " | " +
    "SALARY"
  )
  console.log("-".repeat(idW + titleW + compW + matchW + deadW + salW + 15))

  for (const j of results) {
    const id = (j.id || "").slice(0, idW).padEnd(idW)
    const title = (j.title || "").slice(0, titleW).padEnd(titleW)
    const company = (j.company || "").slice(0, compW).padEnd(compW)
    const match = (String(j.matchScore ?? 0) + "%").padEnd(matchW)
    const deadline = (j.deadline || "--").slice(0, deadW).padEnd(deadW)
    const salary = j.salary || "--"
    console.log(`${id} | ${title} | ${company} | ${match} | ${deadline} | ${salary}`)
  }
}

export function formatPlainDossier(dossier: JobDossier): void {
  console.log(`\n=======================================================`)
  console.log(`📌 ${dossier.title} — ${dossier.company}`)
  console.log(`=======================================================`)
  console.log(`🏢 Location: ${dossier.location} (${dossier.workplace})`)
  console.log(`💰 Salary: ${dossier.compensation.salaryRange} | 🎯 Persona: ${dossier.aiPersonaMatching.bestPersonaTrack} (${dossier.aiPersonaMatching.matchScore}% Match)`)
  console.log(`⏰ Deadline: ${dossier.deadline} | Published: ${dossier.postedOn}`)
  console.log(`👥 Vacancies: ${dossier.vacancies} | Nature: ${dossier.jobNature}`)
  if (dossier.companyWebsite) console.log(`🌐 Company Web: ${dossier.companyWebsite}`)
  if (dossier.companyAddress) console.log(`📍 Address: ${dossier.companyAddress}`)

  console.log(`\n--- 📬 APPLICATION & DIRECT CONTACTS ---`)
  console.log(`• Method: ${dossier.contacts.applicationMethod.toUpperCase()}`)
  if (dossier.contacts.allEmails.length > 0) {
    console.log(`• Recruiter Email(s): ${dossier.contacts.allEmails.join(", ")}`)
  }
  if (dossier.contacts.phoneNumbers.length > 0) {
    console.log(`• Phone / Mobile: ${dossier.contacts.phoneNumbers.join(", ")}`)
  }
  if (dossier.contacts.applicationInstructions) {
    console.log(`• Instructions: ${dossier.contacts.applicationInstructions}`)
  }

  console.log(`\n--- 🎯 AI TAILORING ADVICE ---`)
  console.log(`• Recommended Feature Projects: ${dossier.aiPersonaMatching.featuredProjects.join(", ")}`)
  console.log(`• Action Advice: ${dossier.aiPersonaMatching.cvTailoringAdvice}`)

  if (dossier.description) {
    console.log(`\n--- 📝 JOB DESCRIPTION ---`)
    console.log(dossier.description)
  }
  if (dossier.requirements.education || dossier.requirements.experience) {
    console.log(`\n--- 🎓 REQUIREMENTS & EXPERIENCE ---`)
    if (dossier.requirements.education) console.log(dossier.requirements.education)
    if (dossier.requirements.experience) console.log(dossier.requirements.experience)
    if (dossier.requirements.additionalRequirements) console.log(dossier.requirements.additionalRequirements)
  }
  if (dossier.requirements.hardSkills.length > 0) {
    console.log(`\n--- 🛠️ REQUIRED SKILLS ---`)
    console.log(dossier.requirements.hardSkills.join(", "))
  }
  if (dossier.compensation.benefits) {
    console.log(`\n--- 🎁 BENEFITS ---`)
    console.log(dossier.compensation.benefits)
  }
  console.log(`\n🔗 Apply URL: ${dossier.url}\n`)
}
