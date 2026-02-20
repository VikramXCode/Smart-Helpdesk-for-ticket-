"""
ACCURACY EVALUATION SCRIPT
==========================
Calculates REAL accuracy of classification models on your 1,001 tickets.

This script will:
1. Load all tickets from data/tickets.csv
2. Run predictions using Model 2 (baseline zero-shot)
3. Compare predictions to actual category labels
4. Calculate accuracy, precision, recall, F1-score
5. Show confusion matrix
6. Test improvements (hybrid, ensemble if available)

Run: python evaluate_accuracy.py
"""

import os
import sys
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.model2_classifier import TicketCategoryClassifier

# Try to import advanced models (may not exist yet)
try:
    from src.hybrid_classifier import HybridClassifier
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False

try:
    from src.ensemble_predictor import EnsemblePredictor
    from src.model1_weighted_similarity import CategoryWeightedSimilarityMatcher
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False


class AccuracyEvaluator:
    """Evaluate classification accuracy on labeled dataset."""
    
    def __init__(self, tickets_csv_path: str = "data/tickets.csv"):
        """Initialize evaluator with ticket dataset."""
        print("="*70)
        print("ACCURACY EVALUATION - LOADING DATA")
        print("="*70)
        
        # Load tickets
        print(f"\nLoading tickets from: {tickets_csv_path}")
        self.df = pd.read_csv(tickets_csv_path)
        print(f"✓ Loaded {len(self.df)} tickets")
        
        # Show category distribution
        print(f"\nCategory Distribution:")
        category_counts = self.df['category'].value_counts()
        for category, count in category_counts.items():
            print(f"  {category:25s}: {count:4d} tickets ({count/len(self.df)*100:.1f}%)")
        
        # Initialize models
        print(f"\n{'─'*70}")
        print("LOADING MODELS")
        print(f"{'─'*70}\n")
        
        print("[1/3] Loading baseline model (zero-shot)...")
        self.baseline_model = TicketCategoryClassifier()
        print("✓ Baseline model ready\n")
        
        if HYBRID_AVAILABLE:
            print("[2/3] Loading hybrid model (semantic + keywords)...")
            self.hybrid_model = HybridClassifier(self.baseline_model)
            print("✓ Hybrid model ready\n")
        else:
            print("[2/3] Hybrid model not available (skipping)\n")
            self.hybrid_model = None
        
        if ENSEMBLE_AVAILABLE:
            print("[3/3] Loading ensemble model (5-model voting)...")
            self.similarity_model = CategoryWeightedSimilarityMatcher()
            self.ensemble_model = EnsemblePredictor(
                semantic_classifier=self.baseline_model,
                similarity_matcher=self.similarity_model,
                active_learning_engine=None,
                use_tfidf=False
            )
            print("✓ Ensemble model ready\n")
        else:
            print("[3/3] Ensemble model not available (skipping)\n")
            self.ensemble_model = None
    
    def evaluate_model(self, model, model_name: str, use_hybrid: bool = False, 
                      use_ensemble: bool = False) -> Dict:
        """
        Evaluate a classification model.
        
        Args:
            model: The classifier to evaluate
            model_name: Name for display
            use_hybrid: If True, use hybrid.classify() instead of classify_ticket()
            use_ensemble: If True, use ensemble.predict() instead
            
        Returns:
            Dictionary with accuracy metrics
        """
        print(f"\n{'='*70}")
        print(f"EVALUATING: {model_name}")
        print(f"{'='*70}\n")
        
        predictions = []
        ground_truth = []
        correct = 0
        total = 0
        
        # Per-category metrics
        category_correct = defaultdict(int)
        category_total = defaultdict(int)
        category_predictions = defaultdict(lambda: defaultdict(int))  # actual -> predicted counts
        
        print(f"Processing {len(self.df)} tickets...")
        print(f"Progress: ", end='', flush=True)
        
        for idx, row in self.df.iterrows():
            # Progress indicator
            if idx % 100 == 0:
                print(f"{idx}...", end='', flush=True)
            
            subject = str(row['subject'])
            description = str(row['description'])
            actual_category = row['category']
            
            # Get prediction based on model type
            try:
                if use_ensemble:
                    result = model.predict(subject, description, verbose=False)
                    predicted_category = result['predicted_category']
                elif use_hybrid:
                    result = model.classify(subject, description, verbose=False)
                    predicted_category = result['predicted_category']
                else:
                    result = model.classify_ticket(subject, description, verbose=False)
                    predicted_category = result['predicted_category']
                
                predictions.append(predicted_category)
                ground_truth.append(actual_category)
                
                # Update counts
                total += 1
                category_total[actual_category] += 1
                category_predictions[actual_category][predicted_category] += 1
                
                if predicted_category == actual_category:
                    correct += 1
                    category_correct[actual_category] += 1
                    
            except Exception as e:
                print(f"\n⚠️  Error on ticket {idx}: {e}")
                continue
        
        print(f"{total} ✓\n")
        
        # Calculate overall accuracy
        overall_accuracy = (correct / total) * 100 if total > 0 else 0
        
        print(f"\n{'─'*70}")
        print(f"OVERALL RESULTS")
        print(f"{'─'*70}")
        print(f"Total Tickets: {total}")
        print(f"Correct:       {correct}")
        print(f"Incorrect:     {total - correct}")
        print(f"\n⭐ ACCURACY: {overall_accuracy:.2f}%")
        
        # Per-category metrics
        print(f"\n{'─'*70}")
        print(f"PER-CATEGORY ACCURACY")
        print(f"{'─'*70}")
        print(f"{'Category':<25s} {'Total':>6s} {'Correct':>8s} {'Accuracy':>10s}")
        print(f"{'─'*70}")
        
        for category in sorted(category_total.keys()):
            cat_total = category_total[category]
            cat_correct = category_correct[category]
            cat_accuracy = (cat_correct / cat_total * 100) if cat_total > 0 else 0
            
            print(f"{category:<25s} {cat_total:6d} {cat_correct:8d} {cat_accuracy:9.1f}%")
        
        # Calculate precision, recall, F1 per category
        print(f"\n{'─'*70}")
        print(f"PRECISION, RECALL, F1-SCORE")
        print(f"{'─'*70}")
        print(f"{'Category':<25s} {'Precision':>10s} {'Recall':>10s} {'F1-Score':>10s}")
        print(f"{'─'*70}")
        
        precision_scores = []
        recall_scores = []
        f1_scores = []
        
        for category in sorted(category_total.keys()):
            # True Positives: predicted = category AND actual = category
            tp = category_predictions[category][category]
            
            # False Positives: predicted = category BUT actual != category
            fp = sum(category_predictions[other_cat][category] 
                    for other_cat in category_total.keys() if other_cat != category)
            
            # False Negatives: predicted != category BUT actual = category
            fn = sum(category_predictions[category][other_pred] 
                    for other_pred in category_predictions[category].keys() 
                    if other_pred != category)
            
            # Calculate metrics
            precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0
            
            precision_scores.append(precision)
            recall_scores.append(recall)
            f1_scores.append(f1)
            
            print(f"{category:<25s} {precision*100:9.1f}% {recall*100:9.1f}% {f1*100:9.1f}%")
        
        # Average metrics
        avg_precision = np.mean(precision_scores) * 100
        avg_recall = np.mean(recall_scores) * 100
        avg_f1 = np.mean(f1_scores) * 100
        
        print(f"{'─'*70}")
        print(f"{'AVERAGE (macro)':<25s} {avg_precision:9.1f}% {avg_recall:9.1f}% {avg_f1:9.1f}%")
        
        # Confusion insights
        print(f"\n{'─'*70}")
        print(f"TOP 10 MISCLASSIFICATIONS")
        print(f"{'─'*70}")
        print(f"{'Actual Category':<25s} → {'Predicted As':<25s} {'Count':>6s}")
        print(f"{'─'*70}")
        
        misclassifications = []
        for actual in category_predictions:
            for predicted, count in category_predictions[actual].items():
                if actual != predicted and count > 0:
                    misclassifications.append((actual, predicted, count))
        
        # Sort by count descending
        misclassifications.sort(key=lambda x: x[2], reverse=True)
        
        for actual, predicted, count in misclassifications[:10]:
            print(f"{actual:<25s} → {predicted:<25s} {count:6d}")
        
        if not misclassifications:
            print("🎉 No misclassifications! Perfect accuracy!")
        
        return {
            'model_name': model_name,
            'total': total,
            'correct': correct,
            'accuracy': overall_accuracy,
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1': avg_f1,
            'category_accuracy': {cat: (category_correct[cat]/category_total[cat]*100)
                                 for cat in category_total.keys()},
            'predictions': predictions,
            'ground_truth': ground_truth
        }
    
    def compare_models(self, results: List[Dict]):
        """Compare multiple model results side-by-side."""
        print(f"\n\n{'='*70}")
        print(f"MODEL COMPARISON SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"{'Model':<30s} {'Accuracy':>12s} {'Precision':>12s} {'Recall':>12s} {'F1-Score':>12s}")
        print(f"{'─'*70}")
        
        for result in results:
            print(f"{result['model_name']:<30s} "
                  f"{result['accuracy']:11.2f}% "
                  f"{result['avg_precision']:11.2f}% "
                  f"{result['avg_recall']:11.2f}% "
                  f"{result['avg_f1']:11.2f}%")
        
        # Show improvement
        if len(results) > 1:
            baseline_acc = results[0]['accuracy']
            print(f"\n{'─'*70}")
            print(f"IMPROVEMENTS OVER BASELINE")
            print(f"{'─'*70}")
            
            for result in results[1:]:
                improvement = result['accuracy'] - baseline_acc
                improvement_pct = (improvement / baseline_acc) * 100
                
                arrow = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
                print(f"{arrow} {result['model_name']:<30s}: "
                      f"{improvement:+.2f}% absolute ({improvement_pct:+.1f}% relative)")


def main():
    """Run complete accuracy evaluation."""
    
    # Initialize evaluator
    evaluator = AccuracyEvaluator()
    
    # Store results for comparison
    all_results = []
    
    # Evaluate baseline model
    baseline_results = evaluator.evaluate_model(
        evaluator.baseline_model, 
        "Baseline (Zero-Shot Semantic)",
        use_hybrid=False,
        use_ensemble=False
    )
    all_results.append(baseline_results)
    
    # Evaluate hybrid model if available
    if evaluator.hybrid_model:
        hybrid_results = evaluator.evaluate_model(
            evaluator.hybrid_model,
            "Hybrid (Semantic + Keywords)",
            use_hybrid=True,
            use_ensemble=False
        )
        all_results.append(hybrid_results)
    
    # Evaluate ensemble model if available
    if evaluator.ensemble_model:
        ensemble_results = evaluator.evaluate_model(
            evaluator.ensemble_model,
            "Ensemble (5-Model Voting)",
            use_hybrid=False,
            use_ensemble=True
        )
        all_results.append(ensemble_results)
    
    # Compare all models
    if len(all_results) > 1:
        evaluator.compare_models(all_results)
    
    # Final summary
    print(f"\n\n{'='*70}")
    print(f"✅ EVALUATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 REAL ACCURACY (not estimated):")
    print(f"   Baseline Model: {baseline_results['accuracy']:.2f}%")
    
    if evaluator.hybrid_model:
        print(f"   Hybrid Model:   {hybrid_results['accuracy']:.2f}%")
    
    if evaluator.ensemble_model:
        print(f"   Ensemble Model: {ensemble_results['accuracy']:.2f}%")
    
    print(f"\n💡 Use these numbers in your hackathon presentation!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
