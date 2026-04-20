import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained('../models/inlegalbert_finetuned')
model = AutoModelForSequenceClassification.from_pretrained('../models/inlegalbert_finetuned')
model.eval()
print("Model loaded.")

print("Loading test data...")
test_data = []
with open('indian_data/test.jsonl', 'r') as f:
    for line in f:
        test_data.append(json.loads(line))
print(f"Loaded {len(test_data)} test cases.")

texts = []
true_labels = []
for item in test_data:
    facts = ' '.join(item['facts']) if isinstance(item['facts'], list) else str(item['facts'])
    texts.append(f"{item['title']} {facts}")
    true_labels.append(0 if item['label'] == 'allowed' else 1)  # 0 = allowed (violation), 1 = dismissed

print("Running predictions...")
predictions = []
with torch.no_grad():
    for text in tqdm(texts):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        outputs = model(**inputs)
        pred = torch.argmax(outputs.logits, dim=1).item()
        predictions.append(pred)

acc = accuracy_score(true_labels, predictions)
print(f"\nTest accuracy: {acc:.4f}")
print("\nClassification Report:")
print(classification_report(true_labels, predictions, target_names=['allowed (violation)', 'dismissed (no_violation)']))