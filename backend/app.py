# app.py - Legal Case Prediction API with InLegalBERT, FAISS & Smart Scheduler
import os
import sys

# Force CPU for PyTorch and limit threads to avoid MPS crashes on M4 Mac
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
torch.set_num_threads(4)
torch.set_default_device('cpu')

# Now import the rest
import json
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import re
import pickle
from datetime import datetime

from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Optional imports with error handling
try:
    from contextual_retrieval import ContextualRetrieval
    CONTEXTUAL_AVAILABLE = True
except ImportError:
    CONTEXTUAL_AVAILABLE = False
    print("⚠️ contextual_retrieval module not available. FAISS disabled.")

try:
    from smart_scheduler import SmartScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ smart_scheduler module not available. Scheduler disabled.")

app = Flask(__name__)
CORS(app)
app.secret_key = 'legal-ai-secret-key-2024'

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Global variables
tfidf = None
rf_model = None           # Keep as fallback
judgment_map = None
bm25 = None
case_metadata = None
faiss_retriever = None
scheduler = None

# InLegalBERT model
legalbert_tokenizer = None
legalbert_model = None
USE_LEGALBERT = False    # will be set to True if model loads successfully

def legal_preprocess(text):
    if not isinstance(text, str):
        return ""
    # Indian legal terminology: Article, Section, Act, Rule
    text = re.sub(r'(Article|article|Art|art|Section|section|Sec|sec|Act|act|Rule|rule)(\s+\d+)', r'LEGAL_REF\2', text)
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = word_tokenize(text)
    legal_stopwords = set(stopwords.words('english')).union({
        'court', 'case', 'applicant', 'respondent', 'would', 'could'
    })
    tokens = [w for w in tokens if w not in legal_stopwords and len(w) > 2]
    return ' '.join(tokens)

def load_models():
    global tfidf, rf_model, judgment_map, bm25, case_metadata, faiss_retriever
    global legalbert_tokenizer, legalbert_model, USE_LEGALBERT

    print("Loading models...")

    # 1. Load Random Forest (fallback)
    try:
        with open('../models/tfidf_vectorizer.pkl', 'rb') as f:
            tfidf = pickle.load(f)
        with open('../models/random_forest_model.pkl', 'rb') as f:
            rf_model = pickle.load(f)
        print("✓ Random Forest loaded")
    except Exception as e:
        print(f"❌ Random Forest load error: {e}")
        return False

    # 2. Load BM25 and metadata
    try:
        with open('../models/bm25_index.pkl', 'rb') as f:
            bm25 = pickle.load(f)
        with open('../models/case_metadata.pkl', 'rb') as f:
            case_metadata = pickle.load(f)
        print("✓ BM25 index loaded")
    except Exception as e:
        print(f"⚠️ BM25 not found: {e}")

    # 3. Load FAISS (optional)
    if CONTEXTUAL_AVAILABLE:
        try:
            faiss_retriever = ContextualRetrieval()
            faiss_retriever.load_index('../models/faiss_indian_index.bin')
            print("✓ FAISS retriever loaded")
        except Exception as e:
            print(f"⚠️ FAISS not loaded: {e}")
            faiss_retriever = None
    else:
        print("⚠️ FAISS disabled")

    # 4. Load InLegalBERT fine-tuned model (primary predictor)
    try:
        legalbert_tokenizer = AutoTokenizer.from_pretrained('../models/inlegalbert_finetuned')
        legalbert_model = AutoModelForSequenceClassification.from_pretrained('../models/inlegalbert_finetuned')
        legalbert_model.eval()
        USE_LEGALBERT = True
        print("✓ InLegalBERT fine‑tuned model loaded")
    except Exception as e:
        print(f"⚠️ InLegalBERT model not found, using Random Forest as fallback: {e}")
        USE_LEGALBERT = False

    # 5. Load judgment map
    try:
        with open('../models/judgment_map.pkl', 'rb') as f:
            judgment_map = pickle.load(f)
    except:
        judgment_map = {'violation': 0, 'no_violation': 1}

    return True

def predict_case(case_data):
    """
    Predict using InLegalBERT (if available), else fallback to Random Forest.
    """
    case_text = (
        case_data.get('title', '') + ' ' +
        str(case_data.get('judgment_date', '')) + ' ' +
        ' '.join(case_data.get('facts', []))
    )

    if USE_LEGALBERT and legalbert_model is not None:
        inputs = legalbert_tokenizer(case_text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = legalbert_model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)[0]
        pred_idx = torch.argmax(logits, dim=1).item()
        confidence = probs[pred_idx].item()
        # Map: 0 -> 'violation' (allowed), 1 -> 'no_violation' (dismissed)
        prediction = 'violation' if pred_idx == 0 else 'no_violation'
        return {
            'prediction': prediction,
            'confidence': confidence,
            'probability': {
                'violation': float(probs[0]),
                'no_violation': float(probs[1])
            }
        }
    else:
        # Fallback to Random Forest
        processed_text = legal_preprocess(case_text)
        features = tfidf.transform([processed_text])
        proba = rf_model.predict_proba(features)[0]
        pred_idx = np.argmax(proba)
        confidence = proba[pred_idx]
        prediction = list(judgment_map.keys())[list(judgment_map.values()).index(pred_idx)]
        return {
            'prediction': prediction,
            'confidence': confidence,
            'probability': {
                'violation': float(proba[0]),
                'no_violation': float(proba[1])
            }
        }

def retrieve_precedents_bm25(case_text, top_k=5):
    if bm25 is None or case_metadata is None:
        return []
    processed = legal_preprocess(case_text)
    tokens = word_tokenize(processed.lower())
    scores = bm25.get_scores(tokens)
    top_idx = np.argsort(scores)[-top_k:][::-1]
    precedents = []
    for idx in top_idx:
        if scores[idx] > 0:
            precedents.append({
                'rank': len(precedents)+1,
                'title': case_metadata[idx]['title'][:100],
                'outcome': case_metadata[idx]['judgment'],
                'relevance_score': float(scores[idx]),
                'facts': case_metadata[idx].get('facts', [])[:2]
            })
    return precedents

def retrieve_precedents_faiss(case_text, top_k=5):
    if faiss_retriever is None:
        return []
    try:
        results = faiss_retriever.search(case_text, top_k)
        precedents = []
        for r in results:
            meta = r['metadata']
            precedents.append({
                'rank': len(precedents)+1,
                'title': meta.get('title', 'Unknown')[:100],
                'outcome': meta.get('judgment', 'unknown'),
                'relevance_score': float(r['similarity_score']),
                'facts': meta.get('facts', [])[:2]
            })
        return precedents
    except Exception as e:
        print(f"FAISS error: {e}")
        return []

def retrieve_precedents(case_text, top_k=5, method='bm25'):
    if method == 'bm25':
        return retrieve_precedents_bm25(case_text, top_k)
    elif method == 'faiss':
        return retrieve_precedents_faiss(case_text, top_k)
    else:  # hybrid
        bm25_res = retrieve_precedents_bm25(case_text, top_k)
        faiss_res = retrieve_precedents_faiss(case_text, top_k)
        combined = []
        seen = set()
        for r in bm25_res + faiss_res:
            if r['title'] not in seen:
                seen.add(r['title'])
                combined.append(r)
        combined.sort(key=lambda x: x['relevance_score'], reverse=True)
        for i, r in enumerate(combined[:top_k]):
            r['rank'] = i+1
        return combined[:top_k]

# Local update function for Random Forest (used by scheduler)
def update_random_forest_local(new_texts, new_labels, additional_trees=20):
    global rf_model, tfidf
    X_new = tfidf.transform(new_texts)
    y_new = np.array(new_labels)
    rf_model.n_estimators += additional_trees
    rf_model.fit(X_new, y_new)
    print(f"✓ Random Forest updated: +{additional_trees} trees, total {rf_model.n_estimators}")
    with open('../models/random_forest_model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    return rf_model

# ---------- Routes ----------
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        case_data = {
            'title': data.get('title',''),
            'facts': data.get('facts',[]),
            'judgment_date': data.get('judgment_date', datetime.now().strftime('%Y-%m-%d')),
            'violated_articles': data.get('violated_articles',[])
        }
        prediction = predict_case(case_data)
        method = data.get('retrieval_method', 'bm25')
        case_text = case_data['title'] + ' ' + ' '.join(case_data['facts'])
        precedents = retrieve_precedents(case_text, top_k=5, method=method)
        return jsonify({
            'success': True,
            'prediction': prediction,
            'precedents': precedents,
            'retrieval_method': method,
            'case_summary': {
                'title': case_data['title'],
                'facts': case_data['facts'],
                'facts_count': len(case_data['facts'])
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/sample_cases', methods=['GET'])
def sample_cases():
    # Sample cases for Indian context (you can replace with actual Indian cases)
    samples = [
        {'title': 'KEDAR NARAYAN PARIDA v. STATE OF ORISSA', 'facts': ['Appeal against conviction'], 'violated_articles': []},
        {'title': 'SARDUL SINGH CAVEESHAR v. STATE OF BOMBAY', 'facts': ['Constitutional validity of preventive detention'], 'violated_articles': []},
        {'title': 'MAHENDRA RAMBHAI PATEL v. CONTROLLER OF ESTATE DUTY', 'facts': ['Estate duty assessment'], 'violated_articles': []}
    ]
    return jsonify(samples)

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text','')
    method = data.get('retrieval_method','bm25')
    lines = text.strip().split('\n')
    title = lines[0] if lines else 'Unknown'
    facts = [l.strip() for l in lines[1:] if l.strip()]
    case_data = {'title': title, 'facts': facts or [text[:200]], 'judgment_date': datetime.now().strftime('%Y-%m-%d'), 'violated_articles': []}
    prediction = predict_case(case_data)
    case_text = title + ' ' + ' '.join(facts)
    precedents = retrieve_precedents(case_text, top_k=5, method=method)
    return jsonify({'success': True, 'prediction': prediction, 'precedents': precedents, 'retrieval_method': method,
                    'case_summary': {'title': title, 'facts': facts}})

@app.route('/compare_methods', methods=['POST'])
def compare_methods():
    data = request.json
    case_text = data.get('title','') + ' ' + ' '.join(data.get('facts',[]))
    bm25_res = retrieve_precedents_bm25(case_text, 3)
    faiss_res = retrieve_precedents_faiss(case_text, 3)
    hybrid_res = retrieve_precedents(case_text, 3, method='hybrid')
    return jsonify({'success': True, 'bm25': bm25_res, 'faiss': faiss_res, 'hybrid': hybrid_res})

# Smart Scheduler endpoints (only if available)
if SCHEDULER_AVAILABLE:
    @app.route('/add_case', methods=['POST'])
    def add_case():
        if scheduler is None:
            return jsonify({'success': False, 'error': 'Scheduler not active'})
        data = request.json
        text = data.get('text','')
        if not text:
            return jsonify({'success': False, 'error': 'Empty text'})
        scheduler.add_new_case(text, data.get('label'))
        return jsonify({'success': True, 'message': 'Case added to learning queue'})

    @app.route('/scheduler_status', methods=['GET'])
    def scheduler_status():
        if scheduler is None:
            return jsonify({'success': False, 'error': 'Scheduler not running'})
        return jsonify({'success': True, 'pending_cases': scheduler.get_pending_count(),
                        'last_update': scheduler.last_update_time.isoformat(), 'running': scheduler.running})

    @app.route('/force_update', methods=['POST'])
    def force_update():
        if scheduler is None:
            return jsonify({'success': False, 'error': 'Scheduler not running'})
        scheduler.perform_update(rf_model, tfidf, judgment_map)
        return jsonify({'success': True, 'message': 'Manual update completed'})
else:
    @app.route('/add_case', methods=['POST'])
    def add_case():
        return jsonify({'success': False, 'error': 'Scheduler not installed'})
    @app.route('/scheduler_status', methods=['GET'])
    def scheduler_status():
        return jsonify({'success': False, 'error': 'Scheduler not installed'})
    @app.route('/force_update', methods=['POST'])
    def force_update():
        return jsonify({'success': False, 'error': 'Scheduler not installed'})

def start_scheduler():
    global scheduler
    if not SCHEDULER_AVAILABLE:
        print("⚠️ SmartScheduler not available, skipping.")
        return
    def update_wrapper(texts, labels, additional_trees):
        return update_random_forest_local(texts, labels, additional_trees)
    scheduler = SmartScheduler(model_update_func=update_wrapper, count_threshold=100,
                               check_interval_minutes=30, new_cases_file='pending_cases.jsonl')
    scheduler.start_background_monitoring(rf_model, tfidf, judgment_map)

if __name__ == '__main__':
    print("="*60)
    print("🚀 Legal Case Prediction API with InLegalBERT & FAISS")
    print("="*60)
    if load_models():
        start_scheduler()
        print("\n✅ Ready. Endpoints:")
        print("   POST /predict, GET /sample_cases, POST /analyze_text")
        print("   POST /compare_methods, POST /add_case, GET /scheduler_status, POST /force_update")
        if USE_LEGALBERT:
            print("   Primary predictor: InLegalBERT (fine‑tuned)")
        else:
            print("   Primary predictor: Random Forest (fallback)")
        print("\n🌐 Open browser at http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    else:
        print("❌ Failed to load models. Run legal_prediction_system.py first.")