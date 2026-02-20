"""
Model 1 Enhanced: Category-Weighted Similarity Matching
=======================================================
Extends the base similarity matching with category-aware weighting.

Enhancement:
- Prioritizes similar tickets within the same predicted category
- Still allows cross-category matches (no hard filtering)
- Maintains deterministic behavior
- Backward compatible with existing Model 1

Weighting Strategy:
- Same category: weight = 1.0 (full score)
- Different category: weight = 0.6 (reduced score)
- Final score = cosine_similarity × weight
- Duplicate threshold: 0.80 (unchanged)

Enterprise Benefits:
- More accurate duplicate detection
- Category-aware similarity ranking
- Explainable: clear why certain matches scored higher
- No model retraining required
"""

import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity


class CategoryWeightedSimilarityMatcher:
    """Enhanced similarity matcher with category-aware weighting."""
    
    # Weighting factors
    SAME_CATEGORY_WEIGHT = 1.0
    DIFFERENT_CATEGORY_WEIGHT = 0.6
    
    def __init__(self, embeddings_path='data/ticket_embeddings.pkl'):
        """
        Initialize the category-weighted similarity matcher.
        
        Args:
            embeddings_path: Path to the saved embeddings file
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing Category-Weighted Similarity Matcher")
        
        # Load saved embeddings and ticket data
        print(f"Loading embeddings from {embeddings_path}")
        with open(embeddings_path, 'rb') as f:
            embedding_data = pickle.load(f)
        
        self.embeddings = embedding_data['embeddings']
        self.tickets = embedding_data['tickets']
        self.ticket_ids = embedding_data['ticket_ids']
        self.model_name = embedding_data['model_name']
        
        print(f"✓ Loaded {len(self.tickets)} historical tickets")
        print(f"  Model: {self.model_name}")
        print(f"  Embedding dimension: {self.embeddings.shape[1]}")
        print(f"  Category weighting: Same={self.SAME_CATEGORY_WEIGHT}, Different={self.DIFFERENT_CATEGORY_WEIGHT}")
        
        # Load the same model for encoding new tickets
        print(f"Loading sentence transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model ready for new ticket encoding")
        
        # Similarity threshold for duplicate detection
        self.duplicate_threshold = 0.80
    
    def encode_new_ticket(self, subject, description, category=None):
        """
        Convert a new ticket into an embedding.
        
        Args:
            subject: Ticket subject (required)
            description: Ticket description (required)
            category: Optional category for text formatting
            
        Returns:
            Embedding vector as numpy array
        """
        # Clean inputs
        subject = str(subject).strip()
        description = str(description).strip()
        
        # Build ticket text (category optional)
        if category and str(category).strip() and str(category).lower() not in ['nan', 'none', '']:
            ticket_text = f"[{str(category).strip()}] {subject}. {description}"
        else:
            ticket_text = f"{subject}. {description}"
        
        # Generate embedding
        embedding = self.model.encode(ticket_text, convert_to_numpy=True)
        return embedding
    
    def find_similar_tickets_weighted(self, new_ticket_embedding, predicted_category, top_n=3):
        """
        Find most similar historical tickets with category weighting.
        
        Args:
            new_ticket_embedding: Embedding of the new ticket
            predicted_category: Predicted category for the new ticket
            top_n: Number of similar tickets to return
            
        Returns:
            List of dictionaries with ticket, raw_similarity, weighted_score, weight_applied
        """
        # CRITICAL: Handle empty corpus (first-ever ticket scenario)
        if len(self.tickets) == 0 or self.embeddings.shape[0] == 0:
            print("\n⚠️  No historical tickets found.")
            print("   Skipping duplicate detection (zero-shot mode)")
            print("   This is normal for the first ticket in the system.")
            return []
        
        # Reshape for sklearn cosine_similarity
        new_embedding_reshaped = new_ticket_embedding.reshape(1, -1)
        
        # Compute cosine similarity with all historical tickets
        raw_similarities = cosine_similarity(new_embedding_reshaped, self.embeddings)[0]
        
        # Apply category weighting
        weighted_scores = []
        for idx, raw_sim in enumerate(raw_similarities):
            ticket = self.tickets[idx]
            ticket_category = ticket.get('category', 'Other')
            
            # Determine weight based on category match
            if predicted_category and ticket_category == predicted_category:
                weight = self.SAME_CATEGORY_WEIGHT
            else:
                weight = self.DIFFERENT_CATEGORY_WEIGHT
            
            # Calculate weighted score
            weighted_score = raw_sim * weight
            
            weighted_scores.append({
                'ticket': ticket,
                'raw_similarity': raw_sim,
                'weighted_score': weighted_score,
                'weight_applied': weight,
                'category_match': ticket_category == predicted_category
            })
        
        # Sort by weighted score (descending)
        weighted_scores.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        # Return top N
        return weighted_scores[:top_n]
    
    def check_duplicate(self, weighted_score):
        """
        Check if weighted score indicates a duplicate.
        
        Args:
            weighted_score: Weighted similarity score (0-1)
            
        Returns:
            Boolean indicating if this is likely a duplicate
        """
        return weighted_score >= self.duplicate_threshold
    
    def analyze_new_ticket_weighted(self, subject, description, predicted_category, top_n=3, verbose=True):
        """
        Complete weighted analysis pipeline for a new ticket.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            predicted_category: Predicted category for weighting (from Model 2)
            top_n: Number of similar tickets to show
            verbose: Whether to print detailed output
            
        Returns:
            Dictionary with analysis results including weighted scores and explainability
        """
        if verbose:
            print(f"\n{'='*70}")
            print("CATEGORY-WEIGHTED SIMILARITY ANALYSIS")
            print(f"{'='*70}")
            
            print(f"\n📥 Incoming Ticket:")
            print(f"  Predicted Category: {predicted_category}")
            print(f"  Subject: {subject}")
            print(f"  Description: {description}")
        
        # Step 1: Generate embedding
        if verbose:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating embedding for new ticket...")
        new_embedding = self.encode_new_ticket(subject, description, predicted_category)
        if verbose:
            print(f"✓ Embedding generated (dimension: {len(new_embedding)})")
        
        # Step 2: Find similar tickets with category weighting
        if verbose:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Computing weighted similarity...")
            print(f"  Same category weight: {self.SAME_CATEGORY_WEIGHT}")
            print(f"  Different category weight: {self.DIFFERENT_CATEGORY_WEIGHT}")
        
        similar_tickets = self.find_similar_tickets_weighted(new_embedding, predicted_category, top_n)
        
        # CRITICAL: Handle empty corpus gracefully
        if len(similar_tickets) == 0:
            if verbose:
                print("\n⚠️  ZERO-SHOT MODE: No historical tickets for comparison")
                print("   This ticket will be treated as NEW (not a duplicate)")
            
            return {
                'is_duplicate': False,
                'highest_weighted_score': 0.0,
                'highest_raw_similarity': 0.0,
                'similar_tickets': [],
                'weighting_applied': False,
                'predicted_category': predicted_category,
                'explainability': {
                    'same_category_weight': self.SAME_CATEGORY_WEIGHT,
                    'different_category_weight': self.DIFFERENT_CATEGORY_WEIGHT,
                    'duplicate_threshold': self.duplicate_threshold,
                    'category_matches': 0,
                    'zero_shot_mode': True,
                    'reason': 'No historical tickets in database'
                }
            }
        
        if verbose:
            print(f"✓ Top {top_n} similar tickets found (category-weighted)")
        
        # Step 3: Display results
        if verbose:
            print(f"\n{'='*70}")
            print(f"TOP {top_n} SIMILAR TICKETS (Category-Weighted)")
            print(f"{'='*70}")
        
        is_duplicate = False
        results_list = []
        
        for i, result in enumerate(similar_tickets, 1):
            ticket = result['ticket']
            raw_sim = result['raw_similarity']
            weighted_score = result['weighted_score']
            weight = result['weight_applied']
            category_match = result['category_match']
            
            is_dup = self.check_duplicate(weighted_score)
            if i == 1 and is_dup:
                is_duplicate = True
            
            result_dict = {
                'ticket_id': ticket['ticket_id'],
                'category': ticket['category'],
                'subject': ticket['subject'],
                'description': ticket['description'],
                'status': ticket['status'],
                'priority': ticket['priority'],
                'raw_similarity': raw_sim,
                'weighted_score': weighted_score,
                'weight_applied': weight,
                'category_match': category_match,
                'is_duplicate': is_dup
            }
            results_list.append(result_dict)
            
            if verbose:
                duplicate_marker = "⚠️  POSSIBLE DUPLICATE" if is_dup else ""
                category_indicator = "✓ Same Category" if category_match else "✗ Different Category"
                
                print(f"\n#{i} - Weighted Score: {weighted_score:.4f} ({weighted_score*100:.2f}%) {duplicate_marker}")
                print(f"  Raw Similarity: {raw_sim:.4f} × Weight {weight} = {weighted_score:.4f}")
                print(f"  Category: {ticket['category']} ({category_indicator})")
                print(f"  Ticket ID: {ticket['ticket_id']}")
                print(f"  Subject: {ticket['subject']}")
                print(f"  Status: {ticket['status']}, Priority: {ticket['priority']}")
        
        # Step 4: Recommendation
        if verbose:
            print(f"\n{'='*70}")
            print("WEIGHTED SIMILARITY INSIGHTS")
            print(f"{'='*70}")
            
            if is_duplicate:
                print(f"\n⚠️  DUPLICATE DETECTED (Weighted Score >= {self.duplicate_threshold*100:.0f}%)")
                top_result = similar_tickets[0]
                print(f"\nCategory Match Bonus Applied: {'Yes' if top_result['category_match'] else 'No'}")
                print(f"This ensures duplicates within the same category are prioritized.")
            else:
                print(f"\n✓ NEW ISSUE (No high-similarity duplicates found)")
                same_category_count = sum(1 for r in similar_tickets if r['category_match'])
                print(f"\nSimilar tickets in same category: {same_category_count}/{top_n}")
        
        return {
            'is_duplicate': is_duplicate,
            'highest_weighted_score': similar_tickets[0]['weighted_score'],
            'highest_raw_similarity': similar_tickets[0]['raw_similarity'],
            'similar_tickets': results_list,
            'weighting_applied': True,
            'predicted_category': predicted_category,
            'explainability': {
                'same_category_weight': self.SAME_CATEGORY_WEIGHT,
                'different_category_weight': self.DIFFERENT_CATEGORY_WEIGHT,
                'duplicate_threshold': self.duplicate_threshold,
                'category_matches': sum(1 for r in similar_tickets if r['category_match'])
            }
        }


def main():
    """Main execution function with test scenarios."""
    print("="*70)
    print("MODEL 1 ENHANCED: CATEGORY-WEIGHTED SIMILARITY")
    print("="*70)
    
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    embeddings_path = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
    
    # Initialize matcher
    matcher = CategoryWeightedSimilarityMatcher(embeddings_path)
    
    # Test Scenario 1: Network issue with correct category prediction
    print("\n\n" + "="*70)
    print("TEST 1: Network Issue - Correct Category Prediction")
    print("="*70)
    
    result1 = matcher.analyze_new_ticket_weighted(
        predicted_category="Network",
        subject="Cannot connect to VPN from home",
        description="Getting authentication errors when trying to connect to company VPN. Tried resetting password but still failing.",
        top_n=3
    )
    
    # Test Scenario 2: Hardware issue with incorrect category prediction
    print("\n\n" + "="*70)
    print("TEST 2: Hardware Issue - Wrong Category Predicted")
    print("="*70)
    
    result2 = matcher.analyze_new_ticket_weighted(
        predicted_category="Software",  # Wrong prediction
        subject="Laptop keyboard not working",
        description="Several keys on my laptop keyboard stopped working after spilling coffee.",
        top_n=3
    )
    
    print("\n\n" + "="*70)
    print("COMPARISON: Weighted vs Unweighted Impact")
    print("="*70)
    print("\nTest 1 (Correct Category):")
    print(f"  Top match weighted score: {result1['highest_weighted_score']:.4f}")
    print(f"  Top match raw similarity: {result1['highest_raw_similarity']:.4f}")
    print(f"  Boost from correct category: {(result1['highest_weighted_score'] / result1['highest_raw_similarity'] - 1) * 100:.1f}%")
    
    print("\nTest 2 (Wrong Category):")
    print(f"  Top match weighted score: {result2['highest_weighted_score']:.4f}")
    print(f"  Top match raw similarity: {result2['highest_raw_similarity']:.4f}")
    print(f"  Penalty from wrong category: {(1 - result2['highest_weighted_score'] / result2['highest_raw_similarity']) * 100:.1f}%")
    
    print(f"\n\n{'='*70}")
    print("✓ CATEGORY-WEIGHTED SIMILARITY TESTING COMPLETED")
    print(f"{'='*70}")
    print(f"\nKey Benefits:")
    print(f"  - Same-category matches get priority (weight={matcher.SAME_CATEGORY_WEIGHT})")
    print(f"  - Cross-category matches still visible (weight={matcher.DIFFERENT_CATEGORY_WEIGHT})")
    print(f"  - Fully deterministic and explainable")
    print(f"  - No hard filtering - all historical tickets considered")


if __name__ == "__main__":
    main()
