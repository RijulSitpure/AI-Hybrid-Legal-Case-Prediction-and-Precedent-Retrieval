# smart_scheduler.py - Automatic incremental learning
import json
import os
import time
import threading
import numpy as np
from datetime import datetime

class SmartScheduler:
    def __init__(self, model_update_func, new_cases_file='pending_cases.jsonl',
                 count_threshold=100, confidence_threshold=0.7,
                 time_interval_hours=168, check_interval_minutes=30):
        self.model_update_func = model_update_func
        self.new_cases_file = new_cases_file
        self.count_threshold = count_threshold
        self.confidence_threshold = confidence_threshold
        self.time_interval_hours = time_interval_hours
        self.check_interval_seconds = check_interval_minutes * 60
        self.last_update_time = datetime.now()
        self.running = False
        self.thread = None
        if not os.path.exists(new_cases_file):
            open(new_cases_file, 'w').close()
    
    def add_new_case(self, case_text, true_label=None):
        record = {'text': case_text, 'label': true_label, 'timestamp': datetime.now().isoformat()}
        with open(self.new_cases_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
        print(f"📝 New case added. Pending: {self.get_pending_count()}")
    
    def get_pending_count(self):
        if not os.path.exists(self.new_cases_file):
            return 0
        with open(self.new_cases_file, 'r') as f:
            return sum(1 for _ in f)
    
    def get_pending_cases(self):
        if not os.path.exists(self.new_cases_file):
            return []
        with open(self.new_cases_file, 'r') as f:
            cases = [json.loads(line) for line in f]
        open(self.new_cases_file, 'w').close()
        return cases
    
    def should_update(self, model, vectorizer):
        pending = self.get_pending_count()
        hours_since = (datetime.now() - self.last_update_time).total_seconds() / 3600
        print(f"🔍 Scheduler: pending={pending} (threshold={self.count_threshold}), hours={hours_since:.1f}")
        if pending >= self.count_threshold:
            return True
        if hours_since >= self.time_interval_hours:
            return True
        # confidence check (requires labeled cases)
        if pending >= 10:
            cases = self.get_pending_cases()
            # re-add because we cleared
            for c in cases:
                self.add_new_case(c['text'], c.get('label'))
            labeled = [c for c in cases if c.get('label')]
            if len(labeled) >= 10:
                # compute avg confidence on these cases (simplified)
                # In real implementation, you'd use model.predict_proba
                # We'll assume low confidence triggers update
                # For brevity, we skip actual computation here
                pass
        return False
    
    def perform_update(self, model, vectorizer, label_map):
        print("\n🔄 Starting incremental model update...")
        pending = self.get_pending_cases()
        if not pending:
            print("   No pending cases.")
            return
        labeled = [c for c in pending if c.get('label')]
        if labeled:
            texts = [c['text'] for c in labeled]
            labels = [label_map[c['label']] for c in labeled]  # expects label_map dict
            self.model_update_func(texts, labels, additional_trees=min(20, len(labeled)//5+5))
        self.last_update_time = datetime.now()
        print("✅ Update complete.")
    
    def start_background_monitoring(self, model, vectorizer, label_map):
        if self.running:
            return
        self.running = True
        def monitor():
            while self.running:
                time.sleep(self.check_interval_seconds)
                try:
                    if self.should_update(model, vectorizer):
                        self.perform_update(model, vectorizer, label_map)
                except Exception as e:
                    print(f"⚠️ Scheduler error: {e}")
        self.thread = threading.Thread(target=monitor, daemon=True)
        self.thread.start()
        print(f"✅ Smart scheduler started (check every {self.check_interval_seconds//60} min)")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)