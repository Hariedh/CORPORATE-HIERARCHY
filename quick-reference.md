## ⚡ QUICK START REFERENCE CARD

### 🔴 FIX THE JSON ERROR (What You Experienced)

**The Error:**
```
Invalid JSON format. Expected keys: subsidiaries, directors, owners (arrays)
```

**Why It Happened:**
- The HTML file expected a specific JSON format
- The data didn't have required keys or wasn't valid

**How It's Fixed:**
✅ Updated `app.py` to return proper JSON format
✅ Updated `index.html` to validate data before parsing
✅ Added `utils.py` with validation functions

**Test It:**
```bash
# Should return valid JSON
curl http://localhost:5000/sample_data
```

---

### 🚀 GET RUNNING IN 5 STEPS

**Step 1: Setup**
```bash
mkdir corp-analysis && cd corp-analysis
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir templates uploads
```

**Step 2: Add Files**
- Place `app.py` in root
- Place `utils.py` in root
- Place `index.html` in `templates/`
- Place `requirements.txt` in root

**Step 3: Run**
```bash
python app.py
```

**Step 4: Open Browser**
Visit: http://localhost:5000

**Step 5: Upload & Analyze**
- Upload DEF 14A (required)
- Upload 10-K (optional)
- Click "Analyze Documents"
- Download JSON or view graph

---

### 📊 WHAT EACH PYTHON FILE DOES

**app.py (600+ lines)**
- Flask web server
- PDF extraction (pdfplumber)
- Entity parsing (subsidiaries, directors, owners)
- REST API endpoints
- File upload handling

**utils.py (100+ lines)**
- Data validation
- JSON structure checking
- Error handling
- Data formatting

**requirements.txt**
- pdfplumber (PDF extraction)
- Flask (web framework)
- Werkzeug (file handling)
- reportlab (PDF export)
- gunicorn (production server)

---

### 🔗 KEY API ENDPOINTS

```
POST /upload
├─ Input: 10-K PDF, DEF 14A PDF
└─ Output: {"subsidiaries": [...], "directors": [...], "owners": [...], "metrics": {...}}

GET /sample_data
├─ Input: None
└─ Output: Sample Apple Inc. data

POST /download_json
├─ Input: Analysis data
└─ Output: JSON file download

POST /export_pdf
├─ Input: Analysis data
└─ Output: PDF report download

GET /view_graph?data=...
├─ Input: Analysis data (URL encoded)
└─ Output: Interactive graph visualization
```

---

### 💡 KEY EXTRACTION FUNCTIONS

**pdf_to_text(filepath)**
```python
# Extracts all text from PDF
text = pdf_to_text('apple_10k.pdf')
```

**parse_exhibit21(text)**
```python
# Extracts subsidiaries from Exhibit 21
subs = parse_exhibit21(text)
# Returns: [{"name": "...", "jurisdiction": "..."}, ...]
```

**parse_def14a_directors(text)**
```python
# Extracts board members from DEF 14A
directors = parse_def14a_directors(text)
# Returns: [{"name": "...", "role": "..."}, ...]
```

**parse_def14a_beneficial_owners(text)**
```python
# Extracts shareholders from DEF 14A
owners = parse_def14a_beneficial_owners(text)
# Returns: [{"name": "...", "ownership": 7.32}, ...]
```

**extract_from_filings(ten_k_text, def14a_text)**
```python
# Main function - orchestrates all extraction
result = extract_from_filings(ten_k, def14a)
# Returns: {"subsidiaries": [...], "directors": [...], "owners": [...]}
```

**calculate_metrics(data)**
```python
# Calculates investment metrics
metrics = calculate_metrics(data)
# Returns: {
#   "complexity_score": 6.8,
#   "governance_score": 8.1,
#   "risk_level": "MEDIUM",
#   ...
# }
```

---

### 📈 OUTPUT FORMAT

**Successful Response:**
```json
{
  "subsidiaries": [
    {"name": "Apple Ireland", "jurisdiction": "Ireland", "type": "subsidiary"}
  ],
  "directors": [
    {"name": "Luca Maestri", "role": "CFO", "type": "director"}
  ],
  "owners": [
    {"name": "Vanguard", "ownership": 7.32, "type": "owner"}
  ],
  "metrics": {
    "complexity_score": 6.8,
    "governance_score": 8.1,
    "risk_level": "MEDIUM"
  }
}
```

---

### 🔧 COMMON CUSTOMIZATIONS

**Change Port:**
```python
# In app.py, find:
app.run(debug=True, host='0.0.0.0', port=5000)
# Change port:
app.run(debug=True, host='0.0.0.0', port=8080)
```

**Adjust Max File Size:**
```python
# In app.py, find:
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
# Change to 100MB:
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
```

**Add New Title Keywords:**
```python
# In app.py, in parse_def14a_directors():
title_keywords = [
    "Director", "CEO", "President", 
    "Chief Marketing Officer",  # Add this
    "Controller"                # Add this
]
```

**Modify Extraction Patterns:**
```python
# In app.py, in parse_exhibit21():
patterns = [
    r'custom_pattern_1',
    r'custom_pattern_2'
]
```

---

### 🐛 TROUBLESHOOTING QUICK FIX

| Problem | Solution |
|---------|----------|
| **Port already in use** | Change port to 8080 in app.py |
| **Module not found** | Run `pip install -r requirements.txt` |
| **No subsidiaries found** | Check if PDF has Exhibit 21, adjust patterns |
| **JSON parsing error** | Update to new app.py that validates data |
| **PDF extraction fails** | Ensure PDF is text-based, not scanned |
| **Can't upload file** | Check file size < 50MB, format is PDF |
| **Metrics not calculated** | Ensure data has proper structure |

---

### 🚀 NEXT STEPS

1. **Now:** Copy files and run `python app.py`
2. **Test:** Visit http://localhost:5000
3. **Upload:** Download real 10-K/DEF 14A from SEC EDGAR
4. **Analyze:** See results in real-time
5. **Export:** Download JSON for further analysis
6. **Deploy:** Push to Railway.app, Heroku, or Docker

---

### 📚 FILE LOCATIONS

After setup:
```
corporate-hierarchy-analysis/
├── app.py                 ← Flask backend
├── utils.py              ← Validation helpers
├── requirements.txt      ← Python dependencies
├── templates/
│   ├── index.html       ← Upload page
│   └── financial-demo.html  ← Visualization
└── uploads/             ← Temp files
```

---

### 💻 COMMAND REFERENCE

**Setup Environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run Application:**
```bash
python app.py
# Opens: http://localhost:5000
```

**Test API:**
```bash
curl http://localhost:5000/sample_data
```

**Deactivate Virtual Environment:**
```bash
deactivate
```

---

### ✅ VERIFICATION CHECKLIST

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] app.py in root folder
- [ ] utils.py in root folder
- [ ] index.html in templates/ folder
- [ ] uploads/ folder exists
- [ ] `python app.py` runs without errors
- [ ] Browser opens to http://localhost:5000
- [ ] Can upload files successfully

---

## 🎊 YOU'RE READY!

**What You Have:**
✅ Complete Python backend (600+ lines)
✅ Professional web interface
✅ PDF extraction working
✅ Entity parsing algorithms
✅ Investment metrics calculation
✅ REST API ready
✅ Error handling included
✅ 100% free, no APIs needed

**You Can Now:**
✅ Upload 10-K and DEF 14A files
✅ Automatically extract corporate structure
✅ Calculate investment metrics
✅ Export results as JSON
✅ View interactive graphs
✅ Deploy to production

**Next: Run `python app.py` and start analyzing! 🚀**