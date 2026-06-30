import csv
import json
import os
import re
from pypdf import PdfReader
from transformer.normalize import SKILL_MAP

def get_filename_source(filepath):
    return os.path.basename(filepath)

def extract_text_from_file(filepath):
    """
    Extracts raw text from either a .txt or .pdf file.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    else:
        with open(filepath, mode="r", encoding="utf-8") as f:
            return f.read()

# ==========================================
# REUSABLE HEURISTIC EXTRACTION HELPERS
# ==========================================

def extract_emails(text):
    """
    Extracts all unique emails from unstructured text.
    """
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return sorted(list(set(e.strip().lower() for e in emails)))

def extract_phones(text):
    """
    Extracts all unique phone numbers from unstructured text.
    """
    phones = re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return sorted(list(set(p.strip() for p in phones)))

def extract_links(text):
    """
    Extracts links (GitHub, LinkedIn) from unstructured text.
    """
    links = {}
    github_match = re.search(r"(?:github\.com/)([\w-]+)", text, re.IGNORECASE)
    if github_match:
        links["github"] = f"https://github.com/{github_match.group(1)}"
        
    linkedin_match = re.search(r"(?:linkedin\.com/in/)([\w-]+)", text, re.IGNORECASE)
    if linkedin_match:
        links["linkedin"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
    return links

def extract_name(text):
    """
    Extracts candidate name using multiple structured patterns.
    """
    name_patterns = [
        r"(?:candidate\s+interview\s+notes|notes\s+for|interview\s+notes\s*:?)\s*:?\s*([A-Za-z \t]+)",
        r"(?:spoke\s+with|met\s+with|candidate)\s+([A-Z][a-z]+ [A-Z][a-z]+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = re.sub(r"\s+", " ", match.group(1).strip())
            # Basic sanitization
            if len(name) < 30 and "@" not in name and "/" not in name:
                return name
                
    # Fallback: take first non-empty line
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line) < 30 and "@" not in first_line and "/" not in first_line and "|" not in first_line:
            return first_line
            
    return None

def extract_skills(text, scan_only=False):
    """
    Extracts skills by both searching dedicated sections
    and scanning text for known skills in SKILL_MAP.
    """
    skills = set()
    
    # 1. Dedicated section lookup (only if not scan_only)
    if not scan_only:
        skills_match = re.search(r"(?:skills|technologies)\b:?([\s\S]*?)(?:\n\n|\n[A-Z\s]{4,}|\Z)", text, re.IGNORECASE)
        if skills_match:
            parts = re.split(r",|\n|\|", skills_match.group(1))
            for part in parts:
                p = part.strip()
                # Clean up leading "and " or "or " and trailing punctuation
                p = re.sub(r"^(?:and|or)\s+", "", p, flags=re.IGNORECASE)
                p = p.strip(".,;:!?*")
                # Basic validation
                if p and len(p) < 20 and not re.search(r"(?:experience|education|summary|project)", p, re.IGNORECASE):
                    skills.add(p)
                 
    # 2. Key-phrase scanning matching
    for skill_alias in SKILL_MAP.keys():
        if re.search(r"\b" + re.escape(skill_alias) + r"\b", text, re.IGNORECASE):
            skills.add(SKILL_MAP[skill_alias])
            
    return sorted(list(skills))

def extract_experience(text):
    """
    Extracts experience items from unstructured text.
    """
    experience = []
    
    # Try section match first
    exp_match = re.search(r"(?:experience|work history)\b([\s\S]*?)(?:education|education|\Z)", text, re.IGNORECASE)
    if exp_match:
        exp_text = exp_match.group(1)
    else:
        exp_text = text # Fallback to whole text if no section found
        
    exp_lines = [l.strip() for l in exp_text.split("\n") if l.strip()]
    current_entry = None
    
    for line in exp_lines:
        # Check if line matches a company and title: e.g. "Google - Software Engineer" or "Meta: Tech Lead"
        comp_title = re.match(r"^([A-Za-z0-9\s\.\,&]+)\s*[-:]\s*([A-Za-z0-9\s]+)$", line)
        if comp_title:
            if current_entry:
                experience.append(current_entry)
            current_entry = {
                "company": comp_title.group(1).strip(),
                "title": comp_title.group(2).strip(),
                "start": None,
                "end": None,
                "summary": ""
            }
            continue
            
        # Check if line matches date range: e.g. "2022-03 - Present"
        dates = re.match(r"^(\d{4}[-/]\d{1,2}|[a-zA-Z]+\s+\d{4})\s*(?:-|to)\s*(\d{4}[-/]\d{1,2}|[a-zA-Z]+\s+\d{4}|Present)$", line, re.IGNORECASE)
        if dates and current_entry:
            current_entry["start"] = dates.group(1).strip()
            current_entry["end"] = dates.group(2).strip()
            continue
            
        # Append lines starting with bullet points to summary
        if current_entry and (line.startswith("-") or line.startswith("*")):
            current_entry["summary"] += line.strip() + " "
            
    if current_entry:
        experience.append(current_entry)
        
    # Fallback to single inline pattern (e.g. "works as a Software Engineer at Google")
    if not experience:
        inline_job = re.search(r"works\s+as\s+(?:a\s+)?([A-Za-z\s]+?)\s+at\s+([A-Za-z\s\.,]+?)(?:\.|\n|\Z)", text, re.IGNORECASE)
        if inline_job:
            experience.append({
                "company": inline_job.group(2).strip(),
                "title": inline_job.group(1).strip(),
                "start": None,
                "end": "Present",
                "summary": "Current role extracted from inline text notes"
            })
            
    return experience

def extract_education(text):
    """
    Extracts education items from unstructured text.
    """
    education = []
    edu_match = re.search(r"(?:education)\b([\s\S]*?)(?:skills|\Z)", text, re.IGNORECASE)
    if edu_match:
        edu_text = edu_match.group(1)
        edu_lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
        for line in edu_lines:
            degree_match = re.search(r"(BS|MS|B\.S\.|M\.S\.|Bachelor|Master|PhD)\s+(?:in\s+)?([A-Za-z\s]+)", line, re.IGNORECASE)
            year_match = re.search(r"(\d{4})", line)
            if degree_match or year_match:
                education.append({
                    "institution": line.split(",")[0].strip() if "," in line else line,
                    "degree": degree_match.group(1).strip() if degree_match else None,
                    "field": degree_match.group(2).strip() if degree_match else None,
                    "end_year": int(year_match.group(1)) if year_match else None
                })
    return education

# ==========================================
# PRIMARY PIPELINE PARSERS
# ==========================================

def parse_recruiter_csv(filepath):
    """
    Parses recruiter export CSV rows into a list of standardized candidates.
    """
    candidates = []
    source = get_filename_source(filepath)
    method = "structured_csv_import"
    
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            phone = row.get("phone", "").strip()
            company = row.get("current_company", "").strip()
            title = row.get("title", "").strip()
            
            experience = []
            if company or title:
                experience.append({
                    "company": company if company else None,
                    "title": title if title else None,
                    "start": None,
                    "end": "Present",
                    "summary": "Current job role parsed from recruiter export"
                })
                
            candidates.append({
                "full_name": name if name else None,
                "emails": [email] if email else [],
                "phones": [phone] if phone else [],
                "location": None,
                "links": {},
                "headline": title if title else None,
                "years_experience": None,
                "skills": [],
                "experience": experience,
                "education": [],
                "source": source,
                "method": method
            })
            
    return candidates

def parse_ats_json(filepath):
    """
    Parses semi-structured ATS JSON lists into standardized candidates.
    """
    candidates = []
    source = get_filename_source(filepath)
    method = "semi_structured_ats_import"
    
    with open(filepath, mode="r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            data = [data]
            
        for blob in data:
            name = blob.get("fullName", "").strip()
            email = blob.get("emailAddress", "").strip()
            phone = blob.get("telephone", "").strip()
            
            city = blob.get("city_location", "").strip()
            region = blob.get("state_location", "").strip()
            country = blob.get("country_name", "").strip()
            
            location = {}
            if city: location["city"] = city
            if region: location["region"] = region
            if country: location["country"] = country
            if not location: location = None
            
            raw_skills = blob.get("skills_list", [])
            skills = [s.strip() for s in raw_skills if s.strip()]
            
            raw_work = blob.get("work_history", [])
            experience = []
            for item in raw_work:
                experience.append({
                    "company": item.get("employer"),
                    "title": item.get("role_title"),
                    "start": item.get("started"),
                    "end": item.get("ended") or "Present",
                    "summary": item.get("notes")
                })
                
            candidates.append({
                "full_name": name if name else None,
                "emails": [email] if email else [],
                "phones": [phone] if phone else [],
                "location": location,
                "links": {},
                "headline": experience[0]["title"] if experience else None,
                "years_experience": None,
                "skills": skills,
                "experience": experience,
                "education": [],
                "source": source,
                "method": method
            })
            
    return candidates

def parse_recruiter_notes(filepath):
    """
    Parses recruiter notes (.txt) using reusable helper functions.
    Supports multiple candidate blocks separated by '---'.
    """
    raw_text = extract_text_from_file(filepath)
    source = get_filename_source(filepath)
    
    # Split by horizontal rule separator
    blocks = re.split(r"-{3,}", raw_text)
    candidates = []
    
    for block in blocks:
        text = block.strip()
        if not text:
            continue
            
        years = None
        years_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:years|yrs)\s+(?:of\s+)?(?:experience|exp)", text, re.IGNORECASE)
        if years_match:
            try:
                years = float(years_match.group(1))
            except ValueError:
                pass
                
        experience = extract_experience(text)
        headline = experience[0]["title"] if experience else None
        name = extract_name(text)
        emails = extract_emails(text)
        phones = extract_phones(text)
        
        if name or emails or phones:
            candidates.append({
                "full_name": name,
                "emails": emails,
                "phones": phones,
                "location": None,
                "links": {},
                "headline": headline,
                "years_experience": years,
                "skills": extract_skills(text, scan_only=True),
                "experience": experience,
                "education": [],
                "source": source,
                "method": "unstructured_notes_regex"
            })
            
    return candidates

def parse_resume(filepath):
    """
    Parses resumes (.txt or .pdf) using reusable helper functions.
    """
    text = extract_text_from_file(filepath)
    source = get_filename_source(filepath)
    
    experience = extract_experience(text)
    headline = experience[0]["title"] if experience else None
    
    return [{
        "full_name": extract_name(text),
        "emails": extract_emails(text),
        "phones": extract_phones(text),
        "location": None,
        "links": extract_links(text),
        "headline": headline,
        "years_experience": None,
        "skills": extract_skills(text, scan_only=False),
        "experience": experience,
        "education": extract_education(text),
        "source": source,
        "method": "unstructured_resume_heuristic"
    }]
