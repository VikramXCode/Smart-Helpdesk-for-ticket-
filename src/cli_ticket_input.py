"""
CLI Ticket Input System
========================
Terminal-based interface for raising internal IT helpdesk tickets.

This demo simulates the ticket submission flow that will come from a future UI.
It demonstrates how structured form inputs are processed by Model 1 for
semantic similarity and duplicate detection.

ENTERPRISE USE CASE:
- Employees raise tickets via UI form (future)
- This CLI demo shows the exact same data flow
- Model 1 analyzes the ticket for duplicates
- Recommendation provided: Link to existing or create new

IMPORTANT:
- Model 1 core logic is NOT modified
- Only Model 1 outputs are shown (no mocking)
- This is a production-quality demo for enterprise stakeholders
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Model 1 components (DO NOT MODIFY THEIR LOGIC)
from model1_similarity import TicketSimilarityMatcher

# Import ticket text builder
from ticket_text_builder import (
    build_semantic_text,
    normalize_category,
    validate_ticket_input
)


class TicketCLI:
    """
    Command-line interface for IT helpdesk ticket submission.
    
    Simulates the future UI form flow and demonstrates Model 1 integration.
    """
    
    def __init__(self, embeddings_path: str = None):
        """
        Initialize the CLI system.
        
        Args:
            embeddings_path: Path to pre-generated embeddings file
        """
        if embeddings_path is None:
            # Default path relative to script location
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            embeddings_path = os.path.join(base_dir, 'data', 'ticket_embeddings.pkl')
        
        self.embeddings_path = embeddings_path
        self.similarity_matcher = None
        
        # Issue context options (matches UI form dropdowns)
        self.contexts = [
            "Software / Application",
            "Hardware / Device",
            "Network / VPN",
            "Workplace / Facilities",
            "Access / Permission",
            "Environment / Setup",
            "Others"
        ]
        
        # Context-specific options
        self.software_apps = [
            "GitHub", "Jira", "Confluence", "Slack", "VS Code",
            "IntelliJ IDEA", "Docker", "Kubernetes", "Jenkins",
            "Azure DevOps", "Datadog", "MongoDB", "PostgreSQL",
            "npm", "Outlook", "Teams", "Others"
        ]
        
        self.hardware_devices = [
            "Laptop", "Desktop", "Monitor", "Docking Station",
            "Keyboard", "Mouse", "Headset", "Webcam",
            "External Drive", "Power Adapter", "Others"
        ]
        
        self.network_components = [
            "VPN", "WiFi", "Ethernet", "DNS", "Firewall",
            "Load Balancer", "SSL Certificate", "Others"
        ]
        
        self.facility_items = [
            "Chair", "Desk", "Standing Desk", "Lighting",
            "Air Conditioning", "Power Outlet", "Meeting Room",
            "Others"
        ]
        
        self.access_types = [
            "Application Access", "Database Access", "Cloud Access",
            "Admin Access", "Repository Access", "SSH Access",
            "Others"
        ]
        
        self.environments = [
            "Local Development", "CI/CD Pipeline", "Staging",
            "Production", "Docker Environment", "Cloud Environment",
            "Others"
        ]
    
    def show_banner(self):
        """Display welcome banner."""
        print()
        print("=" * 80)
        print(" " * 20 + "SMART HELPDESK – RAISE INTERNAL TICKET")
        print("=" * 80)
        print()
        print("This system uses AI to detect duplicate tickets and provide smart routing.")
        print("Your ticket will be analyzed against historical tickets using Model 1.")
        print()
    
    def select_option(self, prompt: str, options: list, allow_custom: bool = False) -> str:
        """
        Display numbered options and get user selection.
        
        Args:
            prompt: Question to display
            options: List of options to choose from
            allow_custom: If True, allow "Others" with custom input
        
        Returns:
            Selected option or custom input
        """
        print(prompt)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print()
        
        while True:
            try:
                choice = input("Select option (enter number): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(options):
                    selected = options[choice_num - 1]
                    
                    # If "Others" selected and custom input allowed
                    if selected == "Others" and allow_custom:
                        custom = input("Please specify: ").strip()
                        if custom:
                            return custom
                        else:
                            print("⚠️  Custom input cannot be empty. Try again.\n")
                            continue
                    
                    return selected
                else:
                    print(f"⚠️  Invalid choice. Please enter a number between 1 and {len(options)}.\n")
            
            except ValueError:
                print("⚠️  Please enter a valid number.\n")
            except KeyboardInterrupt:
                print("\n\nTicket submission cancelled.")
                sys.exit(0)
    
    def get_text_input(self, prompt: str, min_length: int = 0) -> str:
        """
        Get text input from user with validation.
        
        Args:
            prompt: Question to display
            min_length: Minimum required length
        
        Returns:
            User input string
        """
        while True:
            try:
                print(prompt)
                user_input = input("> ").strip()
                
                if len(user_input) >= min_length:
                    return user_input
                else:
                    print(f"⚠️  Input must be at least {min_length} characters. Try again.\n")
            
            except KeyboardInterrupt:
                print("\n\nTicket submission cancelled.")
                sys.exit(0)
    
    def collect_ticket_info(self) -> Dict[str, any]:
        """
        Collect ticket information through CLI prompts.
        
        Returns:
            Dictionary with ticket fields
        """
        ticket_data = {}
        
        # Step 1: Select issue context
        print("-" * 80)
        context = self.select_option(
            "STEP 1: What is your issue related to?",
            self.contexts,
            allow_custom=True
        )
        ticket_data['context'] = context
        ticket_data['context_details'] = {}
        print(f"✓ Context: {context}\n")
        
        # Step 2: Conditional context-specific options
        print("-" * 80)
        
        if "Software" in context or "Application" in context:
            app = self.select_option(
                "STEP 2: Which application is affected?",
                self.software_apps,
                allow_custom=True
            )
            ticket_data['context_details']['application'] = app
            print(f"✓ Application: {app}\n")
        
        elif "Hardware" in context or "Device" in context:
            device = self.select_option(
                "STEP 2: Which device is affected?",
                self.hardware_devices,
                allow_custom=True
            )
            ticket_data['context_details']['device_type'] = device
            print(f"✓ Device: {device}\n")
        
        elif "Network" in context or "VPN" in context:
            network = self.select_option(
                "STEP 2: Which network component is affected?",
                self.network_components,
                allow_custom=True
            )
            ticket_data['context_details']['network_component'] = network
            print(f"✓ Network Component: {network}\n")
        
        elif "Workplace" in context or "Facilities" in context:
            facility = self.select_option(
                "STEP 2: Which facility item is affected?",
                self.facility_items,
                allow_custom=True
            )
            ticket_data['context_details']['facility_item'] = facility
            print(f"✓ Facility Item: {facility}\n")
        
        elif "Access" in context or "Permission" in context:
            access = self.select_option(
                "STEP 2: What type of access do you need?",
                self.access_types,
                allow_custom=True
            )
            ticket_data['context_details']['access_type'] = access
            print(f"✓ Access Type: {access}\n")
        
        elif "Environment" in context or "Setup" in context:
            env = self.select_option(
                "STEP 2: Which environment is affected?",
                self.environments,
                allow_custom=True
            )
            ticket_data['context_details']['environment'] = env
            print(f"✓ Environment: {env}\n")
        
        else:
            print("STEP 2: (Skipped for custom context)\n")
        
        # Step 3: Subject
        print("-" * 80)
        subject = self.get_text_input(
            "STEP 3: Enter ticket subject (short summary, 10-200 chars):",
            min_length=10
        )
        ticket_data['subject'] = subject
        print(f"✓ Subject captured\n")
        
        # Step 4: Description
        print("-" * 80)
        description = self.get_text_input(
            "STEP 4: Enter detailed description (minimum 20 chars):",
            min_length=20
        )
        ticket_data['description'] = description
        print(f"✓ Description captured\n")
        
        return ticket_data
    
    def analyze_with_model1(self, semantic_text: str, category: str) -> Dict:
        """
        Run Model 1 inference on the ticket.
        
        Args:
            semantic_text: Built semantic text for Model 1
            category: Normalized category for filtering
        
        Returns:
            Dictionary with analysis results
        """
        # Initialize similarity matcher if not already done
        if self.similarity_matcher is None:
            print("\n[Loading Model 1...]")
            if not os.path.exists(self.embeddings_path):
                print(f"\n⚠️  ERROR: Embeddings file not found at: {self.embeddings_path}")
                print("\nPlease run the following command first:")
                print("  python src/model1_embeddings.py")
                print("\nThis will generate embeddings for all historical tickets.")
                sys.exit(1)
            
            self.similarity_matcher = TicketSimilarityMatcher(self.embeddings_path)
            print("[Model 1 loaded successfully]\n")
        
        # Use Model 1's complete analysis pipeline
        print("[Analyzing ticket with Model 1...]")
        print()
        
        # Call Model 1's official analyze_new_ticket() method
        # This handles: embedding generation + similarity matching + duplicate detection
        analysis = self.similarity_matcher.analyze_new_ticket(
            subject="",  # Empty since semantic_text contains everything
            description=semantic_text,  # Pass built semantic text
            category=category if category else None,
            top_n=3
        )
        
        # Transform similar_tickets from Model 1 format (list of tuples)
        # to CLI display format (list of dicts with 'similarity' key)
        formatted_tickets = []
        for ticket_dict, similarity_score in analysis['similar_tickets']:
            # Add similarity to the ticket dict for display
            ticket_with_score = ticket_dict.copy()
            ticket_with_score['similarity'] = similarity_score
            formatted_tickets.append(ticket_with_score)
        
        return {
            'similar_tickets': formatted_tickets,
            'is_duplicate': analysis['is_duplicate'],
            'top_similarity': analysis['highest_similarity']
        }
    
    def display_results(self, analysis: Dict, ticket_data: Dict):
        """
        Display Model 1 analysis results in enterprise format.
        
        Args:
            analysis: Model 1 analysis results
            ticket_data: Original ticket data
        """
        print()
        print("=" * 80)
        print(" " * 25 + "AI ANALYSIS RESULT – MODEL 1")
        print("=" * 80)
        print()
        
        # Show submitted ticket summary
        print("📝 Your Ticket:")
        print(f"   Context: {ticket_data['context']}")
        if ticket_data['context_details']:
            for key, value in ticket_data['context_details'].items():
                label = key.replace('_', ' ').title()
                print(f"   {label}: {value}")
        print(f"   Subject: {ticket_data['subject']}")
        print()
        
        # Show similar tickets
        similar_tickets = analysis['similar_tickets']
        
        if similar_tickets:
            print("🔍 Top Similar Historical Tickets:")
            print()
            
            for i, ticket in enumerate(similar_tickets, 1):
                similarity_pct = ticket['similarity'] * 100
                
                # Mark possible duplicates
                duplicate_flag = " ⚠️  Possible Duplicate" if similarity_pct >= 80 else ""
                
                print(f"  {i}. {ticket['ticket_id']} – {ticket['subject']}")
                print(f"     Similarity: {similarity_pct:.1f}%{duplicate_flag}")
                print(f"     Status: {ticket.get('status', 'Unknown')}")
                print(f"     Priority: {ticket.get('priority', 'Unknown')}")
                print()
        else:
            print("🔍 No similar historical tickets found.")
            print()
        
        # Duplicate detection status
        print("-" * 80)
        print("Duplicate Detection Status:")
        print()
        
        is_duplicate = analysis['is_duplicate']
        top_similarity = analysis['top_similarity'] * 100
        
        if is_duplicate:
            print(f"  ⚠️  DUPLICATE LIKELY (Similarity: {top_similarity:.1f}% ≥ 80%)")
        else:
            print(f"  ✓ NEW ISSUE (Highest Similarity: {top_similarity:.1f}% < 80%)")
        print()
        
        # AI Recommendation
        print("-" * 80)
        print("💡 AI Recommendation:")
        print()
        
        if is_duplicate and similar_tickets:
            top_ticket = similar_tickets[0]
            print(f"  • This ticket appears to be a duplicate of {top_ticket['ticket_id']}")
            print(f"  • Recommended Action: Link to existing ticket {top_ticket['ticket_id']}")
            print(f"  • Status: {top_ticket.get('status', 'Unknown')}")
            
            if top_ticket.get('status') == 'Open':
                print(f"  • Next Step: Notify user about ongoing investigation")
            elif top_ticket.get('status') == 'Resolved':
                print(f"  • Next Step: Share resolution from {top_ticket['ticket_id']}")
        else:
            print("  • This appears to be a new issue")
            print("  • Recommended Action: Create new ticket")
            
            # Suggest routing based on category/context
            if similar_tickets:
                top_ticket = similar_tickets[0]
                # Infer team from top similar ticket's category
                category = normalize_category(ticket_data['context'], ticket_data['context_details'])
                print(f"  • Suggested Routing: {category} Team")
                print(f"  • Reference Similar Ticket: {top_ticket['ticket_id']} for context")
            else:
                category = normalize_category(ticket_data['context'], ticket_data['context_details'])
                print(f"  • Suggested Routing: {category} Team")
        
        print()
        print("=" * 80)
        print(" " * 30 + "END OF ANALYSIS")
        print("=" * 80)
        print()
    
    def run(self):
        """Main execution flow."""
        try:
            # Show welcome banner
            self.show_banner()
            
            # Collect ticket information
            ticket_data = self.collect_ticket_info()
            
            # Validate inputs
            print("-" * 80)
            print("Validating ticket inputs...")
            valid, error_msg = validate_ticket_input(
                ticket_data['subject'],
                ticket_data['description']
            )
            
            if not valid:
                print(f"\n⚠️  VALIDATION ERROR: {error_msg}")
                print("Please try again with valid inputs.")
                sys.exit(1)
            
            print("✓ Validation passed\n")
            
            # Build semantic text for Model 1
            print("-" * 80)
            print("Building semantic representation for AI analysis...")
            semantic_text = build_semantic_text(
                context=ticket_data['context'],
                subject=ticket_data['subject'],
                description=ticket_data['description'],
                context_details=ticket_data['context_details']
            )
            
            print("\n📄 Semantic Text for Model 1:")
            print("-" * 40)
            print(semantic_text)
            print("-" * 40)
            print()
            
            # Normalize category
            category = normalize_category(
                ticket_data['context'],
                ticket_data['context_details']
            )
            
            # Run Model 1 analysis
            print("-" * 80)
            analysis = self.analyze_with_model1(semantic_text, category)
            
            # Display results
            self.display_results(analysis, ticket_data)
            
            print("\n✓ Ticket analysis complete.")
            print("  In production, this would create/link the ticket automatically.\n")
        
        except KeyboardInterrupt:
            print("\n\nTicket submission cancelled by user.")
            sys.exit(0)
        
        except Exception as e:
            print(f"\n⚠️  ERROR: {str(e)}")
            print("\nPlease ensure:")
            print("  1. Embeddings are generated: python src/model1_embeddings.py")
            print("  2. All dependencies are installed: pip install -r requirements.txt")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Entry point for CLI demo."""
    cli = TicketCLI()
    cli.run()


if __name__ == "__main__":
    main()
