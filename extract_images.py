#!/usr/bin/env python3
"""
Image Extraction Tool
Extracts base64-encoded images from text files and saves them with proper naming convention.
"""

import base64
import os
import sys
from pathlib import Path


def extract_images(input_file: str, output_dir: str = "extracted_images"):
    """
    Extract base64-encoded images from the input text file.
    
    Format expected:
    Line 1: Header (File Name: XX-XX-XXXXX-XX  Total Records: N)
    Line 2+: subdiv_code,year_month,encrypted_metadata,base64_image_data
    
    Naming convention: YYYYMM + subdiv parts + sequence + meter + direction
    Example: 202512212652300611901E.jpg
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    extracted_count = 0
    error_count = 0
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        print("Error: Empty file")
        return
    
    header = lines[0].strip()
    print(f"Processing: {header}")
    
    subdiv_code = None
    if "File Name:" in header:
        parts = header.split("File Name:")[1].split("Total Records:")[0].strip()
        subdiv_code = parts
        print(f"Subdivision Code: {subdiv_code}")
    
    subdiv_parts = subdiv_code.split('-') if subdiv_code else []
    
    for i, line in enumerate(lines[1:], start=1):
        line = line.strip()
        if not line:
            continue
        
        try:
            parts = line.split(',', 3)
            if len(parts) < 4:
                print(f"Line {i+1}: Skipping - invalid format (not enough fields)")
                error_count += 1
                continue
            
            record_subdiv = parts[0]
            year_month = parts[1]
            encrypted_meta = parts[2]
            base64_data = parts[3]
            
            if not base64_data.startswith('/9j/'):
                print(f"Line {i+1}: Skipping - not a valid JPEG base64")
                error_count += 1
                continue
            
            try:
                padding_needed = len(base64_data) % 4
                if padding_needed:
                    base64_data += '=' * (4 - padding_needed)
                image_bytes = base64.b64decode(base64_data)
            except Exception as e:
                print(f"Line {i+1}: Failed to decode base64 - {e}")
                error_count += 1
                continue
            
            subdiv_nums = record_subdiv.replace('-', '')
            sequence = str(i).zfill(3)
            meter = "1"
            direction = "E"
            
            filename = f"{year_month}{subdiv_nums}{sequence}{meter}{direction}.jpg"
            
            filepath = output_path / filename
            with open(filepath, 'wb') as img_file:
                img_file.write(image_bytes)
            
            extracted_count += 1
            print(f"Extracted: {filename}")
            
        except Exception as e:
            print(f"Line {i+1}: Error processing - {e}")
            error_count += 1
            continue
    
    print(f"\n{'='*50}")
    print(f"Extraction Complete!")
    print(f"Total Extracted: {extracted_count}")
    print(f"Errors: {error_count}")
    print(f"Output Directory: {output_path.absolute()}")


def main():
    if len(sys.argv) < 2:
        input_file = "attached_assets/12-21-26523-01_IMAGES_1765046023607.txt"
    else:
        input_file = sys.argv[1]
    
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_images"
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    extract_images(input_file, output_dir)


if __name__ == "__main__":
    main()
