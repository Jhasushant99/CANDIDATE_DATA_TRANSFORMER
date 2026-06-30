import pytest
from transformer.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill
from transformer.merge import merge_candidate_group
from transformer.project import project_candidate, evaluate_path

def test_normalization():
    # Phone normalization
    assert normalize_phone("+1 (555) 019-9234") == "+15550199234"
    assert normalize_phone("5550199234") == "+15550199234"
    assert normalize_phone("+44 7911 123456") == "+447911123456"
    assert normalize_phone(None) is None
    
    # Date normalization
    assert normalize_date("2022-03-01") == "2022-03"
    assert normalize_date("Jan 2020") == "2020-01"
    assert normalize_date("January 2020") == "2020-01"
    assert normalize_date("02/2025") == "2025-02"
    assert normalize_date("Present") == "Present"
    assert normalize_date(None) is None
    
    # Country normalization
    assert normalize_country("United States") == "US"
    assert normalize_country("usa") == "US"
    assert normalize_country("United Kingdom") == "GB"
    assert normalize_country(None) is None
    
    # Skill normalization
    assert normalize_skill("reactjs") == "React"
    assert normalize_skill("react.js") == "React"
    assert normalize_skill("k8s") == "Kubernetes"
    assert normalize_skill("Python") == "Python"
    assert normalize_skill(None) is None

def test_merging():
    raw_csv = {
        "full_name": "John Doe",
        "emails": ["john.doe@gmail.com"],
        "phones": ["+1 555-019-9234"],
        "location": None,
        "links": {},
        "headline": "Software Engineer",
        "years_experience": None,
        "skills": [],
        "experience": [
            {
                "company": "Google",
                "title": "Software Engineer",
                "start": None,
                "end": "Present",
                "summary": "Current job role parsed from recruiter export"
            }
        ],
        "education": [],
        "source": "recruiter_export.csv",
        "method": "structured_csv_import"
    }
    
    raw_ats = {
        "full_name": "john d.",
        "emails": ["john.doe@gmail.com"],
        "phones": ["5550199234"],
        "location": {
            "city": "San Francisco",
            "country": "United States"
        },
        "links": {},
        "headline": "Software Engineer II",
        "years_experience": None,
        "skills": ["Python", "Java"],
        "experience": [
            {
                "company": "Google",
                "title": "Software Engineer II",
                "start": "2022-03-01",
                "end": "",
                "summary": "Worked on Google Search infrastructure."
            }
        ],
        "education": [],
        "source": "ats_blob.json",
        "method": "semi_structured_ats_import"
    }
    
    # ATS is more trusted (1.0) than CSV (0.9)
    # The merged candidate should prioritize raw_ats values for full_name, location, experience details
    merged = merge_candidate_group([raw_csv, raw_ats])
    
    assert merged["full_name"] == "john d."
    assert merged["emails"] == ["john.doe@gmail.com"]
    assert merged["phones"] == ["+15550199234"]
    assert merged["location"] == {"city": "San Francisco", "region": None, "country": "US"}
    assert len(merged["skills"]) == 2
    assert merged["skills"][0]["name"] == "Java"
    assert merged["skills"][1]["name"] == "Python"
    assert len(merged["experience"]) == 1
    assert merged["experience"][0]["title"] == "Software Engineer II"
    assert merged["experience"][0]["start"] == "2022-03"
    assert merged["overall_confidence"] > 0.8

def test_projection():
    profile = {
        "candidate_id": "test-uuid",
        "full_name": "John Doe",
        "emails": ["john.doe@gmail.com", "john.doe+work@gmail.com"],
        "phones": ["+15550199234"],
        "location": {"city": "San Francisco", "region": "CA", "country": "US"},
        "links": {"github": "https://github.com/johndoe"},
        "headline": "Software Engineer",
        "years_experience": 5.0,
        "skills": [
            {"name": "Python", "confidence": 1.0, "sources": ["ats_blob.json"]},
            {"name": "React", "confidence": 0.8, "sources": ["resume.txt"]}
        ],
        "experience": [],
        "education": [],
        "provenance": [],
        "overall_confidence": 0.95
    }
    
    config = {
        "fields": [
            { "path": "full_name", "type": "string", "required": True },
            { "path": "primary_email", "from": "emails[0]", "type": "string", "required": True },
            { "path": "phone", "from": "phones[0]", "type": "string", "required": True, "normalize": "E164" },
            { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical" }
        ],
        "include_confidence": True,
        "on_missing": "null"
    }
    
    projected = project_candidate(profile, config)
    
    assert projected["full_name"] == "John Doe"
    assert projected["primary_email"] == "john.doe@gmail.com"
    assert projected["phone"] == "+15550199234"
    assert projected["skills"] == ["Python", "React"]
    assert "emails" not in projected
    assert "location" not in projected
    assert projected["overall_confidence"] == 0.95
