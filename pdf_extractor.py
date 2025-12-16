"""
PDF User Information Extraction using Open-Source LLMs

This module extracts user name and designation from unstructured PDF documents
using instruction-tuned Large Language Models.

Author: Hariedh Raju
GitHub: https://github.com/Hariedh/CORPORATE-HIERARCHY
License: MIT
"""

import pdfplumber
import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from pathlib import Path
from typing import Dict, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFUserExtractor:
    """
    Extracts user information (name and designation) from PDF documents
    using open-source Large Language Models.
    
    Attributes:
        model_name (str): HuggingFace model identifier
        tokenizer: Loaded tokenizer instance
        model: Loaded LLM instance
    """
    
    def __init__(
        self, 
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        use_quantization: bool = True,
        device: Optional[str] = None
    ):
        """
        Initialize the PDF User Extractor.
        
        Args:
            model_name: HuggingFace model identifier
            use_quantization: Whether to use 4-bit quantization (saves memory)
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Initializing PDFUserExtractor with model: {model_name}")
        logger.info(f"Device: {self.device}")
        
        if self.device == 'cuda':
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        # Load tokenizer
        self.tokenizer = self._load_tokenizer()
        
        # Load model with or without quantization
        self.model = self._load_model(use_quantization)
        
        logger.info("Model loaded successfully!")
    
    def _load_tokenizer(self) -> AutoTokenizer:
        """Load and configure tokenizer."""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        tokenizer.pad_token = tokenizer.eos_token
        return tokenizer
    
    def _load_model(self, use_quantization: bool) -> AutoModelForCausalLM:
        """Load model with optional quantization."""
        if use_quantization and self.device == 'cuda':
            logger.info("Loading model with 4-bit quantization...")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True
            )
        else:
            logger.info("Loading model without quantization...")
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                device_map="auto" if self.device == 'cuda' else None,
                low_cpu_mem_usage=True
            )
            
            if self.device == 'cpu':
                model = model.to('cpu')
        
        return model
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a string
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF reading fails
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from: {pdf_path.name}")
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Processing {total_pages} pages")
                
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    logger.debug(f"Processed page {i}/{total_pages}")
                    
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise Exception(f"Failed to read PDF: {str(e)}")
        
        if not text.strip():
            raise ValueError("No text found in PDF")
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    
    def clean_text(self, text: str, max_length: int = 1500) -> str:
        """
        Clean and preprocess extracted text.
        
        Args:
            text: Raw extracted text
            max_length: Maximum character length to keep
            
        Returns:
            Cleaned text
        """
        logger.debug("Cleaning text...")
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        # Limit text length for model efficiency
        if len(text) > max_length:
            text = text[:max_length]
            logger.debug(f"Text truncated to {max_length} characters")
        
        return text
    
    def create_extraction_prompt(self, text: str) -> str:
        """
        Create instruction prompt for LLM.
        
        Args:
            text: Cleaned document text
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""[INST] Extract the person's name and job designation from the document below.

Return ONLY valid JSON with these exact fields:
- "name": full name of the person
- "designation": job title or role

If information is not found, use null.

Document:
{text}

JSON: [/INST]"""
        
        return prompt
    
    def generate_llm_response(self, prompt: str, max_new_tokens: int = 150) -> str:
        """
        Generate response from LLM.
        
        Args:
            prompt: Formatted instruction prompt
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        logger.info("Generating LLM response...")
        
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.1,
                do_sample=True,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only generated part (after instruction)
        if "[/INST]" in response:
            response = response.split("[/INST]")[-1].strip()
        
        return response
    
    def parse_json_response(self, response: str) -> Dict[str, Optional[str]]:
        """
        Parse and validate JSON from LLM response.
        
        Args:
            response: Raw LLM output
            
        Returns:
            Dictionary with 'name' and 'designation' keys
        """
        logger.debug("Parsing response...")
        
        try:
            # Try to find JSON object in response
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # Validate required fields exist
                if "name" in data and "designation" in data:
                    return {
                        "name": data.get("name"),
                        "designation": data.get("designation")
                    }
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
        
        logger.warning("Failed to parse JSON, returning null values")
        return {"name": None, "designation": None}
    
    def extract(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """
        Complete extraction pipeline - extracts name and designation from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing:
                - name: Extracted person's name or None
                - designation: Extracted job title or None
                - error: Error message if extraction failed
        """
        logger.info(f"Starting extraction for: {pdf_path}")
        
        try:
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(pdf_path)
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Create prompt
            prompt = self.create_extraction_prompt(cleaned_text)
            
            # Generate LLM response
            response = self.generate_llm_response(prompt)
            
            # Parse output
            result = self.parse_json_response(response)
            
            logger.info("Extraction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {"error": str(e), "name": None, "designation": None}
    
    def batch_extract(self, pdf_paths: List[str]) -> List[Dict]:
        """
        Extract information from multiple PDF files.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of dictionaries with extraction results
        """
        logger.info(f"Starting batch extraction for {len(pdf_paths)} files")
        
        results = []
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing file {i}/{len(pdf_paths)}: {pdf_path}")
            result = self.extract(pdf_path)
            results.append({
                "file": pdf_path,
                "data": result
            })
        
        logger.info("Batch extraction completed")
        return results


def main():
    """
    Example usage of PDFUserExtractor.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract user name and designation from PDF documents"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to PDF file"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="mistralai/Mistral-7B-Instruct-v0.2",
        help="HuggingFace model name"
    )
    parser.add_argument(
        "--no-quantization",
        action="store_true",
        help="Disable 4-bit quantization"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path (optional)"
    )
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = PDFUserExtractor(
        model_name=args.model,
        use_quantization=not args.no_quantization
    )
    
    # Extract information
    result = extractor.extract(args.pdf_path)
    
    # Display results
    print("\n" + "="*60)
    print("EXTRACTED INFORMATION")
    print("="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*60)
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
