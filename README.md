# CORPORATE-HIERARCHY
# Corporate Governance & Structure Analysis Platform

Automatically extract and analyze corporate structure, governance, and ownership information from SEC filings (10‑K and DEF 14A) in seconds, instead of hours.

> Upload a 10‑K and proxy statement, get subsidiaries, board members, shareholders, and governance risk metrics in under 5 seconds.

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Architecture](#architecture)  
- [Tech Stack](#tech-stack)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation](#installation)  
  - [Running Locally](#running-locally)  
- [How It Works](#how-it-works)  
- [Example Workflow](#example-workflow)  
- [Evaluation & Metrics](#evaluation--metrics)  
- [Business Value](#business-value)  
- [RICE Score (Prioritization)](#rice-score-prioritization)  
- [Roadmap](#roadmap)  
- [Limitations](#limitations)  
- [Contributing](#contributing)  
- [License](#license)

---

## Overview

This project is a full‑stack prototype for **automated corporate governance and structure analysis** from SEC filings (10‑K and DEF 14A).

It focuses on three key questions:

1. How complex is this company’s corporate structure?  
2. How strong is its governance setup (board, roles, ownership)?  
3. What is the governance/structure risk profile for different investor types?

The system ingests PDFs of 10‑K and DEF 14A filings, extracts structured entities (subsidiaries, directors, beneficial owners), computes metrics, and exposes the result via a web UI and JSON API.

---

## Features

- **PDF ingestion**
  - Upload 10‑K and DEF 14A as PDFs via a web UI
  - Text extraction from multi‑page filings

- **Entity extraction**
  - Subsidiaries (from Exhibit 21 / similar sections)
  - Board members and executives (from proxy statement sections)
  - Major beneficial owners with approximate ownership percentages

- **Metric computation**
  - **Complexity score** (subsidiary count, jurisdictions, offshore share, depth)
  - **Governance score** (board size, independence, role separation, concentration)
  - **Overall risk level** (e.g., Green / Yellow / Red) for governance & structure

- **Investor‑type recommendations**
  - Heuristic views for:
    - Value investors  
    - Growth investors  
    - Conservative investors  
    - Activist / special situations

- **Interactive visualization**
  - Graph‑style view of parent–subsidiary relationships
  - Color coding by region / jurisdiction

- **Export options**
  - JSON response for downstream analytics
  - PDF/HTML summary report for investment memos

- **Web app UX**
  - Simple two‑file upload form (10‑K + DEF 14A)
  - Results page with tables, metrics, and visualization
  - Designed to support a 5–10 minute live demo

---

## Architecture

High‑level architecture:

- **Frontend**
  - Minimal HTML/CSS/JS web app
  - Upload form for filings
  - Results view with tables, metrics, and graphs

- **Backend (API)**
  - Python Flask app exposing:
    - `GET /` – index page  
    - `POST /upload` – handle file uploads and return JSON
  - Orchestrates:
    1. PDF → text extraction  
    2. Section extraction (subsidiaries, directors, owners)  
    3. Entity parsing (regex / rule‑based)  
    4. Metric computation  
    5. Response serialization (JSON + HTML)

- **Core logic**
  - Text parsing utilities for 10‑K / DEF 14A
  - Pattern‑based entity extraction
  - Metric computation module
  - Simple rule‑based recommendation engine

Conceptually: **Browser → Flask API → PDF extraction → parsing & metrics → JSON + HTML UI**.

---

## Tech Stack

- **Language:** Python 3.x  
- **Backend:** Flask  
- **PDF extraction:** `pdfplumber` (or similar)  
- **Data:** Python dicts/lists, JSON  
- **Visualization (optional):** D3.js / Vis.js / other JS graph library  
- **Environment:** `venv` or `conda`, `pip` for dependencies  
- **(Optional)** Docker for containerized deployment  

---

## Getting Started

### Prerequisites

- Python 3.9+  
- `pip`  
- Git  

Optional:

- Node/npm (if you use a JS visualization library)  
- Docker (if you containerize)

### Installation

Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

Install dependencies
pip install -r requirements.txt


---

## How It Works

1. **Upload filings**
   - User uploads:
     - DEF 14A (proxy statement, directors and owners)
     - 10‑K (annual report, subsidiaries in Exhibit 21)

2. **PDF → text**
   - Use `pdfplumber` (or similar) to extract text page by page.
   - Concatenate into raw text blobs for each document.

3. **Section extraction**
   - From 10‑K:
     - Locate “EXHIBIT 21” or “Subsidiaries of the Registrant”.
   - From DEF 14A:
     - Locate “DIRECTORS AND EXECUTIVE OFFICERS”.
     - Locate “SECURITY OWNERSHIP OF CERTAIN BENEFICIAL OWNERS” (or similar).

4. **Entity parsing**
   - **Subsidiaries:**
     - Parse lines like `Name – Jurisdiction` into `{name, jurisdiction}`.
   - **Directors:**
     - Parse `Name, Title` lines; filter by role keywords (CEO, CFO, Director, etc.).
   - **Beneficial owners:**
     - Regex for `Name ... XX.X%` to get `{name, percent}`.

5. **Metric computation**
   - **Complexity score** example factors:
     - Number of subsidiaries
     - Number of distinct jurisdictions
     - Share of offshore / tax‑haven jurisdictions
   - **Governance score** example factors:
     - Board size vs recommended range
     - CEO/Chair duality vs separation
     - Approximate independence ratio (if derivable)
     - Ownership concentration among top holders
   - **Risk level:**
     - Map combined complexity + governance into Green / Yellow / Red.

6. **Recommendations**
   - Simple heuristic rules per investor type:
     - Value vs growth vs conservative vs activist.

7. **Output**
   - Render:
     - Tables for subsidiaries, directors, major owners
     - Metric summary and risk label
     - Optional interactive graph of structure
   - Provide:
     - JSON endpoint for programmatic consumption
     - PDF/HTML report export

---

## Example Workflow

1. Open the app in your browser (`/`).  
2. Upload:
   - `apple_10k.pdf`
   - `apple_def14a.pdf`  
3. Click **Analyze**.  
4. Wait a few seconds for processing.  
5. Inspect results:
   - Subsidiary list (e.g. ~137 entities across multiple regions)
   - Board and key executives
   - Major institutional owners and their approximate stakes
   - Complexity and governance scores + overall risk label
   - Recommendations for different investor profiles  
6. Export:
   - JSON for further analysis
   - PDF summary for investment memos / IC decks

---

## Evaluation & Metrics

Update these numbers to reflect your real test results.

### Extraction quality (example)

- Subsidiaries: ~90% of known subsidiaries captured on a labeled test set  
- Directors: ~94% of board members correctly identified  
- Beneficial owners: ~97% of major owners (≥5%) captured with approximate %  

### System performance (example)

- End‑to‑end analysis time: ~5 seconds per filing pair on a typical laptop  
- Valid output (no parsing failure) on ~90%+ of clean, text‑based SEC PDFs  

### Time & cost savings (example)

- Manual governance/structure review: ~35 minutes per company  
- Platform: < 5 seconds (+ a brief human review)  
- For 100 companies/year: ~52 analyst hours saved  
- For institutions with high analyst hourly cost, this can translate into significant annual savings.

---

## Business Value

- **Institutional investors**
  - Reduce time spent on governance/structure due‑diligence.
  - Standardize governance risk views across coverage universe.

- **Individual investors / advisors**
  - Quickly understand complex issuers.
  - Get a structured view of who owns what and how the board is set up.

- **PE / special situations**
  - Rapid pre‑screening of complex or governance‑fragile names.
  - Support for idea generation and risk flagging.

---

## RICE Score (Prioritization)

Using a simple RICE framework:

- **Reach:** ~260 users/quarter in early beta (analysts + retail + PE/HF pilots)  
- **Impact:** 3 (massive) – high time and cost savings per user  
- **Confidence:** 0.8 – working prototype plus pilot metrics  
- **Effort:** 3 person‑months to polish and launch

RICE score:

RICE = (Reach × Impact × Confidence) / Effort
= (260 × 3 × 0.8) / 3 ≈ 208


This indicates a **high‑priority, high‑ROI project** relative to effort.

---

## Roadmap

Planned / potential enhancements:

- More robust parsing for:
  - Scanned/image‑based PDFs  
  - Non‑US or non‑standard filings  
- ML/NLP‑based section and entity detection (beyond regex)  
- Richer governance metrics:
  - Director tenure & overboarding  
  - Committee structures (audit, comp, etc.)  
- Time‑series tracking of structure and governance changes  
- Alerting and watchlists (e.g., governance deterioration)  
- Multi‑tenant SaaS deployment and RBAC  
- CI/CD pipeline and test suite

---

## Limitations

- Optimized for **US SEC filings** (10‑K + DEF 14A).  
- Works best on text‑based PDFs; performance degrades on scanned documents.  
- Governance and risk scores are heuristic and for research support only.  
- This project does **not** provide financial or investment advice.

> Disclaimer: This tool is for research and educational purposes only and does not constitute financial, legal, or investment advice.

---
