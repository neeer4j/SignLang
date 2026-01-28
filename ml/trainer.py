"""
Model Trainer - Train gesture classification model
"""
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from config import MODEL_PATH, LABELS_PATH


class Trainer:
    """Train and save gesture classification model."""
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.accuracy = 0.0
        self.cv_scores = None
    
    def train(self, features: np.ndarray, labels: list, 
              n_estimators: int = 200, test_size: float = 0.2) -> float:
        """Train RandomForest classifier with optimized parameters.
        
        Args:
            features: Training features array
            labels: List of labels
            n_estimators: Number of trees in forest
            test_size: Fraction for test split
            
        Returns:
            Accuracy score on test set
        """
        # Encode labels
        y = self.label_encoder.fit_transform(labels)
        X = features
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train model with optimized parameters for stability
        self.model = RandomForestClassifier(
            n_estimators=100,                # Reduced for speed/generalization
            max_depth=15,                    # Shallower trees to prevent overfitting
            min_samples_split=5,             # Require more samples to split
            min_samples_leaf=2,              # Smoothing at leaves
            max_features='sqrt',             
            class_weight='balanced',         
            bootstrap=True,
            oob_score=True,                  
            random_state=42,
            n_jobs=-1                        
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        self.accuracy = self.model.score(X_test, y_test)
        
        # Cross-validation for more robust accuracy estimate
        self.cv_scores = cross_val_score(self.model, X, y, cv=5)
        
        return self.accuracy
    
    def get_cv_accuracy(self) -> float:
        """Get mean cross-validation accuracy."""
        if self.cv_scores is None:
            return 0.0
        return self.cv_scores.mean()
    
    def save(self, model_path: str = None, labels_path: str = None) -> bool:
        """Save trained model and label encoder.
        
        Returns:
            True if saved successfully
        """
        if self.model is None:
            return False
        
        model_path = model_path or MODEL_PATH
        labels_path = labels_path or LABELS_PATH
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(labels_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        return True
    
    def get_classes(self) -> list:
        """Get list of trained class labels."""
        return self.label_encoder.classes_.tolist()
    
    def get_training_summary(self) -> dict:
        """Get summary of training results."""
        return {
            'accuracy': self.accuracy,
            'cv_accuracy_mean': self.get_cv_accuracy(),
            'cv_accuracy_std': self.cv_scores.std() if self.cv_scores is not None else 0,
            'classes': self.get_classes(),
            'n_classes': len(self.get_classes())
        }
