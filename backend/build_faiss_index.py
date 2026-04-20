# build_faiss_index.py - Build FAISS index for Indian Supreme Court dataset
import os
import sys

# Force CPU and limit threads to avoid MPS crashes
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_NO_TF'] = '1'

import torch
torch.set_num_threads(4)
torch.set_default_device('cpu')

# Now import the rest
import json
import pandas as pd
import numpy as np
from contextual_retrieval import ContextualRetrieval
import os

def build_index():
    # Use Indian training data (adjust path if needed)
    data_path = 'indian_data/train.jsonl'
    if not os.path.exists(data_path):
        # Fallback to alternative location
        data_path = '../indian_data/train.jsonl'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Please run build_indian_dataset.py first.")
        return

    print("Loading Indian training data...")
    with open(data_path, 'r') as f:
        data = [json.loads(line) for line in f]
    df = pd.DataFrame(data)

    texts = []
    metadata = []
    for idx, row in df.iterrows():
        title = row.get('title', '')
        facts = ' '.join(row.get('facts', [])) if isinstance(row.get('facts'), list) else str(row.get('facts', ''))
        case_text = f"{title} {facts}"[:1000]  # limit length
        texts.append(case_text)
        # Map label to judgment (for consistency with app.py)
        label = row.get('label', 'unknown')
        judgment = 'violation' if label == 'allowed' else 'no_violation' if label == 'dismissed' else 'unknown'
        metadata.append({
            'index': idx,
            'title': title,
            'facts': row.get('facts', []),
            'judgment_date': row.get('judgment_date', ''),
            'judgment': judgment,   # 'violation' or 'no_violation'
            'original_label': label  # keep for reference
        })

    print(f"Prepared {len(texts)} texts. Building index on CPU (this may take a few minutes)...")
    retriever = ContextualRetrieval(model_name='all-MiniLM-L6-v2')
    retriever.build_index(texts, metadata)
    os.makedirs('../models', exist_ok=True)
    # Save with Indian-specific name
    retriever.save_index('../models/faiss_indian_index.bin')
    print("\n✅ FAISS index built and saved to ../models/faiss_indian_index.bin")

if __name__ == '__main__':
    build_index()