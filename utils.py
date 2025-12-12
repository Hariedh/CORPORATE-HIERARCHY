#!/usr/bin/env python3
"""
Data validation and helper utilities for corporate hierarchy analysis
"""

import json

def validate_extraction_data(data):
    """
    Validate extracted data structure
    
    Expected format:
    {
        "subsidiaries": [{"name": "", "jurisdiction": "", "type": "subsidiary"}, ...],
        "directors": [{"name": "", "role": "", "type": "director"}, ...],
        "owners": [{"name": "", "ownership": 0.0, "type": "owner"}, ...],
        "metrics": {...}
    }
    """
    
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    
    required_keys = ['subsidiaries', 'directors', 'owners']
    
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
        
        if not isinstance(data[key], list):
            raise ValueError(f"{key} must be a list, got {type(data[key])}")
    
    # Validate structure
    for sub in data.get('subsidiaries', []):
        if not isinstance(sub, dict) or 'name' not in sub or 'jurisdiction' not in sub:
            raise ValueError("Invalid subsidiary structure")
    
    for director in data.get('directors', []):
        if not isinstance(director, dict) or 'name' not in director or 'role' not in director:
            raise ValueError("Invalid director structure")
    
    for owner in data.get('owners', []):
        if not isinstance(owner, dict) or 'name' not in owner or 'ownership' not in owner:
            raise ValueError("Invalid owner structure")
    
    return True

def format_json_response(subsidiaries, directors, owners, metrics=None):
    """
    Format data as proper JSON response
    """
    data = {
        "subsidiaries": ensure_list(subsidiaries),
        "directors": ensure_list(directors),
        "owners": ensure_list(owners)
    }
    
    if metrics:
        data["metrics"] = metrics
    
    validate_extraction_data(data)
    return data

def ensure_list(items):
    """Ensure items is a list"""
    if items is None:
        return []
    if isinstance(items, list):
        return items
    return [items]

def sanitize_json(data):
    """Remove any problematic characters and ensure JSON serializable"""
    if isinstance(data, dict):
        return {k: sanitize_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item) for item in data]
    elif isinstance(data, str):
        # Remove null bytes and control characters
        return data.replace('\x00', '').replace('\r', ' ')
    else:
        return data