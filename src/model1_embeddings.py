"""
Model 1: Ticket Understanding - Embedding Generator
====================================================
Converts ticket text into vector embeddings using a pre-trained sentence transformer model.
This enables semantic similarity comparison between tickets.

Architecture:
- Pre-trained model: all-MiniLM-L6-v2 (sentence-transformers)
- Input: Ticket subject + description
- Output: 384-dimensional embedding vector
- No training, no fine-tuning - pure inference

Enterprise Benefits:
- Explainable: Uses established sentence embeddings
- Safe: No custom model training required
- Fast: Minimal compute requirements
- Deterministic: Same input always produces same embedding
"""

import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from datetime import datetime


class TicketEmbeddingGenerator:
    """Generates and manages ticket embeddings using sentence transformers."""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the embedding generator.
            
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initializing Ticket Embedding Generator")
        print(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"✓ Model loaded successfully")
        print(f"  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def prepare_ticket_text(self, row):
        """
        Combine ticket fields into a single text for embedding.
        
        MODEL 1 INPUT CONTRACT:
        - Accepts ONLY text fields: subject, description, category (optional)
        - Explicitly IGNORES metadata: priority, urgency, source_system, routing hints
        - Separation of concerns: Model 1 = semantic understanding only
        - Metadata is handled by downstream models (Models 2-4)
        
        Args:
            row: DataFrame row containing ticket data
            
        Returns:
            Combined text string
        """
        # Extract text fields only (ignore all metadata)
        subject = str(row.get('subject', '')).strip()
        description = str(row.get('description', '')).strip()
        category = row.get('category', None)
        
        # Category is OPTIONAL: only include if present and non-empty
        if category and str(category).strip() and str(category).lower() not in ['nan', 'none', '']:
            # Format for historical tickets: [Category] Subject. Description
            return f"[{str(category).strip()}] {subject}. {description}"
        else:
            # Format without category: Subject. Description
            return f"{subject}. {description}"
    
    def generate_embeddings(self, tickets_df):
        """
        Generate embeddings for all tickets in the dataframe.
        
        Args:
            tickets_df: DataFrame containing ticket data
            
        Returns:
            numpy array of embeddings (n_tickets, embedding_dim)
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Generating embeddings for {len(tickets_df)} tickets")
        
        # Prepare ticket texts
        ticket_texts = tickets_df.apply(self.prepare_ticket_text, axis=1).tolist()
        
        # Generate embeddings in batch for efficiency
        embeddings = self.model.encode(
            ticket_texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            batch_size=32
        )
        
        print(f"✓ Embeddings generated successfully")
        print(f"  Shape: {embeddings.shape}")
        print(f"  Embedding dimension: {embeddings.shape[1]}")
        print(f"  Data type: {embeddings.dtype}")
        
        return embeddings
    
    def save_embeddings(self, embeddings, tickets_df, output_path='data/ticket_embeddings.pkl'):
        """
        Save embeddings and associated ticket data to disk.
        
        Args:
            embeddings: numpy array of embeddings
            tickets_df: DataFrame containing ticket data
            output_path: Path to save the embeddings
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Saving embeddings to {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Package embeddings with metadata
        embedding_data = {
            'embeddings': embeddings,
            'tickets': tickets_df.to_dict('records'),
            'ticket_ids': tickets_df['ticket_id'].tolist(),
            'model_name': self.model_name,
            'embedding_dim': embeddings.shape[1],
            'timestamp': datetime.now().isoformat()
        }
        
        # PERSISTENCE NOTE:
        # Pickle storage is for LOCAL/DEMO use only.
        # In production, embeddings should be stored in:
        #   - Vector database (Pinecone, Weaviate, Milvus)
        #   - PostgreSQL with pgvector extension
        #   - Elasticsearch with dense_vector field
        # This abstraction allows easy swap without changing Model 1 logic.
        with open(output_path, 'wb') as f:
            pickle.dump(embedding_data, f)
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ Embeddings saved successfully")
        print(f"  File size: {file_size_mb:.2f} MB")
    
    def verify_embeddings(self, embeddings, tickets_df):
        """
        Perform basic verification on generated embeddings.
        
        Args:
            embeddings: numpy array of embeddings
            tickets_df: DataFrame containing ticket data
        """
        print(f"\n{'='*70}")
        print("EMBEDDING VERIFICATION REPORT")
        print(f"{'='*70}")
        
        print(f"\n📊 Basic Statistics:")
        print(f"  Total tickets processed: {len(tickets_df)}")
        print(f"  Total embeddings generated: {len(embeddings)}")
        print(f"  Embedding dimension: {embeddings.shape[1]}")
        print(f"  Model used: {self.model_name}")
        
        print(f"\n📈 Embedding Statistics:")
        print(f"  Mean of all embeddings: {np.mean(embeddings):.6f}")
        print(f"  Std dev of all embeddings: {np.std(embeddings):.6f}")
        print(f"  Min value: {np.min(embeddings):.6f}")
        print(f"  Max value: {np.max(embeddings):.6f}")
        
        print(f"\n✓ Category Distribution:")
        category_counts = tickets_df['category'].value_counts()
        for category, count in category_counts.items():
            print(f"  {category}: {count} tickets")
        
        print(f"\n✓ Sample Ticket (first entry):")
        first_ticket = tickets_df.iloc[0]
        print(f"  ID: {first_ticket['ticket_id']}")
        print(f"  Category: {first_ticket['category']}")
        print(f"  Subject: {first_ticket['subject']}")
        print(f"  Embedding shape: {embeddings[0].shape}")
        print(f"  Embedding norm: {np.linalg.norm(embeddings[0]):.6f}")
        
        print(f"\n{'='*70}")


def main():
    """Main execution function."""
    print("="*70)
    print("MODEL 1: TICKET UNDERSTANDING - EMBEDDING GENERATION")
    print("="*70)
    
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tickets_path = os.path.join(base_dir, 'data', 'tickets.csv')
    embeddings_output = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
    
    # Step 1: Load tickets
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Loading tickets from {tickets_path}")
    tickets_df = pd.read_csv(tickets_path)
    print(f"✓ Loaded {len(tickets_df)} tickets")
    print(f"  Columns: {list(tickets_df.columns)}")
    
    # Step 2: Initialize embedding generator
    generator = TicketEmbeddingGenerator(model_name='all-MiniLM-L6-v2')
    
    # Step 3: Generate embeddings
    embeddings = generator.generate_embeddings(tickets_df)
    
    # Step 4: Verify embeddings
    generator.verify_embeddings(embeddings, tickets_df)
    
    # Step 5: Save embeddings
    generator.save_embeddings(embeddings, tickets_df, embeddings_output)
    
    print(f"\n{'='*70}")
    print("✓ EMBEDDING GENERATION COMPLETED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"\nNext steps:")
    print(f"  1. Run model1_similarity.py to test similarity matching")
    print(f"  2. Embeddings are ready for integration with routing and classification")


if __name__ == "__main__":
    main()
