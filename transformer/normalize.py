import re
from datetime import datetime

# Common country name mapping to ISO-3166 alpha-2
COUNTRY_MAP = {
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "u.s.a.": "US",
    "u.s.": "US",
    "us": "US",
    "united kingdom": "GB",
    "great britain": "GB",
    "uk": "GB",
    "u.k.": "GB",
    "gb": "GB",
    "canada": "CA",
    "ca": "CA",
    "india": "IN",
    "ind": "IN",
    "in": "IN",
    "germany": "DE",
    "deutschland": "DE",
    "de": "DE",
    "france": "FR",
    "fr": "FR",
    "australia": "AU",
    "aus": "AU",
    "au": "AU",
}

# Skill canonicalization mapping
SKILL_MAP = {
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "type script": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "angular.js": "Angular",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "container": "Docker",
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "go": "Go",
    "golang": "Go",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
}

# Month names mapping
MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

def normalize_phone(phone_str, default_country_code="+1"):
    """
    Normalize phone numbers into E.164 format.
    E.g. '+1 (555) 019-9234' -> '+15550199234'
         '5550199234' -> '+15550199234'
         '+44 7911 123456' -> '+447911123456'
    """
    if not phone_str:
        return None
    
    # Strip everything except digits and leading +
    cleaned = re.sub(r"[^\d+]", "", phone_str)
    
    if not cleaned:
        return None
        
    if cleaned.startswith("+"):
        return cleaned
    
    # If no leading +, we check length.
    # If it's a 10-digit number, prepend default_country_code
    if len(cleaned) == 10:
        return f"{default_country_code}{cleaned}"
    elif len(cleaned) > 10:
        # Try to prepend '+' if the number has a valid country code length
        return f"+{cleaned}"
        
    return cleaned  # Fallback

def normalize_date(date_str):
    """
    Normalize dates into YYYY-MM format.
    E.g. '2022-03-01' -> '2022-03'
         'Jan 2020' -> '2020-01'
         'January 2020' -> '2020-01'
         '2020/01/15' -> '2020-01'
         'Present' -> 'Present' (returns 'Present' as string)
    """
    if not date_str:
        return None
        
    normalized = date_str.strip()
    if normalized.lower() in ["present", "current", "now"]:
        return "Present"
        
    # Attempt to parse YYYY-MM-DD or YYYY-MM
    match_iso = re.match(r"^(\d{4})[-/](\d{1,2})(?:[-/]\d{1,2})?$", normalized)
    if match_iso:
        year = int(match_iso.group(1))
        month = int(match_iso.group(2))
        return f"{year:04d}-{month:02d}"
        
    # Attempt to parse Mon YYYY or Month YYYY
    match_text = re.search(r"([a-zA-Z]+)\s*(\d{4})", normalized)
    if match_text:
        mon_str = match_text.group(1).lower()
        year_str = match_text.group(2)
        if mon_str in MONTHS:
            month = MONTHS[mon_str]
            return f"{year_str}-{month:02d}"
            
    # Attempt to parse MM/YYYY
    match_slash = re.match(r"^(\d{1,2})/(\d{4})$", normalized)
    if match_slash:
        month = int(match_slash.group(1))
        year = int(match_slash.group(2))
        return f"{year:04d}-{month:02d}"

    # Fallback to YYYY if only 4 digits found
    match_year = re.match(r"^(\d{4})$", normalized)
    if match_year:
        return f"{normalized}-01" # Default to January

    return None

def normalize_country(country_name):
    """
    Normalize country names to ISO-3166 alpha-2 format.
    E.g. 'United States' -> 'US'
         'United Kingdom' -> 'GB'
    """
    if not country_name:
        return None
        
    cleaned = country_name.strip().lower()
    return COUNTRY_MAP.get(cleaned, country_name.upper()[:2])

def normalize_skill(skill_name):
    """
    Canonicalize skill names.
    E.g. 'React.js' -> 'React'
         'k8s' -> 'Kubernetes'
    """
    if not skill_name:
        return None
        
    cleaned = skill_name.strip().lower()
    return SKILL_MAP.get(cleaned, skill_name.strip())
