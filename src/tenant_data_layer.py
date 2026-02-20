"""
Multi-Tenant Data Access Layer
================================
Handles tenant isolation for the SaaS platform.

CRITICAL PRINCIPLE:
- All data access MUST be scoped by tenant_id
- NO cross-tenant queries allowed
- Model 1 remains unchanged - it just processes whatever data is passed to it
- Tenant isolation happens at the DATA layer, not the MODEL layer

Architecture:
- Tenant = Company using the SaaS platform
- Each tenant has isolated:
  • Ticket data
  • Embeddings
  • Knowledge base
  • Historical context
- Shared:
  • AI models (Model 1, 2, 3, 4)
  • Infrastructure
  • Codebase

This enables:
- One codebase serving multiple companies
- Data privacy and compliance
- Independent learning per tenant
- Scalable SaaS deployment
"""

import os
import pandas as pd
import pickle
from datetime import datetime
from typing import Optional, Dict, List, Any


class TenantResolver:
    """
    Resolves tenant_id from request context.
    
    In production, this would:
    - Extract tenant_id from JWT token
    - Or from authenticated user's organization
    - Or from API key mapping
    - Or from subdomain (tenant1.helpdesk.com)
    
    For demo/development:
    - Explicitly pass tenant_id to all operations
    """
    
    @staticmethod
    def validate_tenant_id(tenant_id: str) -> bool:
        """
        Validate that tenant_id is valid.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        if not tenant_id or not isinstance(tenant_id, str):
            raise ValueError("tenant_id must be a non-empty string")
        
        if len(tenant_id) < 3 or len(tenant_id) > 50:
            raise ValueError("tenant_id must be 3-50 characters")
        
        # In production, check against tenant database
        # For now, accept any valid string
        return True
    
    @staticmethod
    def get_tenant_from_request(request_headers: Dict[str, str]) -> str:
        """
        Extract tenant_id from HTTP request headers.
        
        Production implementation examples:
        - X-Tenant-ID header
        - JWT token claims
        - API key lookup
        - Subdomain parsing
        
        Args:
            request_headers: HTTP request headers
            
        Returns:
            tenant_id string
        """
        # Example: Check X-Tenant-ID header
        tenant_id = request_headers.get('X-Tenant-ID')
        
        if not tenant_id:
            raise ValueError("Missing tenant_id in request. Cannot proceed.")
        
        TenantResolver.validate_tenant_id(tenant_id)
        return tenant_id


class TenantDataLayer:
    """
    Tenant-aware data access layer for the SaaS platform.
    
    ALL data operations are scoped by tenant_id.
    This ensures complete data isolation between tenants.
    """
    
    def __init__(self, base_data_dir: str = 'data'):
        """
        Initialize the tenant data layer.
        
        Args:
            base_data_dir: Base directory for all tenant data
        """
        self.base_data_dir = base_data_dir
        
        # SECURITY: Ensure data directory structure exists
        os.makedirs(base_data_dir, exist_ok=True)
    
    def _get_tenant_dir(self, tenant_id: str) -> str:
        """
        Get the isolated data directory for a tenant.
        
        Directory structure:
        data/
        ├── tenants/
        │   ├── acme_corp/          # Tenant 1
        │   │   ├── tickets.csv
        │   │   └── embeddings.pkl
        │   ├── globex_inc/         # Tenant 2
        │   │   ├── tickets.csv
        │   │   └── embeddings.pkl
        │   └── initech/            # Tenant 3
        │       ├── tickets.csv
        │       └── embeddings.pkl
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Path to tenant's data directory
        """
        TenantResolver.validate_tenant_id(tenant_id)
        
        # SECURITY: Sanitize tenant_id to prevent directory traversal
        safe_tenant_id = tenant_id.replace('/', '_').replace('\\', '_').replace('..', '_')
        
        tenant_dir = os.path.join(self.base_data_dir, 'tenants', safe_tenant_id)
        os.makedirs(tenant_dir, exist_ok=True)
        
        return tenant_dir
    
    def load_tickets(self, tenant_id: str) -> pd.DataFrame:
        """
        Load tickets for a specific tenant ONLY.
        
        CRITICAL: This function enforces tenant isolation.
        It NEVER returns tickets from other tenants.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            DataFrame containing ONLY this tenant's tickets
        """
        tenant_dir = self._get_tenant_dir(tenant_id)
        tickets_path = os.path.join(tenant_dir, 'tickets.csv')
        
        if not os.path.exists(tickets_path):
            print(f"⚠️  No tickets found for tenant '{tenant_id}'. Creating empty dataset.")
            # Return empty DataFrame with expected schema
            return pd.DataFrame(columns=[
                'ticket_id', 'tenant_id', 'category', 'subject', 
                'description', 'status', 'priority'
            ])
        
        # Load tickets
        tickets_df = pd.read_csv(tickets_path)
        
        # SECURITY: Double-check all tickets belong to this tenant
        if 'tenant_id' in tickets_df.columns:
            if not (tickets_df['tenant_id'] == tenant_id).all():
                raise ValueError(
                    f"SECURITY VIOLATION: Ticket file for tenant '{tenant_id}' "
                    f"contains tickets from other tenants!"
                )
        else:
            # Legacy data without tenant_id - add it
            tickets_df['tenant_id'] = tenant_id
        
        print(f"✓ Loaded {len(tickets_df)} tickets for tenant '{tenant_id}'")
        return tickets_df
    
    def save_tickets(self, tenant_id: str, tickets_df: pd.DataFrame) -> None:
        """
        Save tickets for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            tickets_df: DataFrame containing tickets
        """
        tenant_dir = self._get_tenant_dir(tenant_id)
        tickets_path = os.path.join(tenant_dir, 'tickets.csv')
        
        # SECURITY: Ensure all tickets have correct tenant_id
        tickets_df['tenant_id'] = tenant_id
        
        # Save to tenant-specific directory
        tickets_df.to_csv(tickets_path, index=False)
        print(f"✓ Saved {len(tickets_df)} tickets for tenant '{tenant_id}'")
    
    def load_embeddings(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Load embeddings for a specific tenant ONLY.
        
        CRITICAL: This function enforces tenant isolation.
        It NEVER returns embeddings from other tenants.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary containing embeddings and metadata, or None if not found
        """
        tenant_dir = self._get_tenant_dir(tenant_id)
        embeddings_path = os.path.join(tenant_dir, 'embeddings.pkl')
        
        if not os.path.exists(embeddings_path):
            print(f"⚠️  No embeddings found for tenant '{tenant_id}'.")
            return None
        
        # Load embeddings
        with open(embeddings_path, 'rb') as f:
            embedding_data = pickle.load(f)
        
        # SECURITY: Verify embeddings belong to this tenant
        if 'tenant_id' in embedding_data:
            if embedding_data['tenant_id'] != tenant_id:
                raise ValueError(
                    f"SECURITY VIOLATION: Embedding file for tenant '{tenant_id}' "
                    f"contains embeddings from tenant '{embedding_data['tenant_id']}'!"
                )
        else:
            # Legacy data - add tenant_id
            embedding_data['tenant_id'] = tenant_id
        
        print(f"✓ Loaded embeddings for tenant '{tenant_id}' "
              f"({len(embedding_data['embeddings'])} tickets)")
        
        return embedding_data
    
    def save_embeddings(
        self, 
        tenant_id: str, 
        embeddings, 
        tickets_df: pd.DataFrame, 
        model_name: str, 
        embedding_dim: int
    ) -> None:
        """
        Save embeddings for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            embeddings: Numpy array of embeddings
            tickets_df: DataFrame containing ticket data
            model_name: Name of the model used
            embedding_dim: Dimension of embeddings
        """
        tenant_dir = self._get_tenant_dir(tenant_id)
        embeddings_path = os.path.join(tenant_dir, 'embeddings.pkl')
        
        # Package embeddings with tenant metadata
        embedding_data = {
            'tenant_id': tenant_id,  # CRITICAL: Mark ownership
            'embeddings': embeddings,
            'tickets': tickets_df.to_dict('records'),
            'ticket_ids': tickets_df['ticket_id'].tolist(),
            'model_name': model_name,
            'embedding_dim': embedding_dim,
            'timestamp': datetime.now().isoformat()
        }
        
        # PERSISTENCE NOTE (from Model 1 hardening):
        # Pickle storage is for LOCAL/DEMO use only.
        # In production SaaS, use:
        #   - Vector database with tenant_id indexing (Pinecone, Weaviate)
        #   - PostgreSQL with pgvector + tenant_id column
        #   - Elasticsearch with tenant_id filtering
        # This ensures:
        #   - Scalable multi-tenant storage
        #   - Fast tenant-scoped queries
        #   - Production-grade isolation
        
        with open(embeddings_path, 'wb') as f:
            pickle.dump(embedding_data, f)
        
        file_size_mb = os.path.getsize(embeddings_path) / (1024 * 1024)
        print(f"✓ Saved embeddings for tenant '{tenant_id}' ({file_size_mb:.2f} MB)")
    
    def list_tenants(self) -> List[str]:
        """
        List all tenants in the system.
        
        Returns:
            List of tenant_id strings
        """
        tenants_dir = os.path.join(self.base_data_dir, 'tenants')
        
        if not os.path.exists(tenants_dir):
            return []
        
        # List all directories in tenants/ folder
        tenants = [
            d for d in os.listdir(tenants_dir) 
            if os.path.isdir(os.path.join(tenants_dir, d))
        ]
        
        return sorted(tenants)
    
    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary with tenant statistics
        """
        tickets_df = self.load_tickets(tenant_id)
        embeddings = self.load_embeddings(tenant_id)
        
        stats = {
            'tenant_id': tenant_id,
            'ticket_count': len(tickets_df),
            'has_embeddings': embeddings is not None,
            'embedding_count': len(embeddings['embeddings']) if embeddings else 0,
            'categories': tickets_df['category'].unique().tolist() if len(tickets_df) > 0 else [],
            'last_updated': embeddings.get('timestamp') if embeddings else None
        }
        
        return stats


class TenantAwareEmbeddingService:
    """
    Wrapper around Model 1 that enforces tenant isolation.
    
    CRITICAL DESIGN:
    - This class DOES NOT modify Model 1
    - It only ensures tenant-scoped data is passed to Model 1
    - Model 1 remains frozen and unchanged
    """
    
    def __init__(self, data_layer: TenantDataLayer):
        """
        Initialize the tenant-aware embedding service.
        
        Args:
            data_layer: TenantDataLayer instance
        """
        self.data_layer = data_layer
        
        # Import Model 1 (unchanged)
        from model1_embeddings import TicketEmbeddingGenerator
        self.generator = TicketEmbeddingGenerator()
    
    def generate_embeddings_for_tenant(self, tenant_id: str) -> None:
        """
        Generate embeddings for a specific tenant's tickets.
        
        Model 1 DOES NOT KNOW about tenants.
        This function simply:
        1. Loads tenant-specific tickets
        2. Passes them to Model 1
        3. Saves embeddings to tenant-specific storage
        
        Args:
            tenant_id: Tenant identifier
        """
        print(f"\n{'='*70}")
        print(f"GENERATING EMBEDDINGS FOR TENANT: {tenant_id}")
        print(f"{'='*70}")
        
        # Load ONLY this tenant's tickets
        tickets_df = self.data_layer.load_tickets(tenant_id)
        
        if len(tickets_df) == 0:
            print(f"⚠️  No tickets for tenant '{tenant_id}'. Nothing to embed.")
            return
        
        # Model 1 generates embeddings (unchanged code)
        # It doesn't know or care about tenant_id
        embeddings = self.generator.generate_embeddings(tickets_df)
        
        # Verify embeddings
        self.generator.verify_embeddings(embeddings, tickets_df)
        
        # Save to tenant-specific storage
        self.data_layer.save_embeddings(
            tenant_id=tenant_id,
            embeddings=embeddings,
            tickets_df=tickets_df,
            model_name=self.generator.model_name,
            embedding_dim=embeddings.shape[1]
        )
        
        print(f"✓ Embeddings generated for tenant '{tenant_id}'")


class TenantAwareSimilarityService:
    """
    Wrapper around Model 1 similarity matcher that enforces tenant isolation.
    
    CRITICAL DESIGN:
    - This class DOES NOT modify Model 1
    - It only ensures tenant-scoped embeddings are used
    - Model 1 remains frozen and unchanged
    """
    
    def __init__(self, data_layer: TenantDataLayer):
        """
        Initialize the tenant-aware similarity service.
        
        Args:
            data_layer: TenantDataLayer instance
        """
        self.data_layer = data_layer
        
        # Import Model 1 (unchanged)
        from sentence_transformers import SentenceTransformer
        from model1_embeddings import TicketEmbeddingGenerator
        
        self.generator = TicketEmbeddingGenerator()
    
    def find_similar_tickets_for_tenant(
        self, 
        tenant_id: str, 
        subject: str, 
        description: str, 
        category: Optional[str] = None, 
        top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Find similar tickets within a specific tenant's data ONLY.
        
        CRITICAL: This function ensures NO cross-tenant data leakage.
        - Only loads embeddings for the specified tenant
        - Model 1 compares against tenant-specific embeddings only
        - Results contain ONLY tickets from this tenant
        
        Args:
            tenant_id: Tenant identifier
            subject: New ticket subject
            description: New ticket description
            category: Optional category
            top_n: Number of similar tickets to return
            
        Returns:
            Dictionary with analysis results
        """
        print(f"\n{'='*70}")
        print(f"SIMILARITY SEARCH FOR TENANT: {tenant_id}")
        print(f"{'='*70}")
        
        # Load ONLY this tenant's embeddings
        embedding_data = self.data_layer.load_embeddings(tenant_id)
        
        if not embedding_data:
            return {
                'tenant_id': tenant_id,
                'is_duplicate': False,
                'highest_similarity': 0.0,
                'similar_tickets': [],
                'error': 'No historical tickets for this tenant'
            }
        
        # Generate embedding for new ticket using Model 1 (unchanged)
        new_embedding = self.generator.model.encode(
            f"[{category}] {subject}. {description}" if category 
            else f"{subject}. {description}",
            convert_to_numpy=True
        )
        
        # Use Model 1's similarity logic (unchanged)
        # It compares against the tenant-specific embeddings we loaded
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        new_embedding_reshaped = new_embedding.reshape(1, -1)
        similarities = cosine_similarity(
            new_embedding_reshaped, 
            embedding_data['embeddings']
        )[0]
        
        # Get top N
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            ticket = embedding_data['tickets'][idx]
            score = similarities[idx]
            results.append((ticket, score))
        
        is_duplicate = results[0][1] >= 0.80 if results else False
        
        print(f"✓ Found {len(results)} similar tickets for tenant '{tenant_id}'")
        if is_duplicate:
            print(f"  ⚠️  DUPLICATE DETECTED (similarity: {results[0][1]:.4f})")
        
        return {
            'tenant_id': tenant_id,
            'is_duplicate': is_duplicate,
            'highest_similarity': results[0][1] if results else 0.0,
            'similar_tickets': results,
            'recommended_category': results[0][0]['category'] if results else None
        }


# Export tenant-aware services
__all__ = [
    'TenantResolver',
    'TenantDataLayer',
    'TenantAwareEmbeddingService',
    'TenantAwareSimilarityService'
]
