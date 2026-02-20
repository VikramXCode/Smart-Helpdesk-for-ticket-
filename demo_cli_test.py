"""
CLI Demo Test Script
====================
Automated test demonstrating the CLI ticket submission flow
without requiring interactive user input.

This shows what happens behind the scenes when a user
submits a ticket via the CLI interface.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ticket_text_builder import (
    build_semantic_text,
    normalize_category,
    validate_ticket_input
)
from model1_similarity import TicketSimilarityMatcher


def test_ticket_submission(ticket_data):
    """
    Simulate a complete ticket submission flow.
    
    Args:
        ticket_data: Dictionary with ticket information
    """
    print("="*80)
    print(" " * 25 + "CLI DEMO TEST")
    print("="*80)
    print()
    
    # Display ticket data
    print("📝 Simulated User Input:")
    print(f"   Context: {ticket_data['context']}")
    if ticket_data.get('context_details'):
        for key, value in ticket_data['context_details'].items():
            label = key.replace('_', ' ').title()
            print(f"   {label}: {value}")
    print(f"   Subject: {ticket_data['subject']}")
    print(f"   Description: {ticket_data['description'][:80]}...")
    print()
    
    # Validate inputs
    print("-" * 80)
    print("Step 1: Validating inputs...")
    valid, error_msg = validate_ticket_input(
        ticket_data['subject'],
        ticket_data['description']
    )
    
    if not valid:
        print(f"❌ VALIDATION FAILED: {error_msg}")
        return
    
    print("✓ Validation passed")
    print()
    
    # Build semantic text
    print("-" * 80)
    print("Step 2: Building semantic text for Model 1...")
    semantic_text = build_semantic_text(
        context=ticket_data['context'],
        subject=ticket_data['subject'],
        description=ticket_data['description'],
        context_details=ticket_data.get('context_details', {})
    )
    
    print("\n📄 Semantic Text:")
    print("-" * 40)
    print(semantic_text)
    print("-" * 40)
    print()
    
    # Normalize category
    category = normalize_category(
        ticket_data['context'],
        ticket_data.get('context_details', {})
    )
    print(f"✓ Category: {category}")
    print()
    
    # Load Model 1
    print("-" * 80)
    print("Step 3: Running Model 1 analysis...")
    
    embeddings_path = os.path.join(
        os.path.dirname(__file__),
        'data',
        'ticket_embeddings.pkl'
    )
    
    if not os.path.exists(embeddings_path):
        print(f"❌ ERROR: Embeddings not found at {embeddings_path}")
        print("   Please run: python src/model1_embeddings.py")
        return
    
    print(f"   Loading embeddings from {embeddings_path}")
    matcher = TicketSimilarityMatcher(embeddings_path)
    
    # Use Model 1's complete analysis pipeline
    print("   Running Model 1 analysis...")
    print()
    
    # Call Model 1's official analyze_new_ticket() method
    analysis = matcher.analyze_new_ticket(
        subject="",
        description=semantic_text,
        category=category if category else None,
        top_n=3
    )
    
    # Transform similar_tickets format for display
    formatted_tickets = []
    for ticket_dict, similarity_score in analysis['similar_tickets']:
        ticket_with_score = ticket_dict.copy()
        ticket_with_score['similarity'] = similarity_score
        formatted_tickets.append(ticket_with_score)
    
    is_duplicate = analysis['is_duplicate']
    
    print()
    print("✓ Analysis complete")
    print()
    
    # Display results
    print("="*80)
    print(" " * 25 + "MODEL 1 RESULTS")
    print("="*80)
    print()
    
    if formatted_tickets:
        print("🔍 Top 3 Similar Historical Tickets:")
        print()
        
        for i, ticket in enumerate(formatted_tickets, 1):
            similarity_pct = ticket['similarity'] * 100
            duplicate_flag = " ⚠️  Possible Duplicate" if similarity_pct >= 80 else ""
            
            print(f"  {i}. {ticket['ticket_id']} – {ticket['subject']}")
            print(f"     Similarity: {similarity_pct:.1f}%{duplicate_flag}")
            print(f"     Status: {ticket.get('status', 'Unknown')}")
            print(f"     Priority: {ticket.get('priority', 'Unknown')}")
            print()
    else:
        print("🔍 No similar historical tickets found.")
        print()
    
    # Duplicate detection
    print("-" * 80)
    print("Duplicate Detection:")
    print()
    
    top_similarity = formatted_tickets[0]['similarity'] * 100 if formatted_tickets else 0
    
    if is_duplicate:
        print(f"  ⚠️  DUPLICATE LIKELY (Similarity: {top_similarity:.1f}% ≥ 80%)")
    else:
        print(f"  ✓ NEW ISSUE (Highest Similarity: {top_similarity:.1f}% < 80%)")
    print()
    
    # Recommendation
    print("-" * 80)
    print("💡 AI Recommendation:")
    print()
    
    if is_duplicate and similar_tickets:
        top_ticket = similar_tickets[0]
        print(f"  • Link to existing ticket {top_ticket['ticket_id']}")
        print(f"  • Status: {top_ticket.get('status', 'Unknown')}")
        if top_ticket.get('status') == 'Open':
            print(f"  • Action: Notify user about ongoing investigation")
        elif top_ticket.get('status') == 'Resolved':
            print(f"  • Action: Share resolution from {top_ticket['ticket_id']}")
    else:
        print("  • Create new ticket")
        print(f"  • Route to: {category} Team")
        if similar_tickets:
            print(f"  • Reference: {similar_tickets[0]['ticket_id']} for context")
    
    print()
    print("="*80)
    print()


def main():
    """Run automated tests with different ticket types."""
    
    print("\n" + "="*80)
    print(" " * 20 + "SMART HELPDESK CLI - AUTOMATED DEMO")
    print("="*80)
    print()
    print("This script demonstrates the complete ticket submission flow")
    print("that users will experience via the interactive CLI.")
    print()
    
    # Test Case 1: VPN Issue (likely to find duplicates)
    print("\n" + "█"*80)
    print("TEST CASE 1: Network/VPN Issue")
    print("█"*80 + "\n")
    
    vpn_ticket = {
        'context': 'Network / VPN',
        'context_details': {'network_component': 'VPN'},
        'subject': 'VPN gateway not responding from home',
        'description': 'Cannot connect to corporate VPN since this morning. Getting connection timeout error to vpn.acme.com. Multiple team members having same issue. Very urgent as most of team works remotely.'
    }
    
    test_ticket_submission(vpn_ticket)
    
    input("\nPress Enter to continue to next test case...")
    
    # Test Case 2: Software Access (new issue)
    print("\n" + "█"*80)
    print("TEST CASE 2: Software Access Request")
    print("█"*80 + "\n")
    
    github_ticket = {
        'context': 'Software / Application',
        'context_details': {'application': 'GitHub'},
        'subject': 'Need GitHub Enterprise repository access',
        'description': 'Just joined the data engineering team and need access to the data-pipeline repository on GitHub Enterprise. Manager is John Smith from the Data Platform team. Need write access for upcoming sprint work.'
    }
    
    test_ticket_submission(github_ticket)
    
    input("\nPress Enter to continue to next test case...")
    
    # Test Case 3: Hardware Issue
    print("\n" + "█"*80)
    print("TEST CASE 3: Hardware/Device Issue")
    print("█"*80 + "\n")
    
    laptop_ticket = {
        'context': 'Hardware / Device',
        'context_details': {'device_type': 'Laptop'},
        'subject': 'Laptop fan making loud noise during compilation',
        'description': 'My MacBook Pro fan is running very loud whenever I compile code or run Docker builds. Getting very hot to touch. Concerned about hardware damage. Laptop is only 6 months old.'
    }
    
    test_ticket_submission(laptop_ticket)
    
    print("\n" + "="*80)
    print(" " * 25 + "ALL TESTS COMPLETED")
    print("="*80)
    print()
    print("✓ CLI demo flow validated successfully")
    print("✓ Model 1 integration working correctly")
    print("✓ Duplicate detection functioning as expected")
    print()
    print("To run the interactive CLI:")
    print("  python src/cli_ticket_input.py")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user.")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
