#!/usr/bin/env python3
"""
BDJobs Enterprise Research Engine (v2.0) for Hamim Ahmed (Sayed Johon)
High-speed authenticated REST API & CLI for deep job research, direct recruiter contact extraction,
recency ranking, and AI Persona Track matching.
"""

import os
import re
import sys
import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bdjobs_service")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
COOKIES_PATH = Path(os.environ.get("BDJOBS_COOKIES_PATH", BASE_DIR / "assets" / "cookies_bdjobs.com.txt"))

# Category Aliases
CATEGORY_MAP: Dict[str, int] = {
    "it": 8, "software": 8, "ai": 8, "tech": 8, "backend": 8, "frontend": 8, "fullstack": 8,
    "media": 10, "video": 10, "content": 10, "youtube": 10, "broadcasting": 10,
    "creative": 18, "design": 18, "graphics": 71, "animation": 18,
    "marketing": 9, "sales": 9, "digital_marketing": 30, "ecommerce": 30, "growth": 9, "seo": 30,
    "management": 7, "admin": 7, "operations": 7, "consultancy": 13, "research": 13,
}

# Persona Track Definitions & Keywords for Scoring
PERSONA_PROFILES = {
    "Track A: AI Systems & Automation Engineer": {
        "keywords": [
            "python", "fastapi", "django", "ai", "machine learning", "rag", "llm", "automation",
            "docker", "backend", "api", "restful", "postgresql", "mysql", "redis", "n8n",
            "langchain", "microservices", "cloud", "aws", "data engineer", "software engineer"
        ],
        "primary_categories": [8],
        "featured_projects": ["MicTab Desktop Voice Agent", "AutometaBot RAG Support Engine", "FastAPI Enterprise Automations"],
        "recommended_cv_focus": "Lead with custom AI pipeline architectures, Python backend systems, Supabase pgvector RAG, and n8n workflows."
    },
    "Track B: Media Production & Video Director": {
        "keywords": [
            "video editor", "video creator", "video production", "cinematography", "davinci resolve",
            "premiere pro", "after effects", "creative director", "youtube", "motion graphics",
            "camera", "lighting", "director", "storytelling", "hook", "audio mastering", "film"
        ],
        "primary_categories": [10, 18, 71],
        "featured_projects": ["JunoverseAI YouTube Channel Host & Director", "Canon 5D Mk III + 70-200mm f/2.8L Cinematography", "DaVinci Resolve Node Color Grading"],
        "recommended_cv_focus": "Lead with on-camera hosting, documentary research/scripting, high-retention 3s hooks, DaVinci Resolve color science, and cinema optics."
    },
    "Track C: Growth Marketing & Copywriting": {
        "keywords": [
            "growth marketer", "digital marketing", "copywriter", "content strategist", "cro",
            "conversion rate", "social media", "audience", "funnel", "seo", "e-commerce",
            "lead generation", "email marketing", "branding", "retention"
        ],
        "primary_categories": [9, 30],
        "featured_projects": ["AutometaBot Social DM/Comment Growth Automation", "Psychological Copywriting & High-Converting Hooks", "Amazon KDP Digital Publishing"],
        "recommended_cv_focus": "Lead with consumer psychology, high-converting copy, omnichannel social automation, and data-driven CRO."
    },
    "Track D: Technical Generalist / Startup Lead": {
        "keywords": [
            "product lead", "operations", "founder", "project manager", "scrum", "general management",
            "business analyst", "consultant", "technical lead", "strategy", "startup", "coordinator"
        ],
        "primary_categories": [7, 13],
        "featured_projects": ["Founder of MicTab.com & PeeAI.com", "0-to-1 Product Ownership & Scaling", "Cross-Functional Agency Automation"],
        "recommended_cv_focus": "Lead with 0-to-1 founder execution, bridging technical software engineering and creative media distribution."
    }
}

def clean_html(raw_html: Optional[str]) -> str:
    """Converts HTML to clean, readable text/markdown."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    for li in soup.find_all("li"):
        li.insert_before("\n* ")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n\n")
    text = soup.get_text()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

def extract_contacts(raw_text: str) -> Tuple[List[str], List[str]]:
    """Extracts email addresses and Bangladeshi phone numbers from text."""
    if not raw_text:
        return [], []
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'(?:\+?880|0)1[3-9]\d{8}'
    
    emails = list(set(re.findall(email_pattern, raw_text)))
    valid_emails = [e for e in emails if not any(x in e.lower() for x in ["example.com", "test.com", "yourname@"])]
    phones = list(set(re.findall(phone_pattern, raw_text)))
    return valid_emails, phones

def score_persona_match(title: str, text: str, cat_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculates match score across the 4 Persona Tracks."""
    combined = f"{title.lower()} {text.lower()}"
    best_track = "Track D: Technical Generalist / Startup Lead"
    highest_score = 0
    scores = {}
    matched_skills_map = {}

    for track_name, config in PERSONA_PROFILES.items():
        score = 0
        matched_kw = []
        if cat_id and cat_id in config["primary_categories"]:
            score += 25
        
        for kw in config["keywords"]:
            if kw in title.lower():
                score += 30
                matched_kw.append(kw)
            elif kw in combined:
                score += 5
                if kw not in matched_kw:
                    matched_kw.append(kw)

        final_score = min(score, 100)
        scores[track_name] = final_score
        matched_skills_map[track_name] = matched_kw

        if final_score > highest_score:
            highest_score = final_score
            best_track = track_name

    if highest_score < 20:
        highest_score = 25
        best_track = "Track D: Technical Generalist / Startup Lead"

    track_info = PERSONA_PROFILES[best_track]
    return {
        "bestTrack": best_track,
        "matchScore": highest_score,
        "allScores": scores,
        "matchedKeywords": matched_skills_map.get(best_track, []),
        "featuredProjects": track_info["featured_projects"],
        "recommendedCvFocus": track_info["recommended_cv_focus"],
    }

class BDJobsClient:
    def __init__(self, cookies_file: Path = COOKIES_PATH):
        self.cookies_file = cookies_file
        self.cookies: Dict[str, str] = {}
        self.jwt_token: str = ""
        self.session = requests.Session()
        self.load_cookies()

    def load_cookies(self):
        if not self.cookies_file.exists():
            logger.warning(f"Cookies file not found at {self.cookies_file}")
            return
        try:
            with open(self.cookies_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.cookies = {c["name"]: c["value"] for c in data if "name" in c and "value" in c}
            self.jwt_token = self.cookies.get("AccessTokenForJobseeker", "")
            self.session.cookies.update(self.cookies)
            logger.info(f"Loaded {len(self.cookies)} cookies from {self.cookies_file}")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")

    def get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://bdjobs.com",
            "Referer": "https://bdjobs.com/",
        }
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

    def search_jobs(
        self,
        keyword: str = "",
        category: Optional[str] = None,
        location: str = "",
        page: int = 1,
        limit: int = 20,
        jobage: Optional[int] = None,
        sort_by: str = "latest",
    ) -> List[Dict[str, Any]]:
        """Searches BDJobs with recency filtering and persona scoring."""
        fcat_id = ""
        cat_numeric = None
        if category:
            cat_lower = str(category).lower().strip()
            if cat_lower in CATEGORY_MAP:
                cat_numeric = CATEGORY_MAP[cat_lower]
                fcat_id = str(cat_numeric)
            elif cat_lower.isdigit():
                cat_numeric = int(cat_lower)
                fcat_id = cat_lower

        params = {
            "Icat": "", "industry": "", "category": "", "org": "", "jobNature": "",
            "Fcat": fcat_id,
            "location": location or "",
            "Qot": "", "jobType": "", "jobLevel": "",
            "postedWithin": str(jobage) if jobage else "",
            "deadline": "",
            "keyword": keyword or "",
            "pg": str(page),
            "qAge": "", "Salary": "", "experience": "", "gender": "", "MExp": "",
            "genderB": "", "MPostings": "", "MCat": "", "version": "",
            "rpp": str(min(limit, 50)),
            "Newspaper": "", "armyp": "", "QDisablePerson": "", "pwd": "",
            "workplace": "", "facilitiesForPWD": "", "SaveFilterList": "",
            "UserFilterName": "", "HUserFilterName": "", "earlyJobAccess": "",
            "isPro": "0", "ToggleJobs": "true", "isFresher": "false",
        }

        url = "https://api.bdjobs.com/Jobs/api/JobSearch/GetJobSearch"
        try:
            res = self.session.get(url, params=params, headers=self.get_headers(), timeout=15)
            if res.status_code != 200:
                logger.error(f"Search failed: HTTP {res.status_code}")
                return []

            data = res.json()
            raw_jobs = data.get("data", []) or []
            results = []

            for r in raw_jobs:
                job_id = str(r.get("Jobid", ""))
                title = (r.get("jobTitle", "") or r.get("JobTitleBng", "Untitled")).strip()
                company = (r.get("companyName", "") or "Unknown Company").strip()
                deadline = r.get("deadline", "")
                deadline_db = r.get("deadlineDB", "")
                pub_date = r.get("publishDate", "")
                salary = (r.get("Salary", "") or r.get("JobSalaryRange", "")).strip()
                exp = clean_html(r.get("Exp", "") or r.get("experience", ""))
                edu = clean_html(r.get("MinEdu", "") or r.get("eduRec", ""))
                loc = (r.get("jobLocation", "") or r.get("Location", "") or "Bangladesh").strip()
                preview_desc = clean_html(r.get("jobDescription", "") or r.get("jobContext", ""))

                match_intel = score_persona_match(title, f"{preview_desc} {exp} {edu}", cat_numeric)

                results.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": loc,
                    "deadline": deadline,
                    "deadlineDB": deadline_db,
                    "publishDate": pub_date,
                    "salary": salary if salary and salary != "--" else "Negotiable / Undisclosed",
                    "experience": exp if exp else None,
                    "education": edu if edu else None,
                    "url": f"https://bdjobs.com/h/details/{job_id}?ln=1",
                    "personaTrack": match_intel["bestTrack"],
                    "matchScore": match_intel["matchScore"],
                    "matchedKeywords": match_intel["matchedKeywords"],
                    "featuredProject": match_intel["featuredProjects"][0],
                })

            if sort_by == "latest":
                results.sort(key=lambda x: x.get("publishDate", ""), reverse=True)
            elif sort_by == "match":
                results.sort(key=lambda x: x.get("matchScore", 0), reverse=True)
            elif sort_by == "deadline":
                results.sort(key=lambda x: x.get("deadlineDB", "") or "9999")

            return results
        except Exception as e:
            logger.error(f"Error executing BDJobs search: {e}")
            return []

    def get_job_dossier(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Extracts complete 360 research dossier including direct contact channels."""
        url = "https://gateway.bdjobs.com/jobapply/api/JobSubsystem/Job-Details"
        params = {"JobId": str(job_id), "ln": 1}

        try:
            res = self.session.get(url, params=params, headers=self.get_headers(), timeout=15)
            if res.status_code != 200:
                logger.error(f"Failed to fetch detail for {job_id}: HTTP {res.status_code}")
                return None

            data = res.json()
            jobs = data.get("data", [])
            if not jobs:
                return None

            job = jobs[0]
            title = (job.get("JobTitle", "") or "Untitled").strip()
            company = (job.get("CompnayName", "") or job.get("CompanyNameENG", "Company")).strip()
            cat_id = int(job.get("CategoryID", 0)) if str(job.get("CategoryID", "")).isdigit() else None
            
            raw_desc = job.get("JobDescription", "") or ""
            raw_reqs = job.get("EducationRequirements", "") or ""
            raw_add_reqs = job.get("AdditionJobRequirements", "") or ""
            raw_instr = job.get("ApplyInstruction", "") or ""
            raw_exp = job.get("experience", "") or ""
            raw_benefits = job.get("JobOtherBenifits", "") or ""
            raw_skills = job.get("SkillsRequired", "") or ""
            raw_sugg_skills = job.get("SuggestedSkills", "") or ""
            
            apply_email_field = job.get("ApplyEmail", "") or job.get("JobAppliedEmail", "")
            mobile_field = job.get("MobileNo", "") or ""
            company_web = (job.get("CompanyWeb", "") or "").strip()
            company_addr = (job.get("CompanyAddress", "") or "").strip()
            company_biz = clean_html(job.get("CompanyBusiness", ""))

            # Deep Contact Extraction
            full_text_dump = f"{raw_desc} {raw_reqs} {raw_add_reqs} {raw_instr} {apply_email_field} {mobile_field}"
            extracted_emails, extracted_phones = extract_contacts(full_text_dump)
            if mobile_field and mobile_field not in extracted_phones:
                extracted_phones.append(mobile_field)

            # Determine Application Method
            app_method = "online"
            if extracted_emails or apply_email_field:
                app_method = "direct_email"
            elif job.get("ApplyURL"):
                app_method = "external_url"
            elif "walk in" in raw_instr.lower() or job.get("WalkInInterview"):
                app_method = "walk_in"
            elif "hard copy" in raw_instr.lower() or job.get("HardCopy"):
                app_method = "hard_copy"

            # Match Intelligence
            match_intel = score_persona_match(title, full_text_dump, cat_id)

            return {
                "id": str(job.get("JobId", job_id)),
                "title": title,
                "company": company,
                "companyWebsite": company_web if company_web else None,
                "companyAddress": company_addr if company_addr else None,
                "companyOverview": company_biz if company_biz else None,
                "location": (job.get("JobLocation", "") or "Dhaka, Bangladesh").strip(),
                "workplace": job.get("JobWorkPlace", "Work at office"),
                "jobNature": job.get("JobNature", "Full Time"),
                "postedOn": job.get("PostedOn", ""),
                "deadline": job.get("Deadline", ""),
                "deadlineDB": job.get("DeadlineDB", ""),
                "vacancies": job.get("JobVacancies", "1"),
                "compensation": {
                    "salaryRange": job.get("JobSalaryRange", "Negotiable"),
                    "minSalary": job.get("JobSalaryMinSalary") if job.get("JobSalaryMinSalary") != "0" else None,
                    "maxSalary": job.get("JobSalaryMaxSalary") if job.get("JobSalaryMaxSalary") != "0" else None,
                    "benefits": clean_html(raw_benefits) if raw_benefits else "Standard company benefits",
                },
                "contacts": {
                    "applicationMethod": app_method,
                    "primaryEmail": extracted_emails[0] if extracted_emails else None,
                    "allEmails": extracted_emails,
                    "phoneNumbers": extracted_phones,
                    "applicationInstructions": clean_html(raw_instr) if raw_instr else None,
                    "applyUrl": job.get("ApplyURL") or f"https://bdjobs.com/h/details/{job_id}?ln=1",
                },
                "requirements": {
                    "education": clean_html(raw_reqs),
                    "experience": clean_html(raw_exp),
                    "additionalRequirements": clean_html(raw_add_reqs),
                    "hardSkills": [s.strip() for s in raw_skills.split(",") if s.strip()],
                    "suggestedSkills": [s.strip() for s in raw_sugg_skills.split(",") if s.strip()],
                    "ageLimit": job.get("Age"),
                    "gender": job.get("Gender"),
                },
                "description": clean_html(raw_desc),
                "aiPersonaMatching": {
                    "bestPersonaTrack": match_intel["bestTrack"],
                    "matchScore": match_intel["matchScore"],
                    "matchedKeywords": match_intel["matchedKeywords"],
                    "featuredProjects": match_intel["featuredProjects"],
                    "cvTailoringAdvice": match_intel["recommendedCvFocus"],
                },
                "url": f"https://bdjobs.com/h/details/{job_id}?ln=1",
            }
        except Exception as e:
            logger.error(f"Error fetching job dossier for {job_id}: {e}")
            return None

# ==============================================================================
# FastAPI Application
# ==============================================================================
app = FastAPI(
    title="BDJobs Enterprise Research Engine API",
    description="Dedicated microservice for deep job research, recruiter contact extraction, and persona matching for Hamim Ahmed (Sayed Johon).",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = BDJobsClient()

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "cookiesLoaded": len(client.cookies) > 0,
        "service": "BDJobs Enterprise Engine v2.0",
        "host": "joe@100.86.193.4",
        "targetUser": "Sayed Johon (hello.sayedjohon@gmail.com)",
        "capabilities": ["deep_contact_extraction", "recency_ranking", "4_track_persona_scoring"]
    }

@app.get("/categories")
def get_categories():
    return {
        "aliases": CATEGORY_MAP,
        "personaProfiles": {k: v["keywords"] for k, v in PERSONA_PROFILES.items()}
    }

@app.get("/search")
def search(
    q: Optional[str] = Query(None, description="Keywords / role"),
    category: Optional[str] = Query(None, description="Category code or alias (e.g. it, media, marketing)"),
    location: Optional[str] = Query(None, description="City / Region filter"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    jobage: Optional[int] = Query(None, description="Posted within N days (e.g. 1 for last 24h)"),
    sort: str = Query("latest", description="Sort by 'latest', 'match', or 'deadline'"),
):
    results = client.search_jobs(
        keyword=q or "",
        category=category,
        location=location or "",
        page=page,
        limit=limit,
        jobage=jobage,
        sort_by=sort,
    )
    return {
        "count": len(results),
        "page": page,
        "limit": limit,
        "sortBy": sort,
        "results": results,
    }

@app.get("/detail/{job_id}")
def detail(job_id: str):
    dossier = client.get_job_dossier(job_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return dossier

# ==============================================================================
# CLI Entrypoint
# ==============================================================================
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        port = int(os.environ.get("PORT", 19828))
        print(f"🚀 Starting BDJobs Enterprise Engine on http://0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        return

    import argparse
    parser = argparse.ArgumentParser(description="BDJobs Enterprise CLI")
    subparsers = parser.add_subparsers(dest="command")

    # search
    s_parser = subparsers.add_parser("search", help="Search job listings with persona matching")
    s_parser.add_argument("-q", "--query", default="", help="Keywords (e.g. python, media, marketing)")
    s_parser.add_argument("-c", "--category", default=None, help="Category name/alias (it, media, marketing, etc.)")
    s_parser.add_argument("-l", "--location", default="", help="Location (e.g. Dhaka, Chittagong, Remote)")
    s_parser.add_argument("-n", "--limit", type=int, default=10, help="Number of results")
    s_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    s_parser.add_argument("--jobage", type=int, default=None, help="Posted within N days")
    s_parser.add_argument("--sort", choices=["latest", "match", "deadline"], default="latest")
    s_parser.add_argument("--format", choices=["json", "table", "plain"], default="json")

    # detail / research
    d_parser = subparsers.add_parser("detail", help="Get full 360 research dossier & contact info")
    d_parser.add_argument("id", help="Job ID")
    d_parser.add_argument("--format", choices=["json", "plain"], default="json")

    args = parser.parse_args()

    if args.command == "search":
        cli_client = BDJobsClient()
        res = cli_client.search_jobs(
            keyword=args.query,
            category=args.category,
            location=args.location,
            page=args.page,
            limit=args.limit,
            jobage=args.jobage,
            sort_by=args.sort,
        )
        if args.format == "json":
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.format == "table":
            print(f"{'ID':<10} | {'TITLE':<32} | {'COMPANY':<22} | {'MATCH':<6} | {'DEADLINE':<11} | {'SALARY'}")
            print("-" * 115)
            for j in res:
                sal = j.get('salary') or '--'
                print(f"{j['id']:<10} | {j['title'][:30]:<32} | {j['company'][:20]:<22} | {str(j['matchScore'])+'%':<6} | {j['deadline']:<11} | {sal}")
        else:
            for j in res:
                print(f"\n[{j['id']}] {j['title']} @ {j['company']} (Match: {j['matchScore']}%)")
                print(f"  📍 Location: {j['location']} | 💰 Salary: {j['salary']}")
                print(f"  ⏰ Deadline: {j['deadline']} | 🎯 Track: {j['personaTrack']}")
                print(f"  ⭐ Match Highlight: {j['featuredProject']}")
                print(f"  🔗 {j['url']}")

    elif args.command == "detail":
        cli_client = BDJobsClient()
        dossier = cli_client.get_job_dossier(args.id)
        if not dossier:
            print(json.dumps({"error": f"Job {args.id} not found", "code": "NOT_FOUND"}))
            sys.exit(1)
        if args.format == "json":
            print(json.dumps(dossier, indent=2, ensure_ascii=False))
        else:
            print(f"\n=======================================================")
            print(f"📌 {dossier['title']} — {dossier['company']}")
            print(f"=======================================================")
            print(f"🏢 Location: {dossier['location']} ({dossier['workplace']})")
            print(f"💰 Salary: {dossier['compensation']['salaryRange']} | 🎯 Persona: {dossier['aiPersonaMatching']['bestPersonaTrack']} ({dossier['aiPersonaMatching']['matchScore']}%)")
            print(f"⏰ Deadline: {dossier['deadline']} | Published: {dossier['postedOn']}")
            print(f"👥 Vacancies: {dossier['vacancies']} | Nature: {dossier['jobNature']}")
            if dossier.get('companyWebsite'):
                print(f"🌐 Company Web: {dossier['companyWebsite']}")
            if dossier['companyAddress']:
                print(f"📍 Address: {dossier['companyAddress']}")
            
            print(f"\n--- 📬 APPLICATION & DIRECT CONTACTS ---")
            print(f"• Application Method: {dossier['contacts']['applicationMethod'].upper()}")
            if dossier['contacts']['allEmails']:
                print(f"• Recruiter Email(s): {', '.join(dossier['contacts']['allEmails'])}")
            if dossier['contacts']['phoneNumbers']:
                print(f"• Phone / Mobile: {', '.join(dossier['contacts']['phoneNumbers'])}")
            if dossier['contacts']['applicationInstructions']:
                print(f"• Instructions: {dossier['contacts']['applicationInstructions']}")

            print(f"\n--- 🎯 AI TAILORING RECOMMENDATION ---")
            print(f"• Featured Projects: {', '.join(dossier['aiPersonaMatching']['featuredProjects'])}")
            print(f"• Advice: {dossier['aiPersonaMatching']['cvTailoringAdvice']}")

            print(f"\n--- 📝 JOB DESCRIPTION ---")
            print(dossier['description'])
            print(f"\n--- 🎓 REQUIREMENTS & EXPERIENCE ---")
            print(dossier['requirements']['education'])
            print(dossier['requirements']['experience'])
            if dossier['requirements']['hardSkills']:
                print(f"\n--- 🛠️ REQUIRED SKILLS ---")
                print(", ".join(dossier['requirements']['hardSkills']))
            if dossier['compensation']['benefits']:
                print(f"\n--- 🎁 BENEFITS ---")
                print(dossier['compensation']['benefits'])
            print(f"\n🔗 Apply URL: {dossier['url']}\n")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
