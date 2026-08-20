#!/usr/bin/env python3
"""
BDJobs Microservice & Engine for Sayed Johon
Provides high-speed authenticated REST API & CLI for searching and fetching job listings from BDJobs.com.
"""

import os
import re
import sys
import json
import logging
from typing import Optional, List, Dict, Any
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

# Category Aliases mapped to 4 Persona Tracks
CATEGORY_MAP: Dict[str, int] = {
    "it": 8,
    "software": 8,
    "ai": 8,
    "tech": 8,
    "media": 10,
    "video": 10,
    "creative": 18,
    "design": 18,
    "graphics": 71,
    "marketing": 9,
    "sales": 9,
    "digital_marketing": 30,
    "ecommerce": 30,
    "management": 7,
    "admin": 7,
    "consultancy": 13,
    "research": 13,
}

# Persona Track mapping
TRACK_MAP: Dict[str, str] = {
    "8": "Track A (AI Systems & Automation Engineer)",
    "10": "Track B (Media Production & Video Director)",
    "18": "Track B (Media Production & Video Director)",
    "71": "Track B (Media Production & Video Director)",
    "9": "Track C (Growth Marketing & Copywriting)",
    "30": "Track C (Growth Marketing & Copywriting)",
    "7": "Track D (Technical Generalist / Startup Lead)",
    "13": "Track D (Technical Generalist / Startup Lead)",
}

def clean_html(raw_html: Optional[str]) -> str:
    """Converts HTML to clean, readable text/markdown."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Convert lists to markdown bullets
    for li in soup.find_all("li"):
        li.insert_before("\n* ")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n\n")
    text = soup.get_text()
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

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
    ) -> List[Dict[str, Any]]:
        """Searches BDJobs using direct JSON API."""
        fcat_id = ""
        if category:
            cat_lower = str(category).lower().strip()
            if cat_lower in CATEGORY_MAP:
                fcat_id = str(CATEGORY_MAP[cat_lower])
            elif cat_lower.isdigit():
                fcat_id = cat_lower

        params = {
            "Icat": "",
            "industry": "",
            "category": "",
            "org": "",
            "jobNature": "",
            "Fcat": fcat_id,
            "location": location or "",
            "Qot": "",
            "jobType": "",
            "jobLevel": "",
            "postedWithin": str(jobage) if jobage else "",
            "deadline": "",
            "keyword": keyword or "",
            "pg": str(page),
            "qAge": "",
            "Salary": "",
            "experience": "",
            "gender": "",
            "MExp": "",
            "genderB": "",
            "MPostings": "",
            "MCat": "",
            "version": "",
            "rpp": str(min(limit, 50)),
            "Newspaper": "",
            "armyp": "",
            "QDisablePerson": "",
            "pwd": "",
            "workplace": "",
            "facilitiesForPWD": "",
            "SaveFilterList": "",
            "UserFilterName": "",
            "HUserFilterName": "",
            "earlyJobAccess": "",
            "isPro": "0",
            "ToggleJobs": "true",
            "isFresher": "false",
        }

        url = "https://api.bdjobs.com/Jobs/api/JobSearch/GetJobSearch"
        try:
            res = self.session.get(url, params=params, headers=self.get_headers(), timeout=15)
            if res.status_code != 200:
                logger.error(f"Search failed with HTTP {res.status_code}: {res.text[:200]}")
                return []

            data = res.json()
            raw_jobs = data.get("data", []) or []
            results = []

            for r in raw_jobs:
                job_id = str(r.get("Jobid", ""))
                title = r.get("jobTitle", "") or r.get("JobTitleBng", "Untitled")
                company = r.get("companyName", "Unknown Company")
                deadline = r.get("deadline", "")
                deadline_db = r.get("deadlineDB", "")
                pub_date = r.get("publishDate", "")
                salary = r.get("Salary", "") or r.get("JobSalaryRange", "")
                exp = r.get("Exp", "") or r.get("experience", "")
                edu = r.get("MinEdu", "") or r.get("eduRec", "")
                loc = r.get("jobLocation", "") or r.get("Location", "") or "Bangladesh"
                
                # Determine track
                track = TRACK_MAP.get(fcat_id, "Track D (Technical Generalist / Startup Lead)")

                results.append({
                    "id": job_id,
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": loc.strip(),
                    "deadline": deadline,
                    "deadlineDB": deadline_db,
                    "publishDate": pub_date,
                    "salary": salary.strip() if salary else None,
                    "experience": clean_html(exp) if exp else None,
                    "education": clean_html(edu) if edu else None,
                    "url": f"https://bdjobs.com/h/details/{job_id}?ln=1",
                    "personaTrack": track,
                })

            return results
        except Exception as e:
            logger.error(f"Error executing BDJobs search: {e}")
            return []

    def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetches full job description, requirements, skills, and company details."""
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
            cat_id = str(job.get("CategoryID", ""))
            track = TRACK_MAP.get(cat_id, "Track D (Technical Generalist / Startup Lead)")

            return {
                "id": str(job.get("JobId", job_id)),
                "title": job.get("JobTitle", ""),
                "company": job.get("CompnayName", "") or job.get("CompanyNameENG", ""),
                "companyAddress": job.get("CompanyAddress", ""),
                "companyWeb": job.get("CompanyWeb", ""),
                "companyBusiness": clean_html(job.get("CompanyBusiness", "")),
                "location": job.get("JobLocation", "Dhaka, Bangladesh"),
                "postedOn": job.get("PostedOn", ""),
                "deadline": job.get("Deadline", ""),
                "deadlineDB": job.get("DeadlineDB", ""),
                "vacancies": job.get("JobVacancies", ""),
                "jobNature": job.get("JobNature", "Full Time"),
                "workplace": job.get("JobWorkPlace", "Work at office"),
                "salary": job.get("JobSalaryRange", ""),
                "minSalary": job.get("JobSalaryMinSalary", ""),
                "maxSalary": job.get("JobSalaryMaxSalary", ""),
                "otherBenefits": clean_html(job.get("JobOtherBenifits", "")),
                "description": clean_html(job.get("JobDescription", "")),
                "requirements": clean_html(job.get("EducationRequirements", "")) + "\n" + clean_html(job.get("AdditionJobRequirements", "")),
                "experience": clean_html(job.get("experience", "")),
                "skillsRequired": job.get("SkillsRequired", ""),
                "suggestedSkills": job.get("SuggestedSkills", ""),
                "age": job.get("Age", ""),
                "gender": job.get("Gender", ""),
                "personaTrack": track,
                "url": f"https://bdjobs.com/h/details/{job_id}?ln=1",
            }
        except Exception as e:
            logger.error(f"Error fetching job detail for {job_id}: {e}")
            return None

# ==============================================================================
# FastAPI Application
# ==============================================================================
app = FastAPI(
    title="BDJobs Engine API",
    description="Dedicated microservice for searching and extracting BDJobs listings for Hamim Ahmed (Sayed Johon).",
    version="1.0.0",
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
        "service": "BDJobs Scraper API",
        "host": "joe@100.86.193.4",
        "targetUser": "Sayed Johon (hello.sayedjohon@gmail.com)"
    }

@app.get("/categories")
def get_categories():
    return {
        "aliases": CATEGORY_MAP,
        "tracks": TRACK_MAP,
    }

@app.get("/search")
def search(
    q: Optional[str] = Query(None, description="Keywords / role"),
    category: Optional[str] = Query(None, description="Category code or alias (e.g. it, media, marketing)"),
    location: Optional[str] = Query(None, description="City / Region filter"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    jobage: Optional[int] = Query(None, description="Days posted within"),
):
    results = client.search_jobs(
        keyword=q or "",
        category=category,
        location=location or "",
        page=page,
        limit=limit,
        jobage=jobage,
    )
    return {
        "count": len(results),
        "page": page,
        "limit": limit,
        "results": results,
    }

@app.get("/detail/{job_id}")
def detail(job_id: str):
    job = client.get_job_detail(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job

# ==============================================================================
# CLI Entrypoint
# ==============================================================================
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        port = int(os.environ.get("PORT", 19828))
        print(f"🚀 Starting BDJobs Microservice on http://0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        return

    import argparse
    parser = argparse.ArgumentParser(description="BDJobs Engine CLI")
    subparsers = parser.add_subparsers(dest="command")

    # search
    s_parser = subparsers.add_parser("search", help="Search job listings")
    s_parser.add_argument("-q", "--query", default="", help="Keywords (e.g. python, media, marketing)")
    s_parser.add_argument("-c", "--category", default=None, help="Category name/alias (it, media, marketing, etc.)")
    s_parser.add_argument("-l", "--location", default="", help="Location (e.g. Dhaka, Chittagong, Remote)")
    s_parser.add_argument("-n", "--limit", type=int, default=10, help="Number of results")
    s_parser.add_argument("-p", "--page", type=int, default=1, help="Page number")
    s_parser.add_argument("--jobage", type=int, default=None, help="Posted within N days")
    s_parser.add_argument("--format", choices=["json", "table", "plain"], default="json")

    # detail
    d_parser = subparsers.add_parser("detail", help="Get full job details")
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
        )
        if args.format == "json":
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.format == "table":
            print(f"{'ID':<10} | {'TITLE':<35} | {'COMPANY':<25} | {'DEADLINE':<12} | {'SALARY'}")
            print("-" * 110)
            for j in res:
                sal = j.get('salary') or '--'
                print(f"{j['id']:<10} | {j['title'][:33]:<35} | {j['company'][:23]:<25} | {j['deadline']:<12} | {sal}")
        else:
            for j in res:
                print(f"\n[{j['id']}] {j['title']} @ {j['company']}")
                print(f"  📍 Location: {j['location']} | 💰 Salary: {j['salary'] or 'Not disclosed'}")
                print(f"  ⏰ Deadline: {j['deadline']} | 🎯 Track: {j['personaTrack']}")
                print(f"  🔗 {j['url']}")

    elif args.command == "detail":
        cli_client = BDJobsClient()
        job = cli_client.get_job_detail(args.id)
        if not job:
            print(json.dumps({"error": f"Job {args.id} not found", "code": "NOT_FOUND"}))
            sys.exit(1)
        if args.format == "json":
            print(json.dumps(job, indent=2, ensure_ascii=False))
        else:
            print(f"\n=======================================================")
            print(f"📌 {job['title']} — {job['company']}")
            print(f"=======================================================")
            print(f"🏢 Location: {job['location']} ({job['workplace']})")
            print(f"💰 Salary: {job['salary']} | 🎯 Persona: {job['personaTrack']}")
            print(f"⏰ Deadline: {job['deadline']} | Published: {job['postedOn']}")
            print(f"👥 Vacancies: {job['vacancies']} | Nature: {job['jobNature']}")
            if job.get('companyWeb'):
                print(f"🌐 Company Web: {job['companyWeb']}")
            print(f"\n--- 📝 JOB DESCRIPTION ---")
            print(job['description'])
            print(f"\n--- 🎓 REQUIREMENTS & EXPERIENCE ---")
            print(job['requirements'])
            if job.get('skillsRequired'):
                print(f"\n--- 🛠️ REQUIRED SKILLS ---")
                print(job['skillsRequired'])
            if job.get('otherBenefits'):
                print(f"\n--- 🎁 BENEFITS ---")
                print(job['otherBenefits'])
            print(f"\n🔗 Apply URL: {job['url']}\n")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
