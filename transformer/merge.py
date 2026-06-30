import uuid
from collections import defaultdict
from transformer.normalize import normalize_phone, normalize_date, normalize_country, normalize_skill

# Source type trust score mapping
TRUST_SCORES = {
    "semi_structured_ats_import": 1.0,
    "structured_csv_import": 0.9,
    "unstructured_resume_heuristic": 0.8,
    "unstructured_notes_regex": 0.6
}

def get_trust_score(method):
    return TRUST_SCORES.get(method, 0.5)

def match_candidates(raw_candidates):
    """
    Groups raw candidate records that represent the same physical person.
    Returns a list of lists of raw candidates.
    """
    # Group by normalized email and phone
    email_to_idx = {}
    phone_to_idx = {}
    name_to_idx = {}
    
    parent = list(range(len(raw_candidates)))
    
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
        
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for idx, cand in enumerate(raw_candidates):
        # Normalize emails/phones for matching
        normalized_emails = [e.strip().lower() for e in cand.get("emails", []) if e.strip()]
        normalized_phones = [normalize_phone(p) for p in cand.get("phones", []) if p.strip()]
        normalized_name = cand.get("full_name", "").strip().lower() if cand.get("full_name") else ""
        
        # Link by email
        for email in normalized_emails:
            if email in email_to_idx:
                union(idx, email_to_idx[email])
            else:
                email_to_idx[email] = idx
                
        # Link by phone
        for phone in normalized_phones:
            if phone in phone_to_idx:
                union(idx, phone_to_idx[phone])
            else:
                phone_to_idx[phone] = idx
                
        # Secondary linking: if candidate has no emails/phones but matching name (e.g. Recruiter Notes name only)
        if not normalized_emails and not normalized_phones and normalized_name:
            if normalized_name in name_to_idx:
                union(idx, name_to_idx[normalized_name])
            else:
                name_to_idx[normalized_name] = idx

    # Group components
    groups = defaultdict(list)
    for idx, cand in enumerate(raw_candidates):
        root = find(idx)
        groups[root].append(cand)
        
    return list(groups.values())

def merge_candidate_group(cand_group):
    """
    Merges a group of raw candidate records representing the same candidate.
    """
    # Sort group by trust score (highest trust first)
    cand_group = sorted(cand_group, key=lambda c: get_trust_score(c["method"]), reverse=True)
    primary = cand_group[0]
    
    emails = set()
    phones = set()
    links = {}
    skills_sources = defaultdict(set)
    skills_max_trust = defaultdict(float)
    experience_list = []
    education_list = []
    
    provenance = []
    
    # 1. Names
    full_name = primary["full_name"]
    provenance.append({
        "field": "full_name",
        "source": primary["source"],
        "method": primary["method"]
    })
    
    # Check for name agreements and differences
    for cand in cand_group[1:]:
        if cand["full_name"] and not full_name:
            full_name = cand["full_name"]
            provenance.append({
                "field": "full_name",
                "source": cand["source"],
                "method": cand["method"]
            })
            
    # 2. Emails and Phones (Union)
    for cand in cand_group:
        for email in cand.get("emails", []):
            if email.strip():
                emails.add(email.strip())
        for phone in cand.get("phones", []):
            norm_p = normalize_phone(phone)
            if norm_p:
                phones.add(norm_p)
                
    # Record provenance for emails and phones
    provenance.append({
        "field": "emails",
        "source": primary["source"],
        "method": f"union_across_{len(cand_group)}_sources"
    })
    provenance.append({
        "field": "phones",
        "source": primary["source"],
        "method": f"union_across_{len(cand_group)}_sources"
    })
    
    # 3. Location (Merge components from highest trust sources)
    location = {
        "city": None,
        "region": None,
        "country": None
    }
    loc_prov = {"city": None, "region": None, "country": None}
    
    for cand in cand_group:
        cand_loc = cand.get("location")
        if cand_loc:
            # Check city
            if not location["city"] and cand_loc.get("city"):
                location["city"] = cand_loc["city"].strip()
                loc_prov["city"] = (cand["source"], cand["method"])
            # Check region
            if not location["region"] and cand_loc.get("region"):
                location["region"] = cand_loc["region"].strip()
                loc_prov["region"] = (cand["source"], cand["method"])
            # Check country
            if not location["country"] and cand_loc.get("country"):
                norm_c = normalize_country(cand_loc["country"])
                if norm_c:
                    location["country"] = norm_c
                    loc_prov["country"] = (cand["source"], cand["method"])
                    
    # Clean location if entirely empty
    if not any(location.values()):
        location = None
    else:
        # Record location provenance
        for k, v in location.items():
            if v and loc_prov[k]:
                provenance.append({
                    "field": f"location.{k}",
                    "source": loc_prov[k][0],
                    "method": loc_prov[k][1]
                })

    # 4. Links
    for cand in cand_group:
        for k, v in cand.get("links", {}).items():
            if k not in links and v:
                links[k] = v
                provenance.append({
                    "field": f"links.{k}",
                    "source": cand["source"],
                    "method": cand["method"]
                })
                
    # 5. Headline
    headline = None
    headline_cand = None
    for cand in cand_group:
        if cand.get("headline"):
            headline = cand["headline"]
            headline_cand = cand
            break
            
    if headline:
        provenance.append({
            "field": "headline",
            "source": headline_cand["source"],
            "method": headline_cand["method"]
        })
        
    # 6. Years Experience
    years_experience = None
    years_cand = None
    for cand in cand_group:
        if cand.get("years_experience") is not None:
            years_experience = cand["years_experience"]
            years_cand = cand
            break
            
    if years_experience is not None:
        provenance.append({
            "field": "years_experience",
            "source": years_cand["source"],
            "method": years_cand["method"]
        })
        
    # 7. Skills (Normalized + Confidence)
    for cand in cand_group:
        trust = get_trust_score(cand["method"])
        for s in cand.get("skills", []):
            norm_s = normalize_skill(s)
            if norm_s:
                skills_sources[norm_s].add(cand["source"])
                skills_max_trust[norm_s] = max(skills_max_trust[norm_s], trust)
                
    skills = []
    for skill_name, src_list in skills_sources.items():
        skills.append({
            "name": skill_name,
            "confidence": round(skills_max_trust[skill_name], 2),
            "sources": sorted(list(src_list))
        })
        
    skills = sorted(skills, key=lambda s: s["name"])
    provenance.append({
        "field": "skills",
        "source": primary["source"],
        "method": "canonicalized_skills_extraction"
    })
    
    # 8. Experience (Merged & Deduplicated)
    # Deduplicate matching company + title within the same year period
    seen_jobs = []
    for cand in cand_group:
        trust = get_trust_score(cand["method"])
        for exp in cand.get("experience", []):
            comp = exp.get("company", "")
            title = exp.get("title", "")
            
            # Skip empty
            if not comp and not title:
                continue
                
            start = normalize_date(exp.get("start"))
            end = normalize_date(exp.get("end"))
            
            # Deduplication check: check if company match and date overlap
            is_dup = False
            for job in seen_jobs:
                comp_match = (comp and job["company"] and comp.lower() in job["company"].lower()) or (job["company"] and comp and job["company"].lower() in comp.lower())
                title_match = (title and job["title"] and title.lower() in job["title"].lower()) or (job["title"] and title and job["title"].lower() in title.lower())
                if comp_match:
                    is_dup = True
                    # Update dates and details if this candidate is more trusted
                    if trust > job["_trust"]:
                        if start: job["start"] = start
                        if end: job["end"] = end
                        if exp.get("summary"): job["summary"] = exp["summary"]
                    break
                    
            if not is_dup:
                seen_jobs.append({
                    "company": comp,
                    "title": title,
                    "start": start,
                    "end": end,
                    "summary": exp.get("summary"),
                    "_trust": trust,
                    "_source": cand["source"]
                })
                
    # Clean temporary keys
    for job in seen_jobs:
        job.pop("_trust")
        job.pop("_source")
        experience_list.append(job)
        
    provenance.append({
        "field": "experience",
        "source": primary["source"],
        "method": "merged_work_history"
    })
    
    # 9. Education (Merged & Deduplicated)
    seen_edu = []
    for cand in cand_group:
        for edu in cand.get("education", []):
            inst = edu.get("institution", "")
            deg = edu.get("degree", "")
            
            is_dup = False
            for item in seen_edu:
                inst_match = inst and item["institution"] and inst.lower() in item["institution"].lower()
                if inst_match:
                    is_dup = True
                    if deg and not item["degree"]:
                        item["degree"] = deg
                        item["field"] = edu.get("field")
                        item["end_year"] = edu.get("end_year")
                    break
            if not is_dup:
                seen_edu.append({
                    "institution": inst,
                    "degree": deg,
                    "field": edu.get("field"),
                    "end_year": edu.get("end_year")
                })
    education_list = seen_edu
    provenance.append({
        "field": "education",
        "source": primary["source"],
        "method": "merged_education_records"
    })
    
    # 10. Generate Candidate ID
    # Use deterministic UUID based on first email, or a random UUID if email not present
    sorted_emails = sorted(list(emails))
    if sorted_emails:
        cand_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, sorted_emails[0]))
    else:
        # Fallback to name-based deterministic UUID
        if full_name:
            cand_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, full_name.lower().replace(" ", "")))
        else:
            cand_id = str(uuid.uuid4())
            
    # 11. Calculate Overall Confidence Score
    # Score between 0.0 and 1.0:
    # - Base: trust of primary source (50%)
    # - Completeness: ratio of fields populated (emails, phones, skills, experience, location) (30%)
    # - Multi-source agreement: if candidate matches in multiple files (+10% per additional source, max 20%)
    base_trust = get_trust_score(primary["method"])
    
    completeness_fields = [
        bool(full_name),
        bool(emails),
        bool(phones),
        len(skills) > 0,
        len(experience_list) > 0,
        bool(location)
    ]
    completeness_score = sum(completeness_fields) / len(completeness_fields)
    
    agreement_bonus = min(0.20, (len(cand_group) - 1) * 0.10)
    
    overall_confidence = (base_trust * 0.5) + (completeness_score * 0.3) + agreement_bonus
    overall_confidence = round(min(1.0, overall_confidence), 2)
    
    return {
        "candidate_id": cand_id,
        "full_name": full_name,
        "emails": sorted_emails,
        "phones": sorted(list(phones)),
        "location": location,
        "links": links,
        "headline": headline,
        "years_experience": years_experience,
        "skills": skills,
        "experience": experience_list,
        "education": education_list,
        "provenance": provenance,
        "overall_confidence": overall_confidence
    }

def merge_all_candidates(raw_candidates_lists):
    """
    Receives lists of candidate dicts from different files,
    flattens they, groups same candidates, and merges each group.
    """
    flat_list = []
    for l in raw_candidates_lists:
        flat_list.extend(l)
        
    groups = match_candidates(flat_list)
    merged_results = []
    for group in groups:
        merged = merge_candidate_group(group)
        merged_results.append(merged)
        
    return merged_results
