#!/usr/bin/env python3
import io
import os
import re
import json
import random
import logging
import tarfile
import pandas as pd
from tqdm import tqdm
import boto3
from botocore.config import Config
from botocore import UNSIGNED
import tempfile
import pdfplumber
from html import unescape

# ============================================
# CONFIGURATION
# ============================================
BUCKET = 'indian-supreme-court-judgments'
TRAIN_SPLIT = 0.8
MAX_ALLOWED = 100000
MAX_DISMISSED = 100000
OUTPUT_DIR = 'indian_data'
TRAIN_FILE = os.path.join(OUTPUT_DIR, 'train.jsonl')
TEST_FILE = os.path.join(OUTPUT_DIR, 'test.jsonl')
LOG_FILE = os.path.join(OUTPUT_DIR, 'build.log')

os.makedirs(OUTPUT_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

def list_available_years():
    prefix = 'metadata/parquet/'
    years = []
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix, Delimiter='/'):
            if 'CommonPrefixes' in page:
                for cp in page['CommonPrefixes']:
                    folder = cp['Prefix']
                    year_str = folder.split('year=')[-1].strip('/')
                    if year_str.isdigit():
                        years.append(int(year_str))
    except Exception as e:
        logging.error(f"Failed to list years: {e}")
    return sorted(years)

def fetch_metadata_for_years(years):
    all_dfs = []
    for year in years:
        key = f'metadata/parquet/year={year}/metadata.parquet'
        try:
            with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp_file:
                s3.download_file(BUCKET, key, tmp_file.name)
                df = pd.read_parquet(tmp_file.name)
                os.unlink(tmp_file.name)
            if 'year' in df.columns:
                df = df.drop(columns=['year'])
            df['year'] = int(year)
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str)
            all_dfs.append(df)
            logging.info(f"Loaded year {year}: {len(df)} cases")
        except Exception as e:
            logging.warning(f"Skipping year {year}: {e}")
    if not all_dfs:
        raise ValueError("No metadata could be loaded.")
    return pd.concat(all_dfs, ignore_index=True)

def map_disposal_to_label(disposal):
    if not isinstance(disposal, str):
        return 'other'
    d = disposal.lower()
    if 'allowed' in d and 'partly' not in d and 'partial' not in d:
        return 'allowed'
    if 'dismissed' in d or 'rejected' in d:
        return 'dismissed'
    return 'other'

def clean_html(raw_html):
    if not raw_html or raw_html == 'nan':
        return ""
    # Remove HTML tags but preserve text content
    text = re.sub('<[^<]+?>', ' ', raw_html)  # Replace tags with space
    # Decode HTML entities
    text = unescape(text)
    return text

def extract_case_text(text):
    """
    Extract the actual judgment/case text from webpage content.
    Remove navigation, buttons, disclaimers, and metadata UI.
    """
    if not text:
        return ""
    
    # Remove language selectors, buttons, navigation
    text = re.sub(r'select.*?form-select.*?\</select\>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<button.*?\</button\>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'onclick=.*?(?=\s|<|$)', '', text)  # Remove onclick handlers
    text = re.sub(r'Flip view.*?PDF.*?(?=\n|$)', '', text, flags=re.IGNORECASE)  # Remove button text
    
    # Remove common web UI text
    web_ui_patterns = [
        r'Read in.*?Language',
        r'English.*?Hindi.*?Punjabi',
        r'Disclaimer.*?Visitors to the site',
        r'neither the courts.*?e-Committee',
        r'<div.*?class.*?col',  # Bootstrap columns
        r'<nav.*?\</nav\>',      # Navigation
        r'<footer.*?\</footer\>', # Footer
        r'<header.*?\</header\>', # Header
    ]
    
    for pattern in web_ui_patterns:
        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
    
    return text

def fix_common_ocr_errors(text):
    """Fix common OCR mistakes that don't affect readability much."""
    if not text:
        return text
    
    # Common OCR replacements: keep only safe replacements
    ocr_fixes = {
        r'\bu11der\b': 'under',      # u11 -> u (two ones)
        r'\bCo11rt\b': 'Court',      # two ones to u
        r'\bl1able\b': 'liable',     # l1 -> ll
        r'\bl1ability\b': 'liability',
        r'\brnatter\b': 'matter',    # rn -> m
        r'\brnust\b': 'must',
        r'\bappeals\b': 'appeals',   # consistency fixes
        r'b_': 'by',                 # underscore is common OCR error
        r'_': ' ',                   # underscores to spaces (page breaks)
        r'Chaprer': 'Chapter',       # common typo from OCR
        r'abve': 'above',            # missing 'o'
    }
    
    for pattern, replacement in ocr_fixes.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

PDF_INDEX_CACHE = {}
PDF_TAR_PATH_CACHE = {}


def extract_pdf_id(raw_html):
    if not raw_html or raw_html == 'nan':
        return None

    match = re.search(
        r"open_pdf\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"](\d{4})['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)",
        raw_html,
        flags=re.IGNORECASE
    )
    if match:
        return match.group(3)

    match = re.search(r"open_pdf\(\s*[^,]+,\s*[^,]+,\s*['\"]([^'\"]+)['\"]", raw_html, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def get_pdf_tar_s3_key(year):
    return f'data/tar/year={year}/english/english.tar'


def download_pdf_tar(year):
    if year in PDF_TAR_PATH_CACHE:
        return PDF_TAR_PATH_CACHE[year]

    key = get_pdf_tar_s3_key(year)
    with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
        tar_path = tmp_file.name
    try:
        s3.download_file(BUCKET, key, tar_path)
        PDF_TAR_PATH_CACHE[year] = tar_path
        return tar_path
    except Exception as e:
        logging.warning(f"Could not download PDF archive for year {year}: {e}")
        if os.path.exists(tar_path):
            os.unlink(tar_path)
        PDF_TAR_PATH_CACHE[year] = None
        return None


def load_pdf_index(year):
    if year in PDF_INDEX_CACHE:
        return PDF_INDEX_CACHE[year]

    tar_path = download_pdf_tar(year)
    if not tar_path:
        PDF_INDEX_CACHE[year] = []
        return []

    names = []
    try:
        with tarfile.open(tar_path, mode='r:*') as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.lower().endswith('.pdf'):
                    names.append(member.name)
    except Exception as e:
        logging.warning(f"Could not index PDF archive for year {year}: {e}")
    PDF_INDEX_CACHE[year] = names
    return names


def find_pdf_name(pdf_id, year):
    if not pdf_id:
        return None

    names = load_pdf_index(year)
    if not names:
        return None

    lower_names = {name.lower(): name for name in names}
    candidates = [
        f"{pdf_id}.pdf",
        f"{pdf_id}_EN.pdf",
        f"{pdf_id.upper()}.pdf",
        f"{pdf_id.upper()}_EN.pdf",
    ]
    for candidate in candidates:
        if candidate.lower() in lower_names:
            return lower_names[candidate.lower()]

    pdf_id_lower = pdf_id.lower()
    for name in names:
        if pdf_id_lower in name.lower():
            return name
    return None


def extract_pdf_text_from_bytes(pdf_bytes):
    if not pdf_bytes:
        return ""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return "\n".join(pages)
    except Exception as e:
        logging.warning(f"PDF text extraction failed: {e}")
        return ""


def extract_pdf_text_from_tar(pdf_id, year):
    pdf_name = find_pdf_name(pdf_id, year)
    if not pdf_name:
        return ""

    tar_path = download_pdf_tar(year)
    if not tar_path:
        return ""

    try:
        with tarfile.open(tar_path, mode='r:*') as tar:
            member = tar.getmember(pdf_name)
            with tar.extractfile(member) as fp:
                if not fp:
                    return ""
                pdf_bytes = fp.read()
    except Exception as e:
        logging.warning(f"Could not extract PDF {pdf_name} from archive: {e}")
        return ""

    return extract_pdf_text_from_bytes(pdf_bytes)


def clean_text_aggressive(text):
    """
    Full cleaning pipeline:
    1. Remove HTML tags and web UI elements
    2. Remove disclaimers
    3. Extract core case text
    4. Fix OCR errors
    5. Normalize whitespace
    """
    if not text:
        return ""
    
    # Step 0: Clean HTML tags
    text = clean_html(text)
    
    # Step 1: Extract case content (remove UI/nav)
    text = extract_case_text(text)
    
    # Step 2: Remove non-ASCII
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Step 3: Remove disclaimer blocks
    text = re.sub(
        r'English\s*-.*?brought to our notice for carrying out the corrections\.',
        '',
        text,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Step 4: Remove OCR/scanning artifacts
    text = re.sub(r'[ox]\d{3,4}(?=\s|[A-Z])', '', text)  # x959 patterns
    text = re.sub(r'\b[A-Z]h\s+\d+\s+[a-z]', '', text)  # Th 1 a
    text = re.sub(r'&\s*[a-z]+\s*[&•·]*', '', text)       # & symbols
    text = re.sub(r'-{2,}', ' ', text)                    # Multiple dashes
    text = re.sub(r'~{2,}', ' ', text)                    # Multiple tildes
    
    # Step 5: Remove footer (Decision Date, Case No, Disposal, etc.)
    text = re.sub(
        r'Decision Date\s*:.*?Flip viewPDF',
        '',
        text,
        flags=re.DOTALL | re.IGNORECASE
    )
    # Fallback for variations
    text = re.sub(r'Decision Date\s*:.*$', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Flip\s+view.*?PDF.*?$', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Step 6: Fix common OCR errors
    text = fix_common_ocr_errors(text)
    
    # Step 7: Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def main():
    logging.info("Starting Dataset Build with aggressive cleaning (final version)")
    
    available_years = list_available_years()
    logging.info(f"Total available years: {len(available_years)}")
    years_to_process = available_years
    logging.info(f"Processing years: {years_to_process[0]} to {years_to_process[-1]}")

    df = fetch_metadata_for_years(years_to_process)
    logging.info(f"Total raw cases: {len(df)}")

    df['label'] = df['disposal_nature'].apply(map_disposal_to_label)
    allowed = df[df['label'] == 'allowed']
    dismissed = df[df['label'] == 'dismissed']
    logging.info(f"Available allowed: {len(allowed)}, dismissed: {len(dismissed)}")

    # Balance classes
    allowed_sample = allowed if len(allowed) <= MAX_ALLOWED else allowed.sample(MAX_ALLOWED, random_state=42)
    dismissed_sample = dismissed if len(dismissed) <= MAX_DISMISSED else dismissed.sample(MAX_DISMISSED, random_state=42)
    balanced_df = pd.concat([allowed_sample, dismissed_sample]).reset_index(drop=True)
    logging.info(f"Balanced dataset: {len(balanced_df)} cases")

    records = []
    min_text_length = 500  # Increased minimum to ensure substantial content
    pdf_used = 0
    html_fallback = 0

    for _, row in tqdm(balanced_df.iterrows(), total=len(balanced_df), desc="Cleaning Text"):
        raw = row.get('raw_html', '')
        year = int(row['year']) if 'year' in row else None
        pdf_id = extract_pdf_id(raw)
        pdf_text = ""
        if pdf_id and year is not None:
            pdf_text = extract_pdf_text_from_tar(pdf_id, year)

        if pdf_text:
            cleaned = clean_text_aggressive(pdf_text)
            if len(cleaned) >= min_text_length:
                pdf_used += 1
            else:
                cleaned = clean_text_aggressive(raw)
                html_fallback += 1
        else:
            cleaned = clean_text_aggressive(raw)
            html_fallback += 1

        if len(cleaned) < min_text_length:
            continue

        records.append({
            'title': row.get('title', 'Unknown'),
            'facts': [cleaned[:100000]],  # Significantly increased limit to preserve full judgments
            'judgment_date': str(row.get('decision_date', '')),
            'label': row['label']
        })

    logging.info(f"Records after cleaning: {len(records)}")
    logging.info(f"PDF text used: {pdf_used}, HTML fallback: {html_fallback}")

    random.shuffle(records)
    split = int(len(records) * TRAIN_SPLIT)
    
    with open(TRAIN_FILE, 'w') as f:
        for r in records[:split]:
            f.write(json.dumps(r) + '\n')
    with open(TEST_FILE, 'w') as f:
        for r in records[split:]:
            f.write(json.dumps(r) + '\n')

    logging.info(f"Done! Saved {len(records)} total records to {OUTPUT_DIR}")

if __name__ == '__main__':
    main()