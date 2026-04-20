from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained('../models/inlegalbert_finetuned')
model = AutoModelForSequenceClassification.from_pretrained('../models/inlegalbert_finetuned')
model.eval()

case = "The appellant's conviction is set aside. The appeal is allowed."
inputs = tokenizer(case, return_tensors='pt', truncation=True, max_length=512)
with torch.no_grad():
    outputs = model(**inputs)
probs = torch.softmax(outputs.logits, dim=1)[0]
print(f"Allowed (violation): {probs[0]:.4f}, Dismissed (no_violation): {probs[1]:.4f}")