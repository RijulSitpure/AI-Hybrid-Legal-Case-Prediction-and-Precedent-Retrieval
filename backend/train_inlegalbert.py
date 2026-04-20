#!/usr/bin/env python3
"""
train_inlegalbert.py - Fine‑tune law-ai/InLegalBERT on Indian Supreme Court dataset.
"""

import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset
import torch

# ============================================
# 1. Load data
# ============================================
train_df = pd.read_json("indian_data/train.jsonl", lines=True)
test_df = pd.read_json("indian_data/test.jsonl", lines=True)

# Map labels: allowed -> 0, dismissed -> 1 (or vice versa)
label_map = {'allowed': 0, 'dismissed': 1}
train_df['label_id'] = train_df['label'].map(label_map)
test_df['label_id'] = test_df['label'].map(label_map)

# Use the 'facts' field (list of strings) – combine into one string
def format_text(row):
    facts = ' '.join(row['facts']) if isinstance(row['facts'], list) else str(row['facts'])
    return f"{row['title']} {facts}"

train_texts = train_df.apply(format_text, axis=1).tolist()
test_texts = test_df.apply(format_text, axis=1).tolist()
train_labels = train_df['label_id'].tolist()
test_labels = test_df['label_id'].tolist()

# ============================================
# 2. Tokenization
# ============================================
model_name = "law-ai/InLegalBERT"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize_function(examples):
    return tokenizer(examples['text'], truncation=True, padding='max_length', max_length=512)

train_dataset = Dataset.from_dict({'text': train_texts, 'label': train_labels})
test_dataset = Dataset.from_dict({'text': test_texts, 'label': test_labels})

train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

train_dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'label'])
test_dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'label'])

# ============================================
# 3. Model
# ============================================
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# ============================================
# 4. Training arguments
# ============================================
training_args = TrainingArguments(
    output_dir='../models/inlegalbert_finetuned',
    evaluation_strategy='epoch',
    save_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=4,
    weight_decay=0.01,
    logging_dir='../logs',
    logging_steps=100,
    load_best_model_at_end=True,
    metric_for_best_model='accuracy',
    save_total_limit=2,
    fp16=False,          # set to True if you have GPU with fp16 support
    report_to='none',
)

# ============================================
# 5. Metrics
# ============================================
from sklearn.metrics import accuracy_score, f1_score

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    return {'accuracy': acc, 'f1': f1}

# ============================================
# 6. Trainer
# ============================================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
)

# ============================================
# 7. Train and save
# ============================================
trainer.train()
trainer.save_model('../models/inlegalbert_finetuned')
tokenizer.save_pretrained('../models/inlegalbert_finetuned')

print("✅ InLegalBERT fine‑tuning complete. Model saved to ../models/inlegalbert_finetuned")