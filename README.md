# Multi-Source Candidate Data Transformer

A Python pipeline that ingests candidate profiles from multiple structured (CSV, JSON) and unstructured (txt, pdf) sources, deduplicates and merges them using trust-score conflict resolution, normalizes key fields, and reshapes the final profile using a runtime configurable projection engine.

This repository represents the coding portion (Step 2) of the Eightfold Engineering Intern Assignment.


## 🛠️ Project Structure
- `transformer/`
  - `parse.py`: Reusable, modular extraction helpers (regex, pattern matching, `pypdf` extraction).
  - `normalize.py`: Data normalizers for E.164 phones, YYYY-MM dates, ISO-3166 countries, and skills.
  - `merge.py`: Groups duplicate profiles (via email/phone/name) and resolves conflicts using source trust.
  - `project.py`: Applies configurable projection rules (field selection, remapping, missing-value strategies).
  - `cli.py`: CLI tool entrypoint.
- `tests/`
  - `test_pipeline.py`: Automated unit tests for normalizations, merge rules, and projection configs.
- `mock_data/`: Sample inputs, custom config, and output logs.
- `requirements.txt`: Project dependencies (`reportlab`, `pypdf`, `pytest`).
- `run_on_csv.sh`: Executable helper script to run the transformer on any custom CSV file.


---

## 🚀 Getting Started

### 1. Requirements
Ensure you have **Python 3.11** installed.

### 2. Environment Setup
Create a virtual environment and install the required dependencies:
```bash
# Navigate to project folder
cd /path/to/candidate_data_transformer

# Initialize virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🏃 Running the Code

### 1. Run Automated Unit Tests
Verify all parsing, merging, and projection rules:
```bash
PYTHONPATH=. pytest tests/
```

### 2. Run the Ingestion Pipeline (Configured Mode)
Processes all mock candidates (structured & unstructured) and projects the results using a custom config:
```bash
PYTHONPATH=. python3 transformer/cli.py --config mock_data/custom_config.json
```
- **Inputs**: Defined under `"inputs"` inside `mock_data/custom_config.json`
- **Output saved to**: `mock_data/output_projected.json`

### 3. Run on a Custom CSV file
Easily test any custom CSV export with the helper script:
```bash
./run_on_csv.sh mock_data/recruiter_export.csv
```
- **Output saved to**: `output.json` (canonical schema format)

---

## 🧠 Core Design & Assumptions

### 1. Trust Hierarchy (Conflict Resolution)
When candidate attributes (names, locations, job titles) conflict across sources, the transformer resolves the conflict using a trust hierarchy:
$$\text{ATS JSON (1.0)} > \text{Recruiter CSV (0.9)} > \text{Resume (0.8)} > \text{Recruiter Notes (0.6)}$$

### 2. Matching Logic
Candidates are linked and grouped if they share at least one normalized email, normalized phone, or similar tokenized name tokens (fallback).

### 3. Overall Confidence Score
The candidate completeness and trust score is calculated as:
$$\text{Confidence Score} = (\text{Primary Source Trust} \times 0.5) + (\text{Profile Completeness} \times 0.3) + (\text{Multi-Source Agreement Bonus} \times 0.2)$$
