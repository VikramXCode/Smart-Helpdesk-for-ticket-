"""
Category Definitions for Model 2: Ticket Category Classification
================================================================
Defines semantic descriptions for each ticket category to enable zero-shot classification.

Enterprise Approach:
- No training data required
- Human-readable category definitions
- Easily auditable and explainable
- Can be updated without model retraining
"""

CATEGORIES = [
    "Hardware",
    "Software",
    "Network",
    "Access",
    "Security",
    "Facilities",
    "Database",
    "DevOps",
    "Cloud",
    "Environment",
    "Other"
]

CATEGORY_DESCRIPTIONS = {
    "Hardware": """
        Physical device issues including computers, laptops, desktops, monitors, keyboards,
        mice, printers, scanners, docking stations, cables, adapters, mobile devices, tablets,
        phones, headsets, webcams, speakers, and other peripheral equipment. Issues include
        device failures, malfunctions, errors, not powering on, physical damage, connectivity
        problems, display issues, and hardware replacement requests.
    """,
    
    "Software": """
        Application, program, and software-related issues including installation problems,
        software crashes, errors, bugs, freezing, slow performance, compatibility issues,
        version updates, license activation, feature requests, Microsoft Office, Adobe products,
        browsers, email clients, communication tools like Slack, Teams, Zoom, development IDEs,
        business applications, and third-party software packages.
    """,
    
    "Network": """
        Network connectivity and communication issues including WiFi connection problems,
        ethernet connection failures, VPN access issues, slow internet speed, network
        timeouts, DNS resolution errors, proxy configuration, firewall blocking, remote
        access problems, bandwidth issues, network outages, routing problems, and general
        inability to connect to internal or external resources.
    """,
    
    "Access": """
        Authentication, authorization, and permission issues including account lockouts,
        password resets, forgotten credentials, multi-factor authentication problems, single
        sign-on failures, access denied errors, permission requests, role assignments, user
        account creation, account deactivation, access to specific systems, applications,
        folders, files, databases, or resources. Includes GitHub, Jira, Confluence, SharePoint,
        cloud platforms, and other service access issues.
    """,
    
    "Security": """
        Security-related concerns including suspected malware, virus infections, phishing
        emails, suspicious activity, data breaches, unauthorized access attempts, security
        policy violations, security certificate errors, SSL/TLS issues, encryption problems,
        compliance concerns, data privacy issues, security alerts, antivirus problems, and
        security incident reporting.
    """,
    
    "Facilities": """
        Physical workplace and facility issues including office space problems, desk setup,
        chair ergonomics, lighting, temperature control, HVAC, building access, key cards,
        parking, meeting room bookings, phone system issues, conference room equipment,
        building maintenance, cleaning, and general workplace environment concerns.
    """,
    
    "Database": """
        Database access, connectivity, and query issues including connection timeouts,
        query performance problems, database errors, slow queries, data inconsistencies,
        permission errors, schema access, stored procedure failures, database backups,
        data recovery, PostgreSQL, MySQL, SQL Server, MongoDB, Oracle, and other database
        system related problems.
    """,
    
    "DevOps": """
        Development operations issues including CI/CD pipeline failures, Jenkins build errors,
        GitLab runner problems, deployment failures, containerization issues, Docker registry
        access, Kubernetes pod failures, infrastructure as code problems, configuration
        management, build automation, release management, environment provisioning, and
        development toolchain issues.
    """,
    
    "Cloud": """
        Cloud platform and service issues including AWS, Azure, Google Cloud, access problems,
        S3 bucket permissions, EC2 instance issues, Lambda function errors, cloud storage
        access, API gateway problems, cloud service configurations, resource provisioning,
        billing issues, cloud authentication, service availability, and cloud-specific
        error messages.
    """,
    
    "Environment": """
        Development, testing, staging, and production environment issues including environment
        access problems, environment-specific configurations, deployment environment failures,
        environment variable issues, sandbox access, UAT environment problems, performance
        testing environments, local development setup, Docker environment configuration, and
        environment synchronization issues.
    """,
    
    "Other": """
        Issues that don't clearly fit into the above categories including general inquiries,
        information requests, training questions, documentation requests, process questions,
        policy inquiries, onboarding assistance, offboarding tasks, general support questions,
        and miscellaneous requests that cannot be categorized into the standard categories.
    """
}

# Validation: Ensure all categories have descriptions
assert set(CATEGORIES) == set(CATEGORY_DESCRIPTIONS.keys()), \
    "Category list and descriptions must match"

# Enterprise metadata
CATEGORY_METADATA = {
    "version": "1.0.0",
    "last_updated": "2026-02-20",
    "total_categories": len(CATEGORIES),
    "classification_method": "zero-shot semantic similarity",
    "trainable": False,
    "explainable": True,
    "multi_tenant_safe": True
}


def get_category_description(category):
    """
    Get the semantic description for a category.
    
    Args:
        category: Category name
        
    Returns:
        Description string (stripped of extra whitespace)
    """
    if category not in CATEGORY_DESCRIPTIONS:
        raise ValueError(f"Unknown category: {category}. Valid categories: {CATEGORIES}")
    
    return " ".join(CATEGORY_DESCRIPTIONS[category].split())


def list_categories():
    """
    Get list of all valid categories.
    
    Returns:
        List of category names
    """
    return CATEGORIES.copy()


def validate_category(category):
    """
    Check if a category is valid.
    
    Args:
        category: Category name to validate
        
    Returns:
        Boolean indicating validity
    """
    return category in CATEGORIES


if __name__ == "__main__":
    """Validation and display script."""
    print("="*70)
    print("CATEGORY DEFINITIONS - MODEL 2")
    print("="*70)
    
    print(f"\nTotal Categories: {len(CATEGORIES)}")
    print(f"Classification Method: Zero-Shot Semantic Similarity")
    print(f"Trainable: {CATEGORY_METADATA['trainable']}")
    print(f"Explainable: {CATEGORY_METADATA['explainable']}")
    
    print("\n" + "="*70)
    print("CATEGORY DESCRIPTIONS")
    print("="*70)
    
    for category in CATEGORIES:
        description = get_category_description(category)
        print(f"\n[{category}]")
        print(f"  {description[:150]}...")
    
    print("\n" + "="*70)
    print("✓ CATEGORY DEFINITIONS VALIDATED")
    print("="*70)
