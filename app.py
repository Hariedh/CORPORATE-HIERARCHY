#!/usr/bin/env python3
"""
Corporate Hierarchy & Investment Analysis Platform
Backend implementation for SEC filing analysis
"""

import os
import json
import re
import pdfplumber
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import io

# ============================================================================
# CONFIGURATION
# ============================================================================

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_text(filepath):
    """Extract text from PDF file"""
    try:
        with pdfplumber.open(filepath) as pdf:
            text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
            return text
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def find_section(text, start_markers, end_markers=None, max_chars=20000):
    """
    Find and extract a section of text between markers
    
    Args:
        text: Full document text
        start_markers: List of regex patterns to find section start
        end_markers: List of regex patterns to find section end
        max_chars: Maximum characters to extract
    
    Returns:
        Extracted text section
    """
    for marker in start_markers:
        match = re.search(marker, text, re.I)
        if match:
            start = match.start()
            
            if end_markers:
                for end_marker in end_markers:
                    end_match = re.search(end_marker, text[start:], re.I)
                    if end_match:
                        return text[start:start + end_match.start()]
            
            return text[start:start + max_chars]
    
    return ""

def parse_exhibit21(text):
    """
    Extract subsidiaries from Exhibit 21 section
    
    Format usually: Company Name (State/Country)
    """
    subsidiaries = []
    seen = set()
    
    # Pattern: Name (Jurisdiction) or Name - Jurisdiction
    patterns = [
        r'^\s*([A-Z][A-Za-z0-9\-,&\.\s]{2,90}?)\s*[\(\-–—]\s*([A-Z][a-z]+(?:\s+[A-Z]{2})?)\s*\)?',
        r'^\s*([A-Z][A-Za-z0-9\-,&\.\s]{2,90}?),\s+([A-Z][a-z]+(?:\s+[A-Z]{2})?)',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            name = match.group(1).strip()
            jurisdiction = match.group(2).strip()
            
            # Normalize
            name = re.sub(r'\s+', ' ', name)
            
            if len(name) > 2 and name.lower() not in seen:
                seen.add(name.lower())
                subsidiaries.append({
                    "name": name,
                    "jurisdiction": jurisdiction,
                    "type": "subsidiary"
                })
    
    return subsidiaries

def parse_def14a_directors(text):
    """
    Extract directors and officers from DEF 14A section
    """
    directors = []
    seen = set()
    
    # Common title keywords
    title_keywords = [
        "Director", "CEO", "President", "Chairman", "CFO", "CTO",
        "Chief Financial Officer", "Chief Executive Officer",
        "General Counsel", "Chief Legal Officer", "Officer",
        "Vice President", "Senior Vice President", "SVP"
    ]
    
    # Pattern: Name followed by title
    title_pattern = "|".join(title_keywords)
    pattern = rf"^[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+.*?({title_pattern})"
    
    for match in re.finditer(pattern, text, re.MULTILINE | re.I):
        # Extract name from start of line
        line_start = max(0, match.start() - 100)
        line_text = text[line_start:match.end()]
        
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)', line_text)
        if name_match:
            name = name_match.group(1).strip()
            role = match.group(1).strip()
            
            if name.lower() not in seen and len(name.split()) >= 2:
                seen.add(name.lower())
                directors.append({
                    "name": name,
                    "role": role,
                    "type": "director"
                })
    
    return directors

def parse_def14a_beneficial_owners(text):
    """
    Extract beneficial owners/shareholders from DEF 14A section
    """
    owners = []
    seen = set()
    
    # Pattern: Company/Entity name followed by percentage
    # E.g., "Berkshire Hathaway 5.45%" or "Vanguard Group – 7.32%"
    patterns = [
        r'([A-Z][A-Za-z0-9\-,&\.\s]{2,80}?)\s+(?:—|–|-|:)?\s*(\d+(?:\.\d+)?)\s*%',
        r'([A-Z][A-Za-z0-9\-,&\.\s]{2,80}?)\s+(\d+(?:\.\d+)?)\s*(?:percent|%)',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            name = match.group(1).strip()
            ownership_str = match.group(2).strip()
            
            # Normalize
            name = re.sub(r'\s+', ' ', name)
            name = name.rstrip('.,')
            
            try:
                ownership = float(ownership_str)
                
                # Filter out noise (very small percentages, common words)
                if 0.1 < ownership < 100 and len(name) > 3 and name.lower() not in seen:
                    seen.add(name.lower())
                    owners.append({
                        "name": name,
                        "ownership": ownership,
                        "type": "owner"
                    })
            except ValueError:
                continue
    
    return owners

def extract_from_filings(pdf_10k_text, pdf_14a_text):
    """
    Main extraction function - processes both 10-K and DEF 14A
    """
    
    # Extract Exhibit 21 (subsidiaries) from 10-K
    exhibit21_text = find_section(
        pdf_10k_text,
        [r"EXHIBIT\s+21", r"exhibit\s+21"],
        [r"EXHIBIT\s+22", r"SIGNATURES", r"ITEM\s+16"]
    )
    
    subsidiaries = parse_exhibit21(exhibit21_text) if exhibit21_text else []
    
    # Extract directors from DEF 14A
    directors_text = find_section(
        pdf_14a_text,
        [r"DIRECTORS", r"EXECUTIVE\s+OFFICERS", r"BOARD\s+MEMBERS"],
        [r"EXECUTIVE\s+COMPENSATION", r"COMPENSATION\s+DISCUSSION", r"CD&A"]
    )
    
    directors = parse_def14a_directors(directors_text) if directors_text else []
    
    # Extract beneficial owners from DEF 14A
    owners_text = find_section(
        pdf_14a_text,
        [
            r"BENEFICIAL\s+OWNER",
            r"SECURITY\s+OWNERSHIP",
            r"PRINCIPAL\s+SHAREHOLDERS"
        ],
        [r"EXECUTIVE\s+OFFICERS", r"DIRECTORS", r"PROPOSAL"]
    )
    
    owners = parse_def14a_beneficial_owners(owners_text) if owners_text else []
    
    return {
        "subsidiaries": subsidiaries,
        "directors": directors,
        "owners": owners
    }

def calculate_metrics(data):
    """Calculate investment analysis metrics"""
    
    metrics = {
        "total_subsidiaries": len(data.get("subsidiaries", [])),
        "total_directors": len(data.get("directors", [])),
        "total_owners": len(data.get("owners", [])),
        "ownership_concentration": sum(o.get("ownership", 0) for o in data.get("owners", [])[:3]),
        "countries": len(set(s.get("jurisdiction", "") for s in data.get("subsidiaries", []))),
        "complexity_score": calculate_complexity_score(data),
        "governance_score": calculate_governance_score(data),
        "risk_level": calculate_risk_level(data)
    }
    
    return metrics

def calculate_complexity_score(data):
    """Calculate corporate complexity index (0-10)"""
    score = 0
    
    # More subsidiaries = more complex
    num_subs = len(data.get("subsidiaries", []))
    score += min(num_subs / 2, 4)
    
    # More countries = more complex
    countries = len(set(s.get("jurisdiction", "") for s in data.get("subsidiaries", [])))
    score += min(countries / 2, 3)
    
    # Offshore focus = more complex
    offshore_count = sum(1 for s in data.get("subsidiaries", []) 
                        if s.get("jurisdiction", "").lower() not in ["us", "usa"])
    score += min(offshore_count / 2, 3)
    
    return round(min(score, 10), 1)

def calculate_governance_score(data):
    """Calculate governance quality score (0-10)"""
    score = 5  # Base score
    
    # More directors = better governance
    num_directors = len(data.get("directors", []))
    score += min(num_directors / 3, 3)
    
    # Diverse roles = better governance
    roles = set(d.get("role", "").lower() for d in data.get("directors", []))
    score += min(len(roles) / 4, 2)
    
    return round(min(score, 10), 1)

def calculate_risk_level(data):
    """Calculate overall risk level"""
    owners = data.get("owners", [])
    
    if not owners:
        return "MEDIUM"
    
    # Sum top 3 owners
    top_ownership = sum(o.get("ownership", 0) for o in sorted(
        owners, 
        key=lambda x: x.get("ownership", 0), 
        reverse=True
    )[:3])
    
    if top_ownership > 25:
        return "HIGH"
    elif top_ownership > 15:
        return "MEDIUM"
    else:
        return "LOW"

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle file upload and analysis
    
    Expects:
    - 10k_file: 10-K PDF
    - def14a_file: DEF 14A PDF
    """
    
    try:
        if 'def14a_file' not in request.files:
            return jsonify({'error': 'DEF 14A file required'}), 400
        
        if 'def14a_file' not in request.files:
            return jsonify({'error': '10-K file required'}), 400
        
        def14a_file = request.files['def14a_file']
        ten_k_file = request.files.get('10k_file')
        
        if not def14a_file or def14a_file.filename == '':
            return jsonify({'error': 'Please select DEF 14A file'}), 400
        
        if ten_k_file and ten_k_file.filename == '':
            ten_k_file = None
        
        # Save files
        def14a_filename = secure_filename(def14a_file.filename)
        def14a_path = os.path.join(app.config['UPLOAD_FOLDER'], f"def14a_{datetime.now().timestamp()}_{def14a_filename}")
        def14a_file.save(def14a_path)
        
        ten_k_path = None
        if ten_k_file and allowed_file(ten_k_file.filename):
            ten_k_filename = secure_filename(ten_k_file.filename)
            ten_k_path = os.path.join(app.config['UPLOAD_FOLDER'], f"10k_{datetime.now().timestamp()}_{ten_k_filename}")
            ten_k_file.save(ten_k_path)
        
        # Extract text
        def14a_text = pdf_to_text(def14a_path)
        ten_k_text = pdf_to_text(ten_k_path) if ten_k_path else ""
        
        if not def14a_text:
            return jsonify({'error': 'Could not extract text from DEF 14A'}), 400
        
        # Extract entities
        result = extract_from_filings(ten_k_text, def14a_text)
        
        # If no subsidiaries in 10-K, try extracting from DEF 14A
        if not result["subsidiaries"] and ten_k_text:
            result["subsidiaries"] = parse_exhibit21(def14a_text)
        
        # Calculate metrics
        metrics = calculate_metrics(result)
        
        # Prepare response
        response_data = {
            "subsidiaries": result["subsidiaries"],
            "directors": result["directors"],
            "owners": result["owners"],
            "metrics": metrics,
            "extracted_at": datetime.now().isoformat()
        }
        
        # Clean up files
        try:
            os.remove(def14a_path)
            if ten_k_path:
                os.remove(ten_k_path)
        except:
            pass
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error in upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/view_graph')
def view_graph():
    """View graph with data"""
    data = request.args.get('data')
    if data:
        return render_template('graph.html', data=data)
    return "No data provided", 400

@app.route('/download_json', methods=['POST'])
def download_json():
    """Download analysis as JSON"""
    try:
        data = request.get_json()
        
        json_data = json.dumps(data, indent=2)
        
        bytes_io = io.BytesIO(json_data.encode('utf-8'))
        
        return send_file(
            bytes_io,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Generate PDF report (requires reportlab)"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        data = request.get_json()
        
        # Create PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1e3c72',
            spaceAfter=30,
        )
        elements.append(Paragraph("Corporate Hierarchy & Investment Analysis", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Metrics
        metrics_data = [
            ["Metric", "Value"],
            ["Total Subsidiaries", str(data.get("metrics", {}).get("total_subsidiaries", 0))],
            ["Total Directors", str(data.get("metrics", {}).get("total_directors", 0))],
            ["Total Owners", str(data.get("metrics", {}).get("total_owners", 0))],
            ["Complexity Score", str(data.get("metrics", {}).get("complexity_score", 0))],
            ["Governance Score", str(data.get("metrics", {}).get("governance_score", 0))],
        ]
        
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#1e3c72'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ]))
        
        elements.append(metrics_table)
        
        # Build PDF
        doc.build(elements)
        
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    
    except ImportError:
        return jsonify({'error': 'PDF export requires reportlab. Install: pip install reportlab'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sample_data')
def sample_data():
    """Return sample data for demo"""
    return jsonify({
        "subsidiaries": [
            {"name": "Apple Inc.", "jurisdiction": "US", "type": "parent"},
            {"name": "Apple Ireland Limited", "jurisdiction": "Ireland", "type": "subsidiary"},
            {"name": "Apple Sales International", "jurisdiction": "Ireland", "type": "subsidiary"},
            {"name": "Apple Japan Limited", "jurisdiction": "Japan", "type": "subsidiary"},
            {"name": "Apple Operations Limited", "jurisdiction": "Ireland", "type": "subsidiary"},
            {"name": "Apple Canada Inc.", "jurisdiction": "Canada", "type": "subsidiary"},
            {"name": "Apple Pty Ltd", "jurisdiction": "Australia", "type": "subsidiary"},
        ],
        "directors": [
            {"name": "Luca Maestri", "role": "CFO", "type": "director"},
            {"name": "Craig Federighi", "role": "SVP Software Engineering", "type": "director"},
            {"name": "Katherine Adams", "role": "SVP General Counsel", "type": "director"},
            {"name": "Deirdre O'Brien", "role": "SVP Retail", "type": "director"},
        ],
        "owners": [
            {"name": "Berkshire Hathaway", "ownership": 5.45, "type": "owner"},
            {"name": "Vanguard Group", "ownership": 7.32, "type": "owner"},
            {"name": "BlackRock", "ownership": 6.12, "type": "owner"},
        ],
        "metrics": {
            "total_subsidiaries": 7,
            "total_directors": 4,
            "total_owners": 3,
            "ownership_concentration": 18.89,
            "countries": 6,
            "complexity_score": 6.8,
            "governance_score": 8.1,
            "risk_level": "MEDIUM"
        }
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Maximum 50MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)