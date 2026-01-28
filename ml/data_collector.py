"""
Data Collector Module - Capture training samples
"""
import os
import csv
import numpy as np
from datetime import datetime
from config import DATA_DIR


class DataCollector:
    """Collect and save hand landmark data for training."""
    
    def __init__(self):
        self.current_label = None
        self.samples = []
        self.sample_count = {}
    
    def set_label(self, label: str):
        """Set the current label for data collection."""
        self.current_label = label.upper()
        if self.current_label not in self.sample_count:
            self.sample_count[self.current_label] = 0
    
    def add_sample(self, features: np.ndarray) -> bool:
        """Add a sample with current label.
        
        Args:
            features: Feature vector from FeatureExtractor
            
        Returns:
            True if sample was added successfully
        """
        if self.current_label is None or features is None:
            return False
        
        self.samples.append({
            'label': self.current_label,
            'features': features.tolist()
        })
        self.sample_count[self.current_label] = self.sample_count.get(self.current_label, 0) + 1
        return True
    
    def get_sample_count(self, label: str = None) -> int:
        """Get number of samples collected."""
        if label:
            return self.sample_count.get(label.upper(), 0)
        return sum(self.sample_count.values())
    
    def get_label_counts(self) -> dict:
        """Get sample counts per label."""
        return self.sample_count.copy()
    
    def save(self, filename: str = None) -> str:
        """Save collected samples to CSV file.
        
        Args:
            filename: Optional filename, defaults to timestamped name
            
        Returns:
            Path to saved file
        """
        if not self.samples:
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_data_{timestamp}.csv"
        
        filepath = os.path.join(DATA_DIR, filename)
        
        # Get feature count from first sample
        feature_count = len(self.samples[0]['features'])
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            header = ['label'] + [f'f{i}' for i in range(feature_count)]
            writer.writerow(header)
            
            # Data
            for sample in self.samples:
                row = [sample['label']] + sample['features']
                writer.writerow(row)
        
        return filepath
    
    def clear(self):
        """Clear all collected samples."""
        self.samples = []
        self.sample_count = {}
    
    @staticmethod
    def load(filepath: str):
        """Load training data from CSV file.
        
        Returns:
            tuple: (features_array, labels_list)
        """
        features = []
        labels = []
        
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            for row in reader:
                labels.append(row[0])
                features.append([float(x) for x in row[1:]])
        
        return np.array(features, dtype=np.float32), labels
    
    @staticmethod
    def load_all_data():
        """Load all CSV files from data directory.
        
        Returns:
            tuple: (features_array, labels_list)
        """
        all_features = []
        all_labels = []
        
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.csv'):
                filepath = os.path.join(DATA_DIR, filename)
                features, labels = DataCollector.load(filepath)
                all_features.append(features)
                all_labels.extend(labels)
        
        if not all_features:
            return None, None
        
        return np.vstack(all_features), all_labels
