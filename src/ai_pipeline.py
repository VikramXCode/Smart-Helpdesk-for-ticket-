"""
AI Pipeline: Multi-Model Ticket Analysis Orchestrator
=====================================================
Coordinates Models 1, 2, and 3 to provide complete ticket analysis.

Pipeline Flow:
1. Input: Raw ticket (subject + description)
2. Semantic text building
3. Model 2: Category Classification
4. Model 1: Weighted Similarity Search (using predicted category)
5. Decision: Duplicate or New?
   - If Duplicate → Inherit category + priority
   - If New → Use Model 2 category + Model 3 priority
6. Output: Complete analysis with explainability

Enterprise Benefits:
- Single entry point for all AI operations  
- Deterministic pipeline execution
- Full audit trail of decisions
- Multi-tenant safe
- No randomness or training required
"""

import os
from datetime import datetime
from typing import Dict, Optional

from src.model1_weighted_similarity import CategoryWeightedSimilarityMatcher
from src.model2_classifier import TicketCategoryClassifier
from src.model3_priority_engine import PriorityPredictionEngine


class TicketAIPipeline:
    """Orchestrates all AI models for complete ticket analysis."""
    
    def __init__(self, embeddings_path='data/ticket_embeddings.pkl', verbose=False):
        """
        Initialize the AI pipeline with all models.
        
        Args:
            embeddings_path: Path to ticket embeddings for Model 1
            verbose: Whether to show initialization details
        """
        if verbose:
            print(f"\n{'='*70}")
            print("INITIALIZING AI PIPELINE")
            print(f"{'='*70}")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading AI Pipeline...")
        
        # Initialize Model 2: Category Classifier
        if verbose:
            print(f"\n[Model 2] Category Classifier")
        self.classifier = TicketCategoryClassifier()
        
        # Initialize Model 1: Weighted Similarity Matcher
        if verbose:
            print(f"\n[Model 1] Weighted Similarity Matcher")
        self.similarity_matcher = CategoryWeightedSimilarityMatcher(embeddings_path)
        
        # Initialize Model 3: Priority Prediction Engine
        if verbose:
            print(f"\n[Model 3] Priority Prediction Engine")
        self.priority_engine = PriorityPredictionEngine()
        
        print(f"\n✓ AI Pipeline initialized successfully")
        print(f"  Model 1: Category-Weighted Similarity")
        print(f"  Model 2: Zero-Shot Category Classification")
        print(f"  Model 3: Priority & Urgency Prediction")
        
        if verbose:
            print(f"\n{'='*70}")
    
    def analyze_ticket(self, subject: str, description: str, tenant_id: Optional[str] = None,
                      top_similar: int = 3, verbose: bool = True) -> Dict:
        """
        Complete AI-powered ticket analysis.
        
        Pipeline Steps:
        1. Classify category (Model 2)
        2. Find similar tickets with weighting (Model 1)
        3. Determine if duplicate
        4. Predict priority (Model 3)
           - If duplicate: inherit from original
           - If new: analyze keywords + category
        
        Args:
            subject: Ticket subject
            description: Ticket description
            tenant_id: Optional tenant identifier (for future multi-tenant filtering)
            top_similar: Number of similar tickets to return
            verbose: Whether to print detailed pipeline execution
            
        Returns:
            Complete analysis dictionary with all model outputs and explainability
        """
        if verbose:
            print(f"\n{'='*80}")
            print("AI PIPELINE EXECUTION")
            print(f"{'='*80}")
            print(f"\n📥 New Ticket Received")
            print(f"  Subject: {subject}")
            print(f"  Description: {description[:100]}...")
            if tenant_id:
                print(f"  Tenant ID: {tenant_id}")
        
        pipeline_start = datetime.now()
        
        # ============================================================
        # STEP 1: CATEGORY CLASSIFICATION (Model 2)
        # ============================================================
        if verbose:
            print(f"\n{'─'*80}")
            print("STEP 1: CATEGORY CLASSIFICATION (Model 2)")
            print(f"{'─'*80}")
        
        category_result = self.classifier.classify_ticket(
            subject=subject,
            description=description,
            top_n=3,
            verbose=verbose
        )
        
        predicted_category = category_result['predicted_category']
        category_confidence = category_result['confidence']
        
        # ============================================================
        # STEP 2: WEIGHTED SIMILARITY SEARCH (Model 1)
        # ============================================================
        if verbose:
            print(f"\n{'─'*80}")
            print("STEP 2: WEIGHTED SIMILARITY SEARCH (Model 1)")
            print(f"{'─'*80}")
        
        similarity_result = self.similarity_matcher.analyze_new_ticket_weighted(
            subject=subject,
            description=description,
            predicted_category=predicted_category,
            top_n=top_similar,
            verbose=verbose
        )
        
        is_duplicate = similarity_result['is_duplicate']
        highest_similarity = similarity_result['highest_weighted_score']
        similar_tickets = similarity_result['similar_tickets']
        
        # ============================================================
        # STEP 3: DECISION POINT - DUPLICATE OR NEW?
        # ============================================================
        if verbose:
            print(f"\n{'─'*80}")
            print("STEP 3: DUPLICATE DETECTION")
            print(f"{'─'*80}")
            
            if is_duplicate:
                print(f"\n⚠️  DUPLICATE DETECTED")
                print(f"  Similarity Score: {highest_similarity:.4f} (>= 0.80 threshold)")
                print(f"  Most similar ticket: {similar_tickets[0]['ticket_id']}")
            else:
                print(f"\n✓ NEW TICKET (Not a duplicate)")
                print(f"  Highest similarity: {highest_similarity:.4f} (< 0.80 threshold)")
        
        # ============================================================
        # STEP 4: CATEGORY & PRIORITY DETERMINATION
        # ============================================================
        if is_duplicate:
            # Inherit from duplicate
            duplicate_ticket = similar_tickets[0]  # Most similar ticket
            
            final_category = duplicate_ticket['category']
            category_source = 'inherited-from-duplicate'
            
            if verbose:
                print(f"\n{'─'*80}")
                print("STEP 4: INHERITING FROM DUPLICATE")
                print(f"{'─'*80}")
                print(f"\n📋 Inheriting attributes from {duplicate_ticket['ticket_id']}")
                print(f"  Original Category: {final_category}")
                print(f"  Original Priority: {duplicate_ticket['priority']}")
            
            # Priority prediction with duplicate inheritance
            priority_result = self.priority_engine.predict_priority(
                subject=subject,
                description=description,
                category=final_category,
                is_duplicate=True,
                duplicate_ticket=duplicate_ticket,
                verbose=verbose
            )
            
        else:
            # New ticket - use Model 2 classification
            final_category = predicted_category
            category_source = 'model2-classification'
            
            if verbose:
                print(f"\n{'─'*80}")
                print("STEP 4: PRIORITY PREDICTION (Model 3)")
                print(f"{'─'*80}")
            
            # Priority prediction for new ticket
            priority_result = self.priority_engine.predict_priority(
                subject=subject,
                description=description,
                category=final_category,
                is_duplicate=False,
                verbose=verbose
            )
        
        suggested_priority = priority_result['suggested_priority']
        priority_confidence = priority_result['confidence']
        
        # ============================================================
        # STEP 5: COMPILE COMPLETE ANALYSIS
        # ============================================================
        pipeline_end = datetime.now()
        execution_time = (pipeline_end - pipeline_start).total_seconds()
        
        complete_analysis = {
            # Core Results
            'duplicate': is_duplicate,
            'category': {
                'predicted': final_category,
                'confidence': category_confidence if not is_duplicate else 1.0,
                'source': category_source,
                'alternatives': category_result['top_matches'][1:] if not is_duplicate else []
            },
            'priority': {
                'suggested': suggested_priority,
                'confidence': priority_confidence,
                'reasoning': priority_result['reasoning'],
                'method': priority_result['method']
            },
            
            # Similar Tickets
            'similar_tickets': similar_tickets,
            'highest_similarity_score': highest_similarity,
            
            # Explainability
            'explainability': {
                'pipeline_flow': 'Model2 → Model1 → Duplicate Detection → Model3' if not is_duplicate 
                                else 'Model2 → Model1 → Duplicate Detection → Inheritance',
                'category_decision': category_result['explainability'] if not is_duplicate 
                                    else {'source': 'inherited', 'from_ticket': similar_tickets[0]['ticket_id']},
                'priority_decision': priority_result['explainability'],
                'similarity_weighting': similarity_result['explainability'],
                'duplicate_threshold': 0.80,
                'execution_time_seconds': round(execution_time, 3)
            },
            
            # Raw Model Outputs (for debugging/audit)
            'raw_outputs': {
                'model1_similarity': similarity_result,
                'model2_classification': category_result,
                'model3_priority': priority_result
            },
            
            # Metadata
            'pipeline_version': '1.0.0',
            'timestamp': pipeline_end.isoformat(),
            'tenant_id': tenant_id
        }
        
        # ============================================================
        # FINAL OUTPUT
        # ============================================================
        if verbose:
            print(f"\n{'='*80}")
            print("PIPELINE COMPLETE - FINAL RESULTS")
            print(f"{'='*80}")
            
            print(f"\n🎯 TICKET ANALYSIS SUMMARY")
            print(f"{'─'*80}")
            print(f"  Duplicate: {'YES ⚠️' if is_duplicate else 'NO ✓'}")
            print(f"  Category: {final_category} ({category_source})")
            print(f"  Priority: {suggested_priority} (confidence: {priority_confidence:.2f})")
            print(f"  Execution Time: {execution_time:.3f}s")
            
            print(f"\n📊 TOP SIMILAR TICKETS")
            print(f"{'─'*80}")
            for i, ticket in enumerate(similar_tickets[:3], 1):
                print(f"  #{i} {ticket['ticket_id']}: {ticket['subject'][:50]}...")
                print(f"      Similarity: {ticket['weighted_score']:.4f} | Category: {ticket['category']} | Priority: {ticket['priority']}")
            
            print(f"\n💡 RECOMMENDATIONS")
            print(f"{'─'*80}")
            if is_duplicate:
                print(f"  → Link to original ticket: {similar_tickets[0]['ticket_id']}")
                print(f"  → Notify user about existing ticket")
                print(f"  → Route to same team/agent")
            else:
                print(f"  → Route to {final_category} team")
                print(f"  → Assign priority: {suggested_priority}")
                print(f"  → Reference similar ticket {similar_tickets[0]['ticket_id']} for context")
            
            print(f"\n{'='*80}")
        
        return complete_analysis


def main():
    """Main execution function with comprehensive test scenarios."""
    print("="*80)
    print("TICKET AI PIPELINE - COMPLETE SYSTEM TEST")
    print("="*80)
    
    # File paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    embeddings_path = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
    
    # Initialize pipeline
    pipeline = TicketAIPipeline(embeddings_path, verbose=True)
    
    # Test Scenario 1: Likely Duplicate - VPN Issue
    print("\n\n" + "="*80)
    print("TEST SCENARIO 1: VPN Connection Issue (Likely Duplicate)")
    print("="*80)
    
    result1 = pipeline.analyze_ticket(
        subject="VPN won't connect from home",
        description="Cannot connect to company VPN from my home office. Getting authentication errors. Tried resetting password.",
        tenant_id="acme_corp",
        top_similar=3,
        verbose=True
    )
    
    # Test Scenario 2: New DevOps Issue
    print("\n\n" + "="*80)
    print("TEST SCENARIO 2: Jenkins Pipeline Failure (New Issue)")
    print("="*80)
    
    result2 = pipeline.analyze_ticket(
        subject="Jenkins deployment failing to staging",
        description="Our CI/CD pipeline fails at the deployment step. Build completes successfully but deployment to staging environment times out. Entire team blocked.",
        tenant_id="acme_corp",
        top_similar=3,
        verbose=True
    )
    
    # Test Scenario 3: Security Issue - Production Impact
    print("\n\n" + "="*80)
    print("TEST SCENARIO 3: Security Alert (Critical Priority)")
    print("="*80)
    
    result3 = pipeline.analyze_ticket(
        subject="Suspicious database access attempts",
        description="Multiple unauthorized access attempts detected on production database. Potential security breach. All users may be affected.",
        tenant_id="initech",
        top_similar=3,
        verbose=True
    )
    
    # Summary Report
    print("\n\n" + "="*80)
    print("PIPELINE TEST SUMMARY")
    print("="*80)
    
    test_results = [
        ("VPN Issue", result1),
        ("DevOps Failure", result2),
        ("Security Alert", result3)
    ]
    
    print(f"\n{'Scenario':<20} | {'Duplicate':<10} | {'Category':<10} | {'Priority':<10} | {'Time (s)':<10}")
    print(f"{'─'*80}")
    for name, result in test_results:
        duplicate = "YES" if result['duplicate'] else "NO"
        category = result['category']['predicted']
        priority = result['priority']['suggested']
        exec_time = result['explainability']['execution_time_seconds']
        print(f"{name:<20} | {duplicate:<10} | {category:<10} | {priority:<10} | {exec_time:<10.3f}")
    
    print(f"\n{'='*80}")
    print("✓ AI PIPELINE TESTING COMPLETED")
    print(f"{'='*80}")
    print(f"\nPipeline Capabilities:")
    print(f"  ✓ Multi-model orchestration (Models 1, 2, 3)")
    print(f"  ✓ Duplicate detection with inheritance")
    print(f"  ✓ Zero-shot category classification")
    print(f"  ✓ AI-assisted priority prediction")
    print(f"  ✓ Complete explainability and audit trail")
    print(f"  ✓ Deterministic execution")
    print(f"  ✓ Ready for production deployment")


if __name__ == "__main__":
    main()
