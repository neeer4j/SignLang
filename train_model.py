"""
Train the gesture model from collected/generated data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.data_collector import DataCollector
from ml.trainer import Trainer


def main():
    print("Loading training data...")
    features, labels = DataCollector.load_all_data()
    
    if features is None:
        print("ERROR: No training data found in data/ directory!")
        print("Run: python generate_data.py --generate")
        return
    
    print(f"Loaded {len(labels)} samples")
    print(f"Classes: {sorted(set(labels))}")
    
    print("\nTraining model...")
    trainer = Trainer()
    accuracy = trainer.train(features, labels)
    
    print(f"\nTest Accuracy: {accuracy:.1%}")
    print(f"Cross-Validation: {trainer.get_cv_accuracy():.1%}")
    
    print("\nSaving model...")
    trainer.save()
    
    summary = trainer.get_training_summary()
    print(f"\n✓ Model saved!")
    print(f"  Classes: {', '.join(summary['classes'])}")
    print(f"  Total classes: {summary['n_classes']}")


if __name__ == "__main__":
    main()
