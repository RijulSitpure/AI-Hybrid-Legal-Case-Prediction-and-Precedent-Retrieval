import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import re
import os
import warnings
warnings.filterwarnings('ignore')

# Download NLTK resources
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

print("=" * 60)
print("LEGAL CASE PREDICTION SYSTEM - Indian Supreme Court (Random Forest + BM25)")
print("=" * 60)

# =============================================
# 1. Data Loading and Preprocessing
# =============================================

def load_jsonl(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        print(f"✓ Loaded {len(data)} samples from {file_path}")
        return pd.DataFrame(data)
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return pd.DataFrame()

print("\n📂 Loading datasets...")
train_df = load_jsonl("indian_data/train.jsonl")
test_df = load_jsonl("indian_data/test.jsonl")

if train_df.empty or test_df.empty:
    print("\n❌ Error: Could not load data files. Please check file paths.")
    exit()

print(f"\n📊 Dataset Summary:")
print(f"   Training samples: {len(train_df)}")
print(f"   Testing samples: {len(test_df)}")

def legal_preprocess(text):
    if not isinstance(text, str):
        return ""
    # Preserve legal references (Article, Section, Act, Rule)
    text = re.sub(r'(Article|article|Art|art|Section|section|Sec|sec|Act|act|Rule|rule)(\s+\d+)', r'LEGAL_REF\2', text)
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = word_tokenize(text)
    legal_stopwords = set(stopwords.words('english')).union({
        'court', 'case', 'applicant', 'respondent', 'paragraph',
        'would', 'could', 'also', 'however', 'therefore', 'shall'
    })
    tokens = [word for word in tokens if word not in legal_stopwords and len(word) > 2]
    return ' '.join(tokens)

def remove_outcome_from_text(text):
    """Remove outcome‑indicative phrases to reduce data leakage."""
    if not isinstance(text, str):
        return text
    outcome_phrases = [
        r'appeal allowed', r'appeal dismissed', r'petition allowed', r'petition dismissed',
        r'we allow', r'we dismiss', r'is allowed', r'is dismissed', r'allowed', r'dismissed',
        r'conviction upheld', r'conviction set aside', r'we uphold', r'we set aside',
        r'judgment in favour of', r'judgment against'
    ]
    for phrase in outcome_phrases:
        text = re.sub(r'\b' + phrase + r'\b', '', text, flags=re.IGNORECASE)
    return text.strip()

def preprocess_data(df, is_train=True):
    df['full_text'] = (
        df['title'].fillna('') + ' ' +
        df['judgment_date'].astype(str) + ' ' +
        df['facts'].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
    )
    # Remove outcome keywords
    df['full_text'] = df['full_text'].apply(remove_outcome_from_text)
    df['processed_text'] = df['full_text'].apply(legal_preprocess)
    if 'label' in df.columns:
        df['judgment'] = df['label'].apply(lambda x: 'violation' if x == 'allowed' else 'no_violation')
    return df

print("\n🔄 Preprocessing text data...")
train_df = preprocess_data(train_df, is_train=True)
test_df = preprocess_data(test_df, is_train=False)
print("✓ Preprocessing complete")

# =============================================
# 2. Feature Extraction
# =============================================

print("\n📊 Extracting features...")

tfidf = TfidfVectorizer(max_features=5000, min_df=2, max_df=0.95)
X_train_tfidf = tfidf.fit_transform(train_df['processed_text'])
X_test_tfidf = tfidf.transform(test_df['processed_text'])
print(f"✓ TF-IDF features: {X_train_tfidf.shape[1]} features")

judgment_map = {label: idx for idx, label in enumerate(train_df['judgment'].unique())}
y_train = train_df['judgment'].map(judgment_map).values
y_test = test_df['judgment'].map(judgment_map).values if 'judgment' in test_df.columns else None

print(f"\n📈 Label distribution:")
print(f"   Classes: {judgment_map}")
print(f"   Training: {np.bincount(y_train)}")

# =============================================
# 3. Random Forest (baseline)
# =============================================

print("\n🤖 Training Random Forest...")
print("-" * 40)

rf_model = RandomForestClassifier(n_estimators=100, warm_start=True, random_state=42, n_jobs=-1)
rf_model.fit(X_train_tfidf, y_train)

def update_random_forest(new_texts, new_labels, additional_trees=20):
    global rf_model, tfidf
    X_new = tfidf.transform(new_texts)
    y_new = np.array(new_labels)
    rf_model.n_estimators += additional_trees
    rf_model.fit(X_new, y_new)
    print(f"✓ Random Forest updated: +{additional_trees} trees, total {rf_model.n_estimators}")
    import pickle
    os.makedirs('../models', exist_ok=True)
    with open('../models/random_forest_model.pkl', 'wb') as f:
        pickle.dump(rf_model, f)
    return rf_model

if y_test is not None:
    rf_predictions = rf_model.predict(X_test_tfidf)
    rf_accuracy = accuracy_score(y_test, rf_predictions)
    rf_precision = precision_score(y_test, rf_predictions, average='weighted')
    rf_recall = recall_score(y_test, rf_predictions, average='weighted')
    rf_f1 = f1_score(y_test, rf_predictions, average='weighted')
    
    print(f"\n📊 Random Forest Performance:")
    print(f"   Accuracy:  {rf_accuracy:.4f}")
    print(f"   Precision: {rf_precision:.4f}")
    print(f"   Recall:    {rf_recall:.4f}")
    print(f"   F1-Score:  {rf_f1:.4f}")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, rf_predictions, target_names=judgment_map.keys()))

# =============================================
# 4. Precedent Retrieval (BM25)
# =============================================

from rank_bm25 import BM25Okapi

print("\n" + "=" * 60)
print("📚 BUILDING PRECEDENT RETRIEVAL ENGINE")
print("=" * 60)

print("Tokenizing training cases for BM25 index...")
tokenized_cases = [word_tokenize(text.lower()) for text in train_df['processed_text']]
bm25 = BM25Okapi(tokenized_cases)
print(f"✓ BM25 index built with {len(tokenized_cases)} precedent cases")

case_metadata = []
for idx, row in train_df.iterrows():
    case_metadata.append({
        'index': idx,
        'title': row['title'],
        'judgment_date': row['judgment_date'],
        'judgment': row['judgment'],
        'facts': row['facts'] if isinstance(row['facts'], list) else [str(row['facts'])]
    })

def retrieve_precedents(case_text, top_k=5):
    processed_query = legal_preprocess(case_text)
    tokenized_query = word_tokenize(processed_query.lower())
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[-top_k:][::-1]
    precedents = []
    for idx in top_indices:
        if scores[idx] > 0:
            precedents.append({
                'rank': len(precedents) + 1,
                'title': case_metadata[idx]['title'],
                'judgment_date': case_metadata[idx]['judgment_date'],
                'outcome': case_metadata[idx]['judgment'],
                'relevance_score': float(scores[idx]),
                'facts': case_metadata[idx]['facts'][:2] if case_metadata[idx]['facts'] else []
            })
    return precedents

# =============================================
# 5. Prediction + Precedents (Random Forest only)
# =============================================

def predict_with_precedents(case_data, top_k=5):
    case_text = (case_data.get('title', '') + ' ' +
                 str(case_data.get('judgment_date', '')) + ' ' +
                 ' '.join(case_data.get('facts', [])))
    processed_text = legal_preprocess(case_text)
    features = tfidf.transform([processed_text])
    proba = rf_model.predict_proba(features)[0]
    pred_idx = np.argmax(proba)
    confidence = proba[pred_idx]
    prediction = list(judgment_map.keys())[list(judgment_map.values()).index(pred_idx)]
    precedents = retrieve_precedents(case_text, top_k=top_k)
    return {
        'prediction': prediction,
        'confidence': float(confidence),
        'precedents': precedents,
        'case_summary': {'title': case_data.get('title', ''), 'facts': case_data.get('facts', [])}
    }

# =============================================
# 6. Demo on test samples
# =============================================

print("\n" + "=" * 60)
print("🔮 EXAMPLE PREDICTIONS WITH PRECEDENTS")
print("=" * 60)

test_indices = [0, 1, 2]
for idx in test_indices:
    case_data = {
        'title': test_df.iloc[idx]['title'],
        'facts': test_df.iloc[idx]['facts'],
        'judgment_date': test_df.iloc[idx]['judgment_date'],
    }
    print(f"\n{'='*60}")
    print(f"CASE {idx+1}: {case_data['title'][:70]}...")
    print(f"{'='*60}")
    print(f"📝 Facts: {' '.join(case_data['facts'][:2])[:200]}...")
    result = predict_with_precedents(case_data, top_k=3)
    print(f"\n🎯 PREDICTION: {result['prediction'].upper()}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"\n📚 SUPPORTING PRECEDENTS (Ranked by Relevance):")
    for p in result['precedents']:
        print(f"\n   [{p['rank']}] {p['title'][:70]}")
        print(f"       Outcome: {p['outcome']} | Relevance Score: {p['relevance_score']:.2f}")
        if p.get('facts'):
            print(f"       Key Facts: {' '.join(p['facts'][:1])[:100]}...")
    actual = test_df.iloc[idx]['judgment']
    print(f"\n✅ ACTUAL OUTCOME: {actual}")
    print(f"{'='*60}")

# =============================================
# 7. Consistency Analysis
# =============================================

print("\n" + "=" * 60)
print("⚖️ VERDICT CONSISTENCY ANALYSIS")
print("=" * 60)

consistent_cases = 0
total_analyzed = min(50, len(test_df))
for idx in range(total_analyzed):
    case_data = {
        'title': test_df.iloc[idx]['title'],
        'facts': test_df.iloc[idx]['facts'],
        'judgment_date': test_df.iloc[idx]['judgment_date'],
    }
    result = predict_with_precedents(case_data, top_k=3)
    if result['precedents'] and result['precedents'][0]['outcome'] == result['prediction']:
        consistent_cases += 1
consistency_rate = consistent_cases / total_analyzed * 100
print(f"\n📊 Analysis based on {total_analyzed} test cases:")
print(f"   • Cases where top precedent matches prediction: {consistent_cases}/{total_analyzed}")
print(f"   • Consistency Rate: {consistency_rate:.1f}%")
print(f"\n💡 This shows the system provides EVIDENCE-BACKED predictions!")

# =============================================
# 8. Save models for Flask API
# =============================================

print("\n" + "=" * 60)
print("💾 SAVING MODELS FOR FLASK APP")
print("=" * 60)

os.makedirs('../models', exist_ok=True)
import pickle
with open('../models/bm25_index.pkl', 'wb') as f:
    pickle.dump(bm25, f)
with open('../models/case_metadata.pkl', 'wb') as f:
    pickle.dump(case_metadata, f)
with open('../models/tfidf_vectorizer.pkl', 'wb') as f:
    pickle.dump(tfidf, f)
with open('../models/random_forest_model.pkl', 'wb') as f:
    pickle.dump(rf_model, f)
with open('../models/judgment_map.pkl', 'wb') as f:
    pickle.dump(judgment_map, f)
print("✓ All models saved to ../models/")

print("\n🎉 SYSTEM READY! Run 'python app.py' to start the API.")