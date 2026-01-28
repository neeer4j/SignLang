import os
import sys
import numpy as np
from ml.data_collector import DataCollector
from ml.trainer import Trainer

def debug_system():
    print("=== DEBUGGING SYSTEM ===")
    
    # 1. Check Data Directory
    print(f"Data Directory: {os.path.abspath('data')}")
    if not os.path.exists('data'):
        print("ERROR: Data directory missing!")
        return

    files = [f for f in os.listdir('data') if f.endswith('.csv')]
    print(f"Found {len(files)} CSV files: {files}")
    
    if not files:
        print("ERROR: No CSV files found. Cannot train.")
        return

    # 2. Try Loading Data
    print("\nLoading Data...")
    try:
        features, labels = DataCollector.load_all_data()
        if features is None:
            print("ERROR: DataCollector returned None.")
            return
            
        print(f"Loaded {len(features)} samples.")
        print(f"Feature shape: {features.shape}")
        
        # Verify feature count (should be 68 now)
        if features.shape[1] != 68:
            print(f"WARNING: Feature count mismatch! Expected 68, got {features.shape[1]}")
    except Exception as e:
        print(f"ERROR Loading data: {e}")
        return

    # 3. Try Training
    print("\nAttempting Training...")
    try:
        trainer = Trainer()
        acc = trainer.train(features, labels)
        print(f"Training successful. Accuracy: {acc}")
        
        path = trainer.save()
        print(f"Model saved to: {path}")
    except Exception as e:
        print(f"ERROR Training: {e}")

if __name__ == "__main__":
    debug_system()
