"""
Model 1: Ticket Understanding - Similarity Matcher
===================================================
Compares new incoming tickets with historical tickets using cosine similarity.
Detects repeated issues and finds similar past tickets.

Architecture:
- Input: New ticket text
- Process: Convert to embedding → Compute cosine similarity with all past tickets
- Output: Top-N similar tickets with similarity scores
- Threshold: >= 0.80 indicates likely duplicate/repeated issue

Enterprise Benefits:
- Immediate duplicate detection
- Enables intelligent routing based on similar past tickets
- Supports self-service by showing similar resolved tickets
- No machine learning training required
"""

import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity


class TicketSimilarityMatcher:
    """Finds similar tickets using cosine similarity of embeddings."""
    
    def __init__(self, embeddings_path='data/ticket_embeddings.pkl'):
        """
        Initialize the similarity matcher.
        
        Args:
            embeddings_path: Path to the saved embeddings file
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing Ticket Similarity Matcher")
        
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
        
        # Load the same model for encoding new tickets
        print(f"Loading sentence transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"✓ Model ready for new ticket encoding")
        
        # Similarity threshold for duplicate detection
        self.duplicate_threshold = 0.80
    
    def encode_new_ticket(self, subject, description, category=None):
        """
        Convert a new ticket into an embedding.
        
        MODEL 1 INPUT CONTRACT:
        - Accepts ONLY text fields: subject (required), description (required), category (optional)
        - Category must be OPTIONAL - new tickets may not have category assigned yet
        - Explicitly REJECTS/IGNORES: priority, urgency, source_system, routing_hint, etc.
        - Downstream models (2-4) handle metadata-based decisions
        
        Args:
            subject: Ticket subject (required)
            description: Ticket description (required)
            category: Optional category (default: None)
            
        Returns:
            Embedding vector as numpy array
        """
        # Clean inputs (text only, no metadata)
        subject = str(subject).strip()
        description = str(description).strip()
        
        # Category is OPTIONAL: only include if provided and non-empty
        # New tickets use "Subject. Description" format (no category)
        # This matches how historical tickets without category are processed
        if category and str(category).strip() and str(category).lower() not in ['nan', 'none', '']:
            ticket_text = f"[{str(category).strip()}] {subject}. {description}"
        else:
            ticket_text = f"{subject}. {description}"
        
        # Generate embedding
        embedding = self.model.encode(ticket_text, convert_to_numpy=True)
        return embedding
    
    def find_similar_tickets(self, new_ticket_embedding, top_n=3):
        """
        Find most similar historical tickets.
        
        Args:
            new_ticket_embedding: Embedding of the new ticket
            top_n: Number of similar tickets to return
            
        Returns:
            List of (ticket, similarity_score) tuples
        """
        # Reshape for sklearn cosine_similarity
        new_embedding_reshaped = new_ticket_embedding.reshape(1, -1)
        
        # Compute cosine similarity with all historical tickets
        similarities = cosine_similarity(new_embedding_reshaped, self.embeddings)[0]
        
        # Get indices of top N similar tickets
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        # Prepare results
        results = []
        for idx in top_indices:
            ticket = self.tickets[idx]
            score = similarities[idx]
            results.append((ticket, score))
        
        return results
    
    def check_duplicate(self, similarity_score):
        """
        Check if similarity score indicates a duplicate/repeated issue.
        
        Args:
            similarity_score: Cosine similarity score (0-1)
            
        Returns:
            Boolean indicating if this is likely a duplicate
        """
        return similarity_score >= self.duplicate_threshold
    
    def analyze_new_ticket(self, subject, description, category=None, top_n=3):
        """
        Complete analysis pipeline for a new ticket.
        
        Args:
            subject: Ticket subject
            description: Ticket description
            category: Optional category
            top_n: Number of similar tickets to show
            
        Returns:
            Dictionary with analysis results
        """
        print(f"\n{'='*70}")
        print("NEW TICKET ANALYSIS")
        print(f"{'='*70}")
        
        # Display new ticket
        print(f"\n📥 Incoming Ticket:")
        if category:
            print(f"  Category: {category}")
        print(f"  Subject: {subject}")
        print(f"  Description: {description}")
        
        # Step 1: Generate embedding
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating embedding for new ticket...")
        new_embedding = self.encode_new_ticket(subject, description, category)
        print(f"✓ Embedding generated (dimension: {len(new_embedding)})")
        
        # Step 2: Find similar tickets
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Computing similarity with {len(self.tickets)} historical tickets...")
        similar_tickets = self.find_similar_tickets(new_embedding, top_n)
        print(f"✓ Top {top_n} similar tickets found")
        
        # Step 3: Display results
        print(f"\n{'='*70}")
        print(f"TOP {top_n} SIMILAR PAST TICKETS")
        print(f"{'='*70}")
        
        is_duplicate = False
        for i, (ticket, score) in enumerate(similar_tickets, 1):
            is_dup = self.check_duplicate(score)
            if i == 1 and is_dup:
                is_duplicate = True
            
            duplicate_marker = "⚠️  POSSIBLE DUPLICATE" if is_dup else ""
            
            print(f"\n#{i} - Similarity: {score:.4f} ({score*100:.2f}%) {duplicate_marker}")
            print(f"  Ticket ID: {ticket['ticket_id']}")
            print(f"  Category: {ticket['category']}")
            print(f"  Subject: {ticket['subject']}")
            print(f"  Description: {ticket['description'][:100]}...")
            print(f"  Status: {ticket['status']}")
            print(f"  Priority: {ticket['priority']}")
        
        # Step 4: Provide recommendation
        print(f"\n{'='*70}")
        print("RECOMMENDATION")
        print(f"{'='*70}")
        
        if is_duplicate:
            most_similar = similar_tickets[0][0]
            print(f"\n⚠️  DUPLICATE DETECTED (Similarity >= {self.duplicate_threshold*100:.0f}%)")
            print(f"\nSuggested Actions:")
            print(f"  1. Check if ticket {most_similar['ticket_id']} addresses the same issue")
            if most_similar['status'] == 'Resolved':
                print(f"  2. Reference solution from {most_similar['ticket_id']} (Status: Resolved)")
                print(f"  3. Consider auto-resolving with existing solution")
            else:
                print(f"  2. Link to existing ticket {most_similar['ticket_id']} (Status: {most_similar['status']})")
                print(f"  3. Notify user about ongoing investigation")
            print(f"  4. Route to same team/agent who handled {most_similar['ticket_id']}")
        else:
            print(f"\n✓ NEW ISSUE (No high-similarity duplicates found)")
            print(f"\nSuggested Actions:")
            most_similar = similar_tickets[0][0]
            print(f"  1. Route to {most_similar['category']} team (based on similarity)")
            print(f"  2. Reference similar ticket {most_similar['ticket_id']} for context")
            print(f"  3. Standard triage and assignment process")
        
        print(f"\n{'='*70}")
        
        return {
            'is_duplicate': is_duplicate,
            'highest_similarity': similar_tickets[0][1],
            'similar_tickets': similar_tickets,
            'recommended_category': similar_tickets[0][0]['category']
        }


def main():
    """Main execution function with test scenarios."""
    print("="*70)
    print("MODEL 1: TICKET UNDERSTANDING - SIMILARITY MATCHING")
    print("="*70)
    
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    embeddings_path = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
    
    # Initialize matcher
    matcher = TicketSimilarityMatcher(embeddings_path)
    
    # Test Scenario 1: Clear duplicate (VPN issue similar to T001)
    print("\n\n" + "="*70)
    print("TEST SCENARIO 1: Likely Duplicate Ticket")
    print("="*70)
    
    matcher.analyze_new_ticket(
        category="Network",
        subject="VPN authentication error",
        description="Cannot connect to VPN from home office. Keep getting authentication failure message. Tried rebooting my laptop.",
        top_n=3
    )
    
    # Test Scenario 2: Similar but not duplicate (Payment issue similar but different)
    print("\n\n" + "="*70)
    print("TEST SCENARIO 2: Similar but Different Issue")
    print("="*70)
    
    matcher.analyze_new_ticket(
        category="Payment",
        subject="Payment confirmation email not received",
        description="Payment went through successfully but customer not receiving confirmation email. Payment shows in system.",
        top_n=3
    )
    
    # Test Scenario 3: New unique issue
    print("\n\n" + "="*70)
    print("TEST SCENARIO 3: New Unique Issue")
    print("="*70)
    
    matcher.analyze_new_ticket(
        category="Messaging",
        subject="Voice call feature not available",
        description="The voice call button is missing from our messaging interface. Only seeing video call and chat options.",
        top_n=3
    )
    
    print(f"\n\n{'='*70}")
    print("✓ SIMILARITY MATCHING TESTING COMPLETED")
    print(f"{'='*70}")
    print(f"\nKey Observations:")
    print(f"  - Duplicate detection threshold: {matcher.duplicate_threshold*100:.0f}%")
    print(f"  - Embeddings enable semantic matching beyond keyword matching")
    print(f"  - Ready for integration into helpdesk workflow")


if __name__ == "__main__":
    main()
