"""
CLI: Full AI Pipeline Integration
==================================
Terminal-based interface for complete multi-model ticket analysis.

Features:
- Interactive ticket submission
- Contextual dropdown prompts
- Real AI pipeline integration (Models 1, 2, 3)
- Complete analysis display with explainability
- Professional enterprise formatting

Usage:
    python src/cli_full_pipeline.py
"""

import os
import sys
from datetime import datetime

from src.ai_pipeline import TicketAIPipeline
from src.ticket_text_builder import build_semantic_text, validate_ticket_input


class FullPipelineCLI:
    """Interactive CLI for AI-powered ticket submission and analysis."""
    
    ISSUE_CONTEXTS = {
        '1': {
            'name': 'Software / Application',
            'category': 'Software',
            'details': ['GitHub', 'Jira', 'VS Code', 'Microsoft Office', 'Slack', 'Other App']
        },
        '2': {
            'name': 'Hardware / Device',
            'category': 'Hardware',
            'details': ['Laptop', 'Monitor', 'Docking Station', 'Keyboard', 'Mouse', 'Other Device']
        },
        '3': {
            'name': 'Network / Connectivity',
            'category': 'Network',
            'details': ['WiFi', 'VPN', 'Ethernet', 'Network Drive', 'Slow Internet']
        },
        '4': {
            'name': 'Workplace Issues',
            'category': 'Facilities',
            'details': ['Desk Setup', 'Chair', 'Meeting Room', 'Temperature', 'Building Access']
        },
        '5': {
            'name': 'Access / Permissions',
            'category': 'Access',
            'details': ['Account Locked', 'Password Reset', 'Permission Request', 'New Account', 'Access Denied']
        },
        '6': {
            'name': 'Development Environment',
            'category': 'Environment',
            'details': ['Local Setup', 'Docker', 'Database', 'Cloud Services', 'CI/CD']
        },
        '7': {
            'name': 'Security / Other',
            'category': 'Other',
            'details': ['Security Concern', 'Phishing Email', 'General Question', 'Other']
        }
    }
    
    def __init__(self):
        """Initialize the CLI with AI pipeline."""
        print("="*80)
        print("SMART HELPDESK - AI-POWERED TICKET SUBMISSION")
        print("="*80)
        
        # Initialize AI pipeline
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        embeddings_path = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
        
        print("\n[Initializing AI Pipeline...]")
        self.pipeline = TicketAIPipeline(embeddings_path, verbose=False)
        print("✓ AI Pipeline ready\n")
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("="*80)
        print("Welcome to the Smart Helpdesk Ticketing System")
        print("="*80)
        print("\nThis system uses AI to:")
        print("  • Detect duplicate tickets automatically")
        print("  • Classify your issue category")
        print("  • Suggest appropriate priority")
        print("  • Find similar past tickets")
        print("\nLet's get started with your issue...\n")
    
    def select_issue_context(self):
        """Prompt user to select issue context."""
        print("─"*80)
        print("STEP 1: Select your issue type")
        print("─"*80)
        
        for key, context in self.ISSUE_CONTEXTS.items():
            print(f"  [{key}] {context['name']}")
        
        while True:
            choice = input("\nSelect issue type (1-7): ").strip()
            if choice in self.ISSUE_CONTEXTS:
                return self.ISSUE_CONTEXTS[choice]
            print("Invalid selection. Please choose 1-7.")
    
    def select_detail(self, context):
        """Prompt user to select specific detail within context."""
        print(f"\n─"*80)
        print(f"STEP 2: What specifically is the issue with '{context['name']}'?")
        print("─"*80)
        
        details = context['details']
        for i, detail in enumerate(details, 1):
            print(f"  [{i}] {detail}")
        
        while True:
            choice = input(f"\nSelect option (1-{len(details)}): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(details):
                    return details[idx]
            except ValueError:
                pass
            print(f"Invalid selection. Please choose 1-{len(details)}.")
    
    def get_subject(self):
        """Prompt user for ticket subject."""
        print(f"\n─"*80)
        print("STEP 3: Brief subject line")
        print("─"*80)
        print("Enter a short description of your issue (minimum 10 characters)")
        
        while True:
            subject = input("\nSubject: ").strip()
            if len(subject) >= 10:
                return subject
            print("Subject too short. Please enter at least 10 characters.")
    
    def get_description(self):
        """Prompt user for detailed description."""
        print(f"\n─"*80)
        print("STEP 4: Detailed description")
        print("─"*80)
        print("Provide details about your issue (minimum 20 characters)")
        print("Include: What happened? When? What have you tried?")
        
        while True:
            description = input("\nDescription: ").strip()
            if len(description) >= 20:
                return description
            print("Description too short. Please enter at least 20 characters.")
    
    def display_analysis(self, analysis):
        """Display complete AI analysis results."""
        print("\n\n" + "="*80)
        print("AI ANALYSIS COMPLETE")
        print("="*80)
        
        # Duplicate Status
        print("\n🔍 DUPLICATE DETECTION")
        print("─"*80)
        if analysis['duplicate']:
            similar = analysis['similar_tickets'][0]
            print(f"⚠️  POSSIBLE DUPLICATE DETECTED")
            print(f"   Similar to: {similar['ticket_id']}")
            print(f"   Original Subject: {similar['subject']}")
            print(f"   Similarity Score: {similar['weighted_score']:.2%}")
            print(f"   Status: {similar['status']}")
            print(f"\n   → This issue may already be reported")
            print(f"   → Check ticket {similar['ticket_id']} for updates")
        else:
            print(f"✓  NEW ISSUE (Not a duplicate)")
            print(f"   Highest similarity: {analysis['highest_similarity_score']:.2%}")
            print(f"   → This appears to be a new issue")
        
        # Category Classification
        print("\n\n📂 CATEGORY CLASSIFICATION")
        print("─"*80)
        cat = analysis['category']
        print(f"Predicted Category: {cat['predicted']}")
        print(f"Confidence: {cat['confidence']:.2%}")
        print(f"Source: {cat['source']}")
        
        if cat.get('alternatives'):
            print(f"\nAlternative categories considered:")
            for alt in cat['alternatives'][:2]:
                print(f"  • {alt['category']}: {alt['score']:.2%}")
        
        # Priority Suggestion
        print("\n\n⚡ PRIORITY RECOMMENDATION")
        print("─"*80)
        pri = analysis['priority']
        print(f"Suggested Priority: {pri['suggested']}")
        print(f"Confidence: {pri['confidence']:.2%}")
        print(f"Method: {pri['method']}")
        
        print(f"\nReasoning:")
        for i, reason in enumerate(pri['reasoning'], 1):
            print(f"  {i}. {reason}")
        
        # Similar Tickets
        print("\n\n📋 SIMILAR PAST TICKETS")
        print("─"*80)
        for i, ticket in enumerate(analysis['similar_tickets'][:3], 1):
            print(f"\n#{i} Ticket {ticket['ticket_id']} (Similarity: {ticket['weighted_score']:.2%})")
            print(f"   Subject: {ticket['subject']}")
            print(f"   Category: {ticket['category']} | Priority: {ticket['priority']} | Status: {ticket['status']}")
        
        # Recommendations
        print("\n\n💡 RECOMMENDED ACTIONS")
        print("─"*80)
        
        if analysis['duplicate']:
            similar = analysis['similar_tickets'][0]
            print(f"Since this appears to be a duplicate:")
            print(f"  1. Review existing ticket: {similar['ticket_id']}")
            print(f"  2. Check if solution is already available")
            if similar['status'] == 'Resolved':
                print(f"  3. Original ticket was resolved - solution may apply to you")
            else:
                print(f"  3. Subscribe to {similar['ticket_id']} for updates")
            print(f"  4. Contact the team handling {similar['ticket_id']}")
        else:
            print(f"This is a new issue. Recommended next steps:")
            print(f"  1. Submit ticket to {cat['predicted']} team")
            print(f"  2. Assign priority: {pri['suggested']}")
            print(f"  3. Reference similar ticket {analysis['similar_tickets'][0]['ticket_id']} for context")
            print(f"  4. Expected routing: {cat['predicted']} support team")
        
        # Execution Info
        print("\n\n⚙️  SYSTEM INFORMATION")
        print("─"*80)
        exp = analysis['explainability']
        print(f"Pipeline: {exp['pipeline_flow']}")
        print(f"Execution Time: {exp['execution_time_seconds']:.3f}s")
        print(f"All decisions are deterministic and auditable")
        
        print("\n" + "="*80)
    
    def confirm_submission(self):
        """Ask user to confirm ticket submission."""
        print("\n─"*80)
        while True:
            choice = input("\nWould you like to analyze another ticket? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            print("Please enter 'y' or 'n'")
    
    def run(self):
        """Main CLI execution loop."""
        self.display_welcome()
        
        while True:
            try:
                # Step 1: Select issue context
                context = self.select_issue_context()
                
                # Step 2: Select specific detail
                detail = self.select_detail(context)
                
                # Step 3: Get subject
                subject = self.get_subject()
                
                # Step 4: Get description
                description = self.get_description()
                
                # Validate input
                print("\n[Validating input...]")
                is_valid, validation_msg = validate_ticket_input(subject, description)
                
                if not is_valid:
                    print(f"❌ Validation Error: {validation_msg}")
                    continue
                
                print("✓ Input validated")
                
                # Display what will be analyzed
                print("\n" + "="*80)
                print("SUBMITTING FOR AI ANALYSIS")
                print("="*80)
                print(f"\nIssue Type: {context['name']} → {detail}")
                print(f"Subject: {subject}")
                print(f"Description: {description}")
                print("\n[Running AI Pipeline...]")
                
                # Run AI Pipeline
                analysis = self.pipeline.analyze_ticket(
                    subject=subject,
                    description=description,
                    tenant_id="demo_tenant",
                    top_similar=3,
                    verbose=False
                )
                
                # Display results
                self.display_analysis(analysis)
                
                # Continue?
                if not self.confirm_submission():
                    break
                
                print("\n" + "="*80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n[Session interrupted by user]")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
        
        print("\n" + "="*80)
        print("Thank you for using Smart Helpdesk AI!")
        print("="*80)


def main():
    """Entry point for CLI."""
    cli = FullPipelineCLI()
    cli.run()


if __name__ == "__main__":
    main()
