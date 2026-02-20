"""
Ticket Text Builder
====================
Converts structured ticket form inputs into semantic text for Model 1.

This module mimics what a future UI form will provide and transforms
the structured data into natural language that Model 1 can understand.

KEY PRINCIPLE:
- Model 1 only understands TEXT (subject + description + context)
- UI forms capture structured data (dropdowns, fields)
- This builder bridges the gap: Form Fields → Semantic Text

ENTERPRISE CONTEXT:
In production, this will be called by the API layer after form submission.
The CLI demo uses this same logic to ensure consistency.
"""


def build_semantic_text(
    subject: str,
    description: str,
    context: str = None,
    context_details: dict = None
) -> str:
    """
    Build semantic text from structured ticket inputs.
    
    This is the ONLY text that Model 1 will see. It combines:
    - Subject (short summary)
    - Description (detailed explanation)
    - [Optional] Issue context (category) - for backward compatibility
    - [Optional] Context-specific details - for backward compatibility
    
    Args:
        subject: Short subject line (e.g., "Laptop overheating during builds")
        description: Detailed description of the issue
        context: Optional issue context (e.g., "Software / Application")
        context_details: Optional dict with context-specific fields
    
    Returns:
        Semantic text string optimized for Model 1 embedding generation
    
    Example:
        Input:
            subject = "Docking station not detecting monitor"
            description = "External display not showing up when connected"
        
        Output:
            Docking station not detecting monitor.
            External display not showing up when connected.
    """
    # Initialize text blocks
    text_parts = []
    
    # Add context tag only if provided (backward compatibility)
    if context:
        text_parts.append(f"[Context: {context}]")
    
    # Add context-specific details only if provided (backward compatibility)
    if context_details:
        # Map common field names to readable labels
        field_labels = {
            "application": "Application",
            "device_type": "Device",
            "network_component": "Network Component",
            "facility_item": "Facility Item",
            "access_type": "Access Type",
            "environment": "Environment"
        }
        
        for field_key, field_value in context_details.items():
            if field_value and field_value != "Others":
                label = field_labels.get(field_key, field_key.replace("_", " ").title())
                text_parts.append(f"[{label}: {field_value}]")
    
    # Add subject and description (core content)
    if subject:
        text_parts.append(subject)
    
    if description:
        text_parts.append(description)
    
    # Join all parts with newlines for readability
    semantic_text = "\n".join(text_parts)
    
    return semantic_text


def normalize_category(context: str, context_details: dict = None) -> str:
    """
    Convert UI context selection to database category field.
    
    This maps the user-friendly context labels to the category values
    used in tickets.csv for similarity matching.
    
    Args:
        context: Issue context from UI (e.g., "Software / Application")
        context_details: Optional details to refine category
    
    Returns:
        Category string matching tickets.csv schema
    
    Example:
        normalize_category("Hardware / Device") → "Hardware"
        normalize_category("Software / Application") → "Software Access"
    """
    # Mapping from UI context to database category
    category_map = {
        "Software / Application": "Software Access",
        "Hardware / Device": "Hardware",
        "Network / VPN": "Network",
        "Workplace / Facilities": "Hardware",  # Facilities often mapped to Hardware in ITSM
        "Access / Permission": "Software Access",
        "Environment / Setup": "Development Tools",
        "Others": "Software Access"  # Default fallback
    }
    
    # Check if we can refine based on context details
    if context == "Network / VPN" and context_details:
        network_comp = context_details.get("network_component", "")
        if "Security" in network_comp or "Certificate" in network_comp:
            return "Security"
        return "Network"
    
    if context == "Software / Application" and context_details:
        app = context_details.get("application", "")
        if "Database" in app or "MongoDB" in app or "PostgreSQL" in app:
            return "Database"
        if "Docker" in app or "Kubernetes" in app or "Jenkins" in app:
            return "DevOps"
        return "Software Access"
    
    return category_map.get(context, "Software Access")


def validate_ticket_input(subject: str, description: str) -> tuple[bool, str]:
    """
    Validate ticket inputs before processing.
    
    Enterprise validation rules:
    - Subject must not be empty
    - Subject must be between 10-200 characters
    - Description must not be empty
    - Description must be at least 20 characters
    
    Args:
        subject: Ticket subject
        description: Ticket description
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    
    Example:
        validate_ticket_input("", "Test") → (False, "Subject cannot be empty")
        validate_ticket_input("Valid", "Valid description here") → (True, "")
    """
    # Check subject
    if not subject or not subject.strip():
        return False, "Subject cannot be empty"
    
    subject = subject.strip()
    if len(subject) < 10:
        return False, "Subject must be at least 10 characters"
    
    if len(subject) > 200:
        return False, "Subject must be less than 200 characters"
    
    # Check description
    if not description or not description.strip():
        return False, "Description cannot be empty"
    
    description = description.strip()
    if len(description) < 20:
        return False, "Description must be at least 20 characters (provide details about the issue)"
    
    return True, ""


# Example usage and testing
if __name__ == "__main__":
    print("="*80)
    print("TICKET TEXT BUILDER - EXAMPLES")
    print("="*80)
    print()
    
    # Example 1: Hardware issue
    print("Example 1: Hardware Issue")
    print("-" * 80)
    text1 = build_semantic_text(
        context="Hardware / Device",
        subject="Docking station not detecting external monitor",
        description="When I connect my external Dell monitor to the docking station, it's not being detected. The monitor works fine when connected directly to laptop via HDMI.",
        context_details={"device_type": "Docking Station"}
    )
    print(text1)
    print()
    
    # Example 2: Software issue
    print("Example 2: Software Issue")
    print("-" * 80)
    text2 = build_semantic_text(
        context="Software / Application",
        subject="VS Code not detecting Python interpreter",
        description="After installing Python 3.11, VS Code is not showing it in the interpreter list. Tried reloading window and reinstalling Python extension.",
        context_details={"application": "VS Code"}
    )
    print(text2)
    print()
    
    # Example 3: Network issue
    print("Example 3: Network Issue")
    print("-" * 80)
    text3 = build_semantic_text(
        context="Network / VPN",
        subject="VPN connection drops every 30 minutes",
        description="Corporate VPN disconnects automatically every 30 minutes. Have to re-authenticate each time. Using Cisco AnyConnect on Windows 11.",
        context_details={"network_component": "VPN"}
    )
    print(text3)
    print()
    
    # Example 4: Validation tests
    print("Example 4: Validation Tests")
    print("-" * 80)
    
    # Valid input
    valid, msg = validate_ticket_input(
        "Laptop overheating",
        "My laptop gets very hot during builds and compilation"
    )
    print(f"Valid input: {valid}, Message: '{msg}'")
    
    # Invalid - subject too short
    valid, msg = validate_ticket_input(
        "Short",
        "This is a valid description with enough characters"
    )
    print(f"Short subject: {valid}, Message: '{msg}'")
    
    # Invalid - description too short
    valid, msg = validate_ticket_input(
        "Valid subject here",
        "Too short"
    )
    print(f"Short description: {valid}, Message: '{msg}'")
    
    print()
    print("="*80)
    print("✓ Ticket Text Builder Ready")
    print("="*80)
