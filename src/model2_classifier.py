"""
Model 2: Ticket Category Classification
========================================
Zero-shot ticket category classification using semantic similarity.

Approach:
- NO training data required
- Uses pre-trained embeddings (same model as Model 1)
- Compares ticket text to category descriptions
- Picks category with highest semantic similarity

Architecture:
- Input: Ticket subject + description
- Process: Embed ticket → Compare to embedded category descriptions → Similarity ranking
- Output: Predicted category + confidence score + top matches

Enterprise Benefits:
- Deterministic and explainable
- No training pipeline needed
- Easy to add/modify categories (just update descriptions)
- Fully auditable: shows why a category was chosen
- Multi-tenant safe: no tenant-specific training
"""

import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import pickle

from src.category_definitions import (
    CATEGORIES,
    CATEGORY_DESCRIPTIONS,
    get_category_description,
    validate_category
)


class TicketCategoryClassifier:
    """Zero-shot ticket category classifier using semantic similarity."""
    
    def __init__(self, model_name='all-MiniLM-L6-v2', cache_dir='data/category_embeddings.pkl'):
        """
        Initialize the category classifier.
        
        Args:
            model_name: Name of the sentence transformer model (must match Model 1)
            cache_dir: Path to cache category embeddings
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing Ticket Category Classifier")
        
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.categories = CATEGORIES
        
        # Load sentence transformer model
        print(f"Loading sentence transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model loaded (same as Model 1 for consistency)")
        
        # Load or generate category embeddings
        self.category_embeddings = self._load_or_generate_category_embeddings()
        
        print(f"✓ Category Classifier ready")
        print(f"  Total categories: {len(self.categories)}")
        print(f"  Classification method: Zero-shot semantic similarity")
        print(f"  Trainable: False (embeddings only)")
    
    def _load_or_generate_category_embeddings(self):
        """
        Load cached category embeddings or generate new ones.
        
        Returns:
            Dictionary mapping category names to embeddings
        """
        # Try to load from cache
        if os.path.exists(self.cache_dir):
            print(f"Loading cached category embeddings from {self.cache_dir}")
            with open(self.cache_dir, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Verify cache is up to date
            if (cached_data.get('model_name') == self.model_name and 
                set(cached_data.get('categories', [])) == set(self.categories)):
                print(f"✓ Loaded {len(cached_data['embeddings'])} category embeddings from cache")
                return cached_data['embeddings']
            else:
                print(f"⚠ Cache outdated, regenerating embeddings...")
        
        # Generate new embeddings
        print(f"Generating embeddings for {len(self.categories)} categories...")
        category_embeddings = {}
        
        for category in self.categories:
            description = get_category_description(category)
            embedding = self.model.encode(description, convert_to_numpy=True)
            category_embeddings[category] = embedding
        
        # Save to cache
        os.makedirs(os.path.dirname(self.cache_dir), exist_ok=True)
        cache_data = {
            'model_name': self.model_name,
            'categories': self.categories,
            'embeddings': category_embeddings,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(self.cache_dir, 'wb') as f:
            pickle.dump(cache_data, f)
        
        print(f"✓ Generated and cached {len(category_embeddings)} category embeddings")
        
        return category_embeddings
    
    def encode_ticket(self, subject, description):
        """
        Convert a ticket into an embedding.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            
        Returns:
            Embedding vector as numpy array
        """
        # Clean inputs
        subject = str(subject).strip()
        description = str(description).strip()
        
        # Create combined ticket text (same format as Model 1)
        ticket_text = f"{subject}. {description}"
        
        # Generate embedding
        embedding = self.model.encode(ticket_text, convert_to_numpy=True)
        return embedding
    
    def classify_ticket(self, subject, description, top_n=3, verbose=True):
        """
        Classify a ticket into a category using zero-shot semantic similarity.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            top_n: Number of top category matches to return
            verbose: Whether to print detailed output
            
        Returns:
            Dictionary with predicted category, confidence, and top matches
        """
        if verbose:
            print(f"\n{'='*70}")
            print("TICKET CATEGORY CLASSIFICATION (Model 2)")
            print(f"{'='*70}")
            
            print(f"\n📥 Ticket to Classify:")
            print(f"  Subject: {subject}")
            print(f"  Description: {description[:100]}...")
        
        # Step 1: Encode ticket
        if verbose:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Encoding ticket text...")
        ticket_embedding = self.encode_ticket(subject, description)
        if verbose:
            print(f"✓ Ticket embedding generated")
        
        # Step 2: Compute similarity with each category
        if verbose:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Computing similarity with {len(self.categories)} categories...")
        
        category_scores = []
        for category in self.categories:
            category_embedding = self.category_embeddings[category]
            
            # Compute cosine similarity
            similarity = cosine_similarity(
                ticket_embedding.reshape(1, -1),
                category_embedding.reshape(1, -1)
            )[0][0]
            
            category_scores.append({
                'category': category,
                'score': similarity
            })
        
        # Sort by score (descending)
        category_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Get top prediction
        predicted_category = category_scores[0]['category']
        confidence = category_scores[0]['score']
        top_matches = category_scores[:top_n]
        
        if verbose:
            print(f"✓ Classification complete")
            
            print(f"\n{'='*70}")
            print("CLASSIFICATION RESULTS")
            print(f"{'='*70}")
            
            print(f"\n🎯 Predicted Category: {predicted_category}")
            print(f"   Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
            
            print(f"\n📊 Top {top_n} Category Matches:")
            for i, match in enumerate(top_matches, 1):
                indicator = "✓" if i == 1 else " "
                print(f"  {indicator} #{i} {match['category']:<15} - {match['score']:.4f} ({match['score']*100:.2f}%)")
            
            print(f"\n{'='*70}")
            print("EXPLAINABILITY")
            print(f"{'='*70}")
            print(f"\nWhy '{predicted_category}'?")
            print(f"  Ticket text semantically closest to the '{predicted_category}' category description.")
            print(f"  Confidence indicates how strongly the ticket matches this category.")
            print(f"  Method: Zero-shot semantic similarity (no training data).")
        
        return {
            'predicted_category': predicted_category,
            'confidence': confidence,
            'top_matches': top_matches,
            'all_scores': category_scores,
            'method': 'zero-shot-semantic-similarity',
            'explainability': {
                'predicted_category': predicted_category,
                'confidence': confidence,
                'reasoning': f"Ticket semantically most similar to '{predicted_category}' category description",
                'top_alternatives': [m['category'] for m in top_matches[1:top_n]]
            }
        }
    
    def classify_batch(self, tickets, verbose=False):
        """
        Classify multiple tickets.
        
        Args:
            tickets: List of dicts with 'subject' and 'description' keys
            verbose: Whether to print progress
            
        Returns:
            List of classification results
        """
        results = []
        total = len(tickets)
        
        if verbose:
            print(f"Classifying {total} tickets...")
        
        for i, ticket in enumerate(tickets, 1):
            if verbose and i % 10 == 0:
                print(f"  Progress: {i}/{total}")
            
            result = self.classify_ticket(
                subject=ticket['subject'],
                description=ticket['description'],
                verbose=False
            )
            results.append(result)
        
        if verbose:
            print(f"✓ Classified {total} tickets")
        
        return results


def main():
    """Main execution function with test scenarios."""
    print("="*70)
    print("MODEL 2: TICKET CATEGORY CLASSIFICATION")
    print("="*70)
    
    # Initialize classifier
    classifier = TicketCategoryClassifier()
    
    # Test Scenario 1: Clear hardware issue
    print("\n\n" + "="*70)
    print("TEST 1: Hardware Issue")
    print("="*70)
    
    result1 = classifier.classify_ticket(
        subject="Laptop screen flickering",
        description="My laptop screen keeps flickering and sometimes goes completely black. The issue started yesterday and is getting worse.",
        top_n=3
    )
    
    # Test Scenario 2: Network connectivity issue
    print("\n\n" + "="*70)
    print("TEST 2: Network Issue")
    print("="*70)
    
    result2 = classifier.classify_ticket(
        subject="Cannot connect to VPN",
        description="Getting authentication failure when trying to connect to company VPN from home. Tried resetting password but still not working.",
        top_n=3
    )
    
    # Test Scenario 3: Database access issue
    print("\n\n" + "="*70)
    print("TEST 3: Database Issue")
    print("="*70)
    
    result3 = classifier.classify_ticket(
        subject="PostgreSQL connection timeout",
        description="Cannot connect to the production PostgreSQL database. Getting connection timeout errors. Need access urgently for data analysis.",
        top_n=3
    )
    
    # Test Scenario 4: DevOps pipeline issue
    print("\n\n" + "="*70)
    print("TEST 4: DevOps Issue")
    print("="*70)
    
    result4 = classifier.classify_ticket(
        subject="Jenkins build failing",
        description="Our CI/CD pipeline in Jenkins is failing at the deployment step. Build completes but deployment to staging environment times out.",
        top_n=3
    )
    
    # Test Scenario 5: Security concern
    print("\n\n" + "="*70)
    print("TEST 5: Security Issue")
    print("="*70)
    
    result5 = classifier.classify_ticket(
        subject="Suspicious email received",
        description="Received an email claiming to be from IT asking me to verify my credentials. The link looks suspicious and may be phishing.",
        top_n=3
    )
    
    # Summary
    print("\n\n" + "="*70)
    print("CLASSIFICATION SUMMARY")
    print("="*70)
    
    test_results = [
        ("Hardware", result1),
        ("Network", result2),
        ("Database", result3),
        ("DevOps", result4),
        ("Security", result5)
    ]
    
    print(f"\nTest Results:")
    for expected, result in test_results:
        predicted = result['predicted_category']
        confidence = result['confidence']
        match = "✓" if expected == predicted else "✗"
        print(f"  {match} Expected: {expected:<12} | Predicted: {predicted:<12} | Confidence: {confidence:.2f}")
    
    print(f"\n{'='*70}")
    print("✓ CATEGORY CLASSIFICATION TESTING COMPLETED")
    print(f"{'='*70}")
    print(f"\nKey Features:")
    print(f"  - Zero-shot classification (no training data)")
    print(f"  - Semantic similarity-based")
    print(f"  - Fully explainable and deterministic")
    print(f"  - {len(CATEGORIES)} categories supported")
    print(f"  - Ready for integration into AI pipeline")


if __name__ == "__main__":
    main()
