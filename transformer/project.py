import re
from transformer.normalize import normalize_phone, normalize_skill

def evaluate_path(profile, path_str):
    """
    Evaluates a path expression on a profile dict.
    Supports:
      - 'full_name'
      - 'location.city'
      - 'emails[0]'
      - 'skills[].name'
    """
    if not path_str:
        return None
        
    parts = path_str.split(".")
    current = profile
    
    for i, part in enumerate(parts):
        if current is None:
            return None
            
        # Check if part has an array syntax, e.g. 'emails[0]' or 'skills[]'
        array_match = re.match(r"^(\w+)(?:\[(\d*)\])$", part)
        if array_match:
            key = array_match.group(1)
            idx_str = array_match.group(2)
            
            # Retrieve list
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
                
            if not isinstance(current, list):
                return None
                
            if idx_str == "":  # 'skills[]' - map remaining path over elements
                # If there are remaining path parts, map them
                remaining_path = ".".join(parts[i+1:])
                if remaining_path:
                    # Evaluate on each element in the list
                    return [evaluate_path(item, remaining_path) for item in current]
                else:
                    return current
            else:  # Specific index, e.g. 'emails[0]'
                idx = int(idx_str)
                if idx < len(current):
                    current = current[idx]
                else:
                    return None
        else:
            # Simple dict key
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
                
    return current

def project_candidate(profile, config):
    """
    Projects a canonical candidate profile according to a configuration dictionary.
    """
    projected = {}
    
    # Global options
    include_confidence = config.get("include_confidence", True)
    include_provenance = config.get("include_provenance", False) # Default to false unless toggled on
    on_missing = config.get("on_missing", "null")  # "null", "omit", "error"
    
    fields_config = config.get("fields", [])
    
    # If no fields are specified in config, output the default schema
    if not fields_config:
        # Default projection
        projected = {
            "candidate_id": profile["candidate_id"],
            "full_name": profile["full_name"],
            "emails": profile["emails"],
            "phones": profile["phones"],
            "location": profile["location"],
            "links": profile["links"],
            "headline": profile["headline"],
            "years_experience": profile["years_experience"],
            "skills": profile["skills"],
            "experience": profile["experience"],
            "education": profile["education"]
        }
        
        if include_confidence:
            projected["overall_confidence"] = profile["overall_confidence"]
        else:
            # Strip confidence from skills list
            projected["skills"] = [
                {k: v for k, v in s.items() if k != "confidence"}
                for s in profile["skills"]
            ]
            
        if include_provenance:
            projected["provenance"] = profile["provenance"]
            
        return projected

    # Custom fields mapping
    for field_cfg in fields_config:
        dest_path = field_cfg["path"]
        source_path = field_cfg.get("from", dest_path)
        field_type = field_cfg.get("type", "string")
        required = field_cfg.get("required", False)
        norm_override = field_cfg.get("normalize")
        
        # Evaluate value
        val = evaluate_path(profile, source_path)
        
        # Handle custom normalizations overrides
        if val is not None:
            if norm_override == "E164":
                if isinstance(val, list):
                    val = [normalize_phone(v) for v in val if v]
                else:
                    val = normalize_phone(str(val))
            elif norm_override == "canonical":
                if isinstance(val, list):
                    val = [normalize_skill(v) for v in val if v]
                else:
                    val = normalize_skill(str(val))
                    
        # Check if missing
        is_missing = (val is None) or (isinstance(val, list) and not val) or (isinstance(val, str) and not val.strip())
        
        if is_missing:
            if required:
                if on_missing == "error":
                    raise ValueError(f"Required field '{dest_path}' is missing.")
                elif on_missing == "omit":
                    continue  # Skip adding to output
                else:  # "null"
                    projected[dest_path] = None
            else:
                if on_missing == "omit":
                    continue
                else:
                    projected[dest_path] = None
        else:
            # Cast type if specified
            if field_type == "string" and not isinstance(val, (list, dict)):
                val = str(val)
            elif field_type == "string[]" and isinstance(val, list):
                val = [str(v) for v in val]
                
            projected[dest_path] = val

    # Include global sections if configured
    if include_confidence and "overall_confidence" not in projected:
        projected["overall_confidence"] = profile["overall_confidence"]
        
    if include_provenance and "provenance" not in projected:
        projected["provenance"] = profile["provenance"]
        
    return projected
