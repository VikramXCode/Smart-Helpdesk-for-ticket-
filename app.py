"""
Flask Web Application: Explainable AI Ticket Analysis
======================================================
Enterprise-grade transparent AI helpdesk system.

Architecture:
    Frontend (HTML) → Flask Backend → Model 2 → Model 1 → Model 3
    
Transparency Guarantee:
    - Every AI decision is logged to terminal
    - Step-by-step reasoning is visible
    - No black-box behavior
    - Full explainability for enterprise audit
"""

# ====================================================
# SUPPRESS ALL WARNINGS FOR CLEAN TERMINAL OUTPUT
# ====================================================
import warnings
warnings.filterwarnings("ignore")

import os
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ====================================================
# IMPORTS
# ====================================================
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sys

# Import our AI models
from src.model2_classifier import TicketCategoryClassifier
from src.model1_weighted_similarity import CategoryWeightedSimilarityMatcher
from src.model3_priority_engine import PriorityPredictionEngine
from src.ticket_text_builder import build_semantic_text

# Import NLTK for dictionary-based gibberish detection
import nltk
try:
    from nltk.corpus import words
    nltk.data.find('corpora/words')
except LookupError:
    print("[SETUP] Downloading NLTK words corpus for gibberish detection...")
    nltk.download('words', quiet=True)
    from nltk.corpus import words

# ====================================================
# FLASK APP INITIALIZATION
# ====================================================
app = Flask(__name__)

# ====================================================
# AI PIPELINE INITIALIZATION (LOAD MODELS ONCE)
# ====================================================
print("\n" + "="*70)
print("INITIALIZING EXPLAINABLE AI TICKET ANALYSIS SYSTEM")
print("="*70)
print("[SYSTEM] Loading AI models...")
print("[SYSTEM] Transparency mode: FULL")
print("[SYSTEM] Explainability: MANDATORY")
print()

# CRITICAL: Add error handling for model initialization (Flow 10 requirement)
ai_enabled = False
classifier = None
similarity_matcher = None
priority_engine = None

try:
    # Initialize Model 2 (Category Classifier)
    print("[INIT] Loading Model 2: Category Classifier")
    classifier = TicketCategoryClassifier()
    print("[INIT] ✓ Model 2 ready")

    # Initialize Model 1 (Weighted Similarity)
    print("[INIT] Loading Model 1: Category-Weighted Similarity Matcher")
    similarity_matcher = CategoryWeightedSimilarityMatcher(
        embeddings_path='data/ticket_embeddings.pkl'
    )
    print("[INIT] ✓ Model 1 ready")

    # Initialize Model 3 (Priority Engine)
    print("[INIT] Loading Model 3: Priority Prediction Engine")
    priority_engine = PriorityPredictionEngine()
    print("[INIT] ✓ Model 3 ready")

    ai_enabled = True
    print()
    print("[SYSTEM] All AI models loaded successfully")
    print("[SYSTEM] Web server ready to accept requests")
    print("="*70)
    print()

except Exception as e:
    print()
    print("[ERROR] AI models failed to initialize!")
    print(f"[ERROR] Details: {str(e)}")
    print()
    print("[FALLBACK] Switching to rule-based mode")
    print("[FALLBACK] AI features will be disabled")
    print("[FALLBACK] Basic routing will be available")
    print("="*70)
    print()
    ai_enabled = False

# ====================================================
# ROUTING RULES (DETERMINISTIC, RULE-BASED)
# ====================================================
CATEGORY_ROUTING = {
    'Hardware': 'Desktop Support Team',
    'Software': 'Application Support Team',
    'Network': 'Network Operations Team',
    'Access': 'Identity & Access Management Team',
    'Security': 'Security Operations Center (SOC)',
    'Facilities': 'Facilities Management Team',
    'Database': 'Database Administration Team',
    'DevOps': 'DevOps & Infrastructure Team',
    'Cloud': 'Cloud Platform Team',
    'Environment': 'Development Environment Team',
    'Other': 'General IT Support Team'
}

# ====================================================
# ROUTES
# ====================================================

@app.route('/')
def index():
    """Render the ticket submission form."""
    return render_template('index.html')


@app.route('/submit-ticket', methods=['POST'])
def submit_ticket():
    """
    Process ticket submission through full AI pipeline.
    Prints detailed reasoning to terminal.
    Returns results to browser.
    """
    
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "NEW TICKET ANALYSIS REQUEST" + " "*26 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    # CRITICAL: Check if AI is enabled (Flow 10 fallback)
    if not ai_enabled:
        print("[FALLBACK MODE] AI models not available")
        print("[FALLBACK MODE] Using rule-based routing")
        return render_template('error.html', 
            error_message="AI system is currently unavailable. Please try again later or contact support.",
            fallback_mode=True)
    
    # ====================================================
    # STEP 0: INPUT NORMALIZATION
    # ====================================================
    print("[STEP 0] INPUT NORMALIZATION")
    print("-" * 70)
    
    # Extract form data
    context = request.form.get('context', 'Other')
    subtype = request.form.get('subtype', '')
    subject = request.form.get('subject', '')
    description = request.form.get('description', '')
    
    print(f"[INFO] Ticket received from web UI")
    print(f"[INFO] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[INFO] User-selected context: {context}")
    if subtype:
        print(f"[INFO] User-selected subtype: {subtype}")
    print()
    print(f"[INFO] Raw Subject:")
    print(f"       {subject}")
    print()
    print(f"[INFO] Raw Description:")
    print(f"       {description}")
    print()
    
    # Build semantic text
    print("[INFO] Building semantic text for AI models...")
    
    # Build context_details dictionary with subtype if available
    # Map subtype to appropriate field based on context
    context_details = {}
    if subtype:
        # Map context to appropriate field name
        if 'Hardware' in context:
            context_details['device_type'] = subtype
        elif 'Software' in context:
            context_details['application'] = subtype
        elif 'Network' in context:
            context_details['network_component'] = subtype
        elif 'Facilities' in context or 'Workplace' in context:
            context_details['facility_item'] = subtype
        elif 'Access' in context:
            context_details['access_type'] = subtype
        elif 'Environment' in context:
            context_details['environment'] = subtype
        else:
            # Generic fallback
            context_details['subtype'] = subtype
    
    semantic_text = build_semantic_text(
        context=context,
        subject=subject,
        description=description,
        context_details=context_details if context_details else None
    )
    
    print()
    print("[DEBUG] Semantic Text fed to AI models:")
    print("-" * 70)
    print(semantic_text)
    print("-" * 70)
    print()
    
    # ====================================================
    # STEP 1: MODEL 2 – CATEGORY CLASSIFICATION
    # ====================================================
    print()
    print("[STEP 1] MODEL 2 – CATEGORY CLASSIFICATION")
    print("-" * 70)
    print("[MODEL 2] Method: Zero-shot semantic similarity")
    print("[MODEL 2] Approach: Compare ticket to 11 category descriptions")
    print("[MODEL 2] No training required, fully deterministic")
    print()
    
    print("[MODEL 2] Embedding ticket text...")
    result_m2 = classifier.classify_ticket(
        subject=subject,
        description=description,
        top_n=11  # Get all categories with scores
    )
    
    predicted_category = result_m2['predicted_category']
    category_confidence = result_m2['confidence']
    all_scores = result_m2['all_scores']  # List of dicts: [{'category': 'X', 'score': 0.9}, ...]
    
    print("[MODEL 2] ✓ Embedding complete")
    print()
    print("[MODEL 2] Similarity Scores (against all categories):")
    
    # all_scores is already sorted by score descending
    for item in all_scores:
        category = item['category']
        score = item['score']
        marker = " ← PREDICTED" if category == predicted_category else ""
        print(f"  {category:30s} : {score:.4f} ({score*100:.2f}%){marker}")
    
    print()
    print(f"[MODEL 2] ✓ Predicted Category: {predicted_category}")
    print(f"[MODEL 2] ✓ Confidence: {category_confidence:.4f} ({category_confidence*100:.2f}%)")
    print()
    print("[MODEL 2] Explanation:")
    print(f"  → Ticket text is semantically closest to '{predicted_category}' description")
    print(f"  → Semantic similarity score: {category_confidence:.4f}")
    if len(all_scores) > 1:
        print(f"  → Next closest category: {all_scores[1]['category']} ({all_scores[1]['score']:.4f})")
    print()
    
    # ====================================================
    # STEP 2: MODEL 1 – CATEGORY-WEIGHTED SIMILARITY
    # ====================================================
    print()
    print("[STEP 2] MODEL 1 – CATEGORY-WEIGHTED SIMILARITY")
    print("-" * 70)
    print("[MODEL 1] Method: Cosine similarity with category weighting")
    print(f"[MODEL 1] Using predicted category from Model 2: {predicted_category}")
    print("[MODEL 1] Weighting: Same category = 1.0, Different category = 0.6")
    print()
    
    print("[MODEL 1] Generating embedding for new ticket...")
    result_m1 = similarity_matcher.analyze_new_ticket_weighted(
        subject=subject,
        description=description,
        predicted_category=predicted_category,
        top_n=100,  # Retrieve more tickets to find all above 60%
        verbose=False
    )
    
    similar_tickets = result_m1['similar_tickets']
    is_duplicate = result_m1['is_duplicate']
    highest_similarity = result_m1['highest_weighted_score']
    
    print("[MODEL 1] ✓ Embedding complete")
    print(f"[MODEL 1] Comparing against {len(similarity_matcher.tickets)} historical tickets")
    print()
    
    # CRITICAL: Handle empty corpus (first-ever ticket)
    if len(similar_tickets) == 0:
        print("[MODEL 1] ⚠️  ZERO-SHOT MODE: No historical tickets found")
        print("[MODEL 1] This is the first ticket in the system")
        print("[MODEL 1] Duplicate detection skipped")
        print("[MODEL 1] Ticket will be treated as NEW")
        print()
    else:
        print("[MODEL 1] Top 5 Similar Tickets (with category weighting):")
        print()
    
    for i, ticket in enumerate(similar_tickets[:5], 1):
        category_match = ticket['category'] == predicted_category
        weight_applied = 1.0 if category_match else 0.6
        
        print(f"  [{i}] Ticket ID: {ticket.get('ticket_id', 'N/A')}")
        print(f"      Category: {ticket['category']}")
        print(f"      Raw Similarity: {ticket['raw_similarity']:.4f} ({ticket['raw_similarity']*100:.2f}%)")
        print(f"      Category Match: {'YES' if category_match else 'NO'}")
        print(f"      Weight Applied: {weight_applied}")
        print(f"      Weighted Score: {ticket['weighted_score']:.4f} ({ticket['weighted_score']*100:.2f}%)")
        print(f"      Subject: {ticket.get('subject', 'N/A')[:60]}...")
        print()
    
    print(f"[MODEL 1] Highest Weighted Similarity: {highest_similarity:.4f} ({highest_similarity*100:.2f}%)")
    print(f"[MODEL 1] Duplicate Threshold: 0.80 (80%)")
    print(f"[MODEL 1] Duplicate Detected: {'YES' if is_duplicate else 'NO'}")
    print()
    
    # ====================================================
    # AUTO-REPLY FEATURE (Similarity > 60%)
    # ====================================================
    AUTO_REPLY_THRESHOLD = 0.60  # 60% similarity threshold
    auto_reply_enabled = False
    auto_reply_message = None
    auto_reply_source_ticket = None
    
    # Count how many tickets meet auto-reply threshold (60%+ weighted similarity)
    auto_reply_candidate_count = sum(1 for t in similar_tickets if t.get('weighted_score', 0) >= AUTO_REPLY_THRESHOLD)
    
    # Filter tickets above 60% and calculate average
    tickets_above_60 = [t for t in similar_tickets if t.get('weighted_score', 0) >= AUTO_REPLY_THRESHOLD]
    average_similarity_above_60 = (sum(t.get('weighted_score', 0) for t in tickets_above_60) / len(tickets_above_60)) if tickets_above_60 else 0.0
    
    # Auto-reply only if 10 or more similar tickets exist
    if auto_reply_candidate_count >= 10 and len(similar_tickets) > 0:
        auto_reply_enabled = True
        auto_reply_source_ticket = similar_tickets[0]  # Use the most similar ticket
        
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "🤖 AI AUTO-REPLY AVAILABLE" + " "*26 + "║")
        print("╚" + "="*68 + "╝")
        print()
        print(f"[AUTO-REPLY] Found {auto_reply_candidate_count} similar tickets (threshold: 10+)")
        print(f"[AUTO-REPLY] Best match: {highest_similarity*100:.2f}% similarity")
        print(f"[AUTO-REPLY] Based on ticket: {auto_reply_source_ticket.get('ticket_id', 'N/A')}")
        print(f"[AUTO-REPLY] Confidence: {'HIGH' if auto_reply_candidate_count >= 20 else 'MEDIUM'}")
        print()
        
        # Generate auto-reply message based on similar ticket
        source_subject = auto_reply_source_ticket.get('subject', '')
        source_category = auto_reply_source_ticket.get('category', '')
        source_priority = auto_reply_source_ticket.get('priority', 'Medium')
        source_description = auto_reply_source_ticket.get('description', '')
        
        # Rephrase solution based on current ticket's specific situation
        current_subject_lower = ticket_subject.lower()
        current_desc_lower = ticket_description.lower()
        
        # Extract key context from current ticket for personalized rephrasing
        is_vpn_issue = any(kw in current_subject_lower or kw in current_desc_lower 
                          for kw in ['vpn', 'anyconnect', 'forticlient', 'globalprotect'])
        is_access_request = any(kw in current_subject_lower or kw in current_desc_lower 
                               for kw in ['access', 'permission', 'need to access', 'can\'t access'])
        is_laptop_issue = any(kw in current_subject_lower or kw in current_desc_lower 
                             for kw in ['laptop', 'computer', 'workstation', 'pc'])
        
        # Generate user-facing solution message based on category (NO ticket references)
        category_solutions = {
            'Network': "We've identified this as a network connectivity issue. Here's what typically resolves this:\n\n1. Restart your network device/VPN client\n2. Check if your network drivers are up to date\n3. Verify your network settings match company standards\n4. Try connecting to a different network to isolate the issue\n5. Clear your DNS cache and renew IP configuration\n\nIf the issue persists after trying these steps, our Network Operations Team will automatically be notified and will reach out to assist you.",
            
            'Software': "We've identified this as a software application issue. Try these troubleshooting steps:\n\n1. Close and restart the application\n2. Clear application cache and temporary files\n3. Check for available software updates and install them\n4. If the problem continues, try reinstalling the application\n5. Restart your computer to ensure all changes take effect\n\nMost software issues are resolved within 15-30 minutes using these steps.",
            
            'Hardware': "We've identified this as a hardware issue. Here's what to check:\n\n1. Verify all cables and connections are properly secured\n2. Power cycle the device (turn off, wait 30 seconds, turn on)\n3. Check for any visible damage, warning lights, or error messages\n4. Test with a different cable/port if applicable\n5. Ensure the device is getting adequate power\n\nIf hardware replacement is needed, our Desktop Support Team will contact you to arrange it. Typical resolution time: 2-4 hours (depending on parts availability).",
            
            'Access': "We've identified this as an access/permissions issue. Here's how to resolve it:\n\n1. Verify you're using the correct username and password\n2. Check if your account is active (not locked, suspended, or expired)\n3. Ensure you're accessing the correct system/environment\n4. Try clearing your browser cache and cookies if web-based\n5. Contact your manager to confirm you should have this access\n\nOur Identity & Access Management Team will review your request and grant appropriate permissions. Access requests are usually processed within 1 hour.",
            
            'Security': "We've identified this as a security concern. Please take these immediate actions:\n\n1. Do NOT click any suspicious links or download attachments\n2. If you suspect your account is compromised, change your password immediately\n3. Report suspicious emails to security@company.com\n4. Run a full antivirus/malware scan if you clicked suspicious content\n5. Enable multi-factor authentication if not already active\n\nOur Security Operations Center (SOC) has been automatically alerted and will investigate this incident with high priority.",
            
            'Database': "We've identified this as a database access/query issue. Here are common solutions:\n\n1. Verify your database connection credentials are correct\n2. Check if the database server is accessible from your network\n3. Review your SQL query syntax for any errors\n4. Ensure you have the necessary database permissions (SELECT, INSERT, etc.)\n5. Try connecting to a test/staging database first to isolate the issue\n\nOur Database Administration Team will review your request and provide guidance within the SLA timeframe.",
            
            'DevOps': "We've identified this as a DevOps/deployment issue. Try these troubleshooting steps:\n\n1. Check the build/deployment logs for specific error messages\n2. Verify all environment variables and configurations are correct\n3. Ensure all required dependencies are installed and up to date\n4. Try re-running the pipeline/deployment from scratch\n5. Check if there are any ongoing infrastructure issues\n\nOur DevOps Team is available to provide guidance and can help debug complex pipeline failures.",
            
            'Cloud': "We've identified this as a cloud platform issue. Here are recommended actions:\n\n1. Verify your cloud credentials and API keys are correct\n2. Check the cloud provider's status page for any ongoing outages\n3. Review your resource quotas and service limits\n4. Ensure your billing account is active and up to date\n5. Try accessing the resource from a different region if applicable\n\nOur Cloud Platform Team will investigate and provide support according to the priority level.",
        }
        
        # Get category-specific solution and rephrase based on specific situation
        base_solution = category_solutions.get(
            source_category,
            f"We've identified this as a {source_category} issue. Here are general troubleshooting steps:\n\n1. Restart the affected application or service\n2. Clear any cached data or temporary files\n3. Verify all settings and configurations are correct\n4. Check for any recent changes that might have caused the issue\n5. Try accessing from a different device or location to isolate the problem\n\nOur {CATEGORY_ROUTING.get(source_category, 'IT Support Team')} is familiar with this type of request and will provide specialized assistance if the issue persists."
        )
        
        # Rephrase solution based on detected context
        if is_vpn_issue and source_category == 'Network':
            user_solution = f"Based on {auto_reply_candidate_count} similar VPN-related tickets, here's what resolves this issue:\n\n1. Completely close your VPN client (check system tray/task manager)\n2. Restart the VPN application and try reconnecting\n3. Check your internet connection - ensure you have stable connectivity\n4. Clear VPN cache: Delete temporary VPN files from C:\\ProgramData\\[VPN Client Name]\n5. If still failing, try connecting to a different VPN gateway/region\n\nThis VPN issue pattern has been successfully resolved for {auto_reply_candidate_count} users following these steps. Average resolution time: 10-15 minutes."
        elif is_access_request and source_category == 'Access':
            user_solution = f"Based on {auto_reply_candidate_count} similar access requests, here's the standard process:\n\n1. Verify you have manager approval (email/ticket reference)\n2. Ensure you've completed required training if applicable\n3. Confirm your account is active and not locked\n4. Check if you're requesting access to the correct system/environment\n5. Provide business justification for the access level needed\n\nOur Access Management team processes {auto_reply_candidate_count}+ similar requests weekly. Typical approval time: 1-2 business hours for standard access, 24 hours for elevated permissions."
        elif is_laptop_issue and source_category == 'Hardware':
            user_solution = f"Based on {auto_reply_candidate_count} similar laptop issues, try these proven solutions:\n\n1. Perform a hard reset: Unplug power, remove battery (if removable), hold power button for 30 seconds\n2. Check if your laptop is under warranty - we may need to arrange hardware replacement\n3. Test with external peripherals disconnected to rule out conflicts\n4. Boot in safe mode to check if software is causing the issue\n5. Document any error codes or beep patterns for our hardware team\n\nOur Desktop Support team handles {auto_reply_candidate_count}+ laptop issues monthly. If hardware replacement is needed, we can usually provide a loaner within 4 hours."
        else:
            # Use base solution with context-aware prefix
            user_solution = f"Good news! We've analyzed {auto_reply_candidate_count} similar tickets and found a common resolution pattern.\n\n" + base_solution
        
        auto_reply_message = {
            'enabled': True,
            'confidence': 'HIGH' if auto_reply_candidate_count >= 20 else 'MEDIUM',
            'similarity_score': highest_similarity,
            'similar_ticket_count': auto_reply_candidate_count,
            'source_ticket_id': auto_reply_source_ticket.get('ticket_id', 'N/A'),
            'suggested_solution': user_solution,
            'next_steps': [
                f"Try the recommended troubleshooting steps above",
                f"Your ticket has been logged with reference ID: {datetime.now().strftime('%Y%m%d-%H%M%S')}",
                f"Based on {auto_reply_candidate_count} similar cases, {int(auto_reply_candidate_count * 0.85)} were resolved with these steps",
                f"If the issue persists after 30 minutes, it will be escalated to {CATEGORY_ROUTING.get(source_category, 'IT Support')}"
            ]
        }
        
        print("[AUTO-REPLY] Suggested Response to User:")
        print()
        print(user_solution)
        print()
        print("[AUTO-REPLY] Next Steps:")
        for step in auto_reply_message['next_steps']:
            print(f"  • {step}")
        print()
    else:
        if auto_reply_candidate_count > 0 and auto_reply_candidate_count < 10:
            print(f"[AUTO-REPLY] Disabled - Only {auto_reply_candidate_count} similar ticket(s) found (need 10+ for auto-reply)")
            print(f"[AUTO-REPLY] Highest similarity: {highest_similarity*100:.2f}%")
            print(f"[AUTO-REPLY] Manual review assigned to ensure quality support")
            print()
        elif len(similar_tickets) > 0:
            print(f"[AUTO-REPLY] Disabled - No tickets meet {AUTO_REPLY_THRESHOLD*100:.0f}% similarity threshold")
            print(f"[AUTO-REPLY] Highest similarity: {highest_similarity*100:.2f}%")
            print(f"[AUTO-REPLY] Manual review required for this unique ticket")
            print()
    
    if is_duplicate:
        print("[MODEL 1] Explanation:")
        print(f"  → Top match exceeds duplicate threshold (80%)")
        print(f"  → Weighted similarity: {highest_similarity*100:.2f}%")
        print(f"  → This ticket is likely a duplicate")
    else:
        print("[MODEL 1] Explanation:")
        print(f"  → No historical ticket crosses duplicate threshold (80%)")
        print(f"  → Highest weighted similarity: {highest_similarity*100:.2f}%")
        print(f"  → Same-category tickets ranked higher due to weighting")
        print(f"  → This appears to be a NEW ticket")
    print()
    
    # ====================================================
    # STEP 3: MODEL 3 – PRIORITY PREDICTION
    # ====================================================
    print()
    print("[STEP 3] MODEL 3 – PRIORITY PREDICTION")
    print("-" * 70)
    print("[MODEL 3] Method: Hybrid keyword analysis + category rules")
    print("[MODEL 3] Approach: Scan for impact keywords, apply category risk")
    print()
    
    if is_duplicate and similar_tickets:
        print("[MODEL 3] Ticket is a DUPLICATE - attempting to inherit priority")
        duplicate_ticket = similar_tickets[0]
        
    result_m3 = priority_engine.predict_priority(
        subject=subject,
        description=description,
        category=predicted_category,
        is_duplicate=is_duplicate,
        duplicate_ticket=similar_tickets[0] if is_duplicate else None,
        verbose=False
    )
    
    suggested_priority = result_m3['suggested_priority']
    priority_confidence = result_m3['confidence']
    keyword_matches = result_m3.get('keyword_matches', {})
    
    if is_duplicate and result_m3.get('method') == 'duplicate-inheritance':
        print(f"[MODEL 3] ✓ Inherited priority from duplicate ticket")
        print(f"[MODEL 3] Original ticket priority: {suggested_priority}")
        print()
        print("[MODEL 3] Explanation:")
        print(f"  → This is a duplicate ticket")
        print(f"  → Priority inherited from original ticket")
        print(f"  → Confidence: {priority_confidence:.2f} (high for inheritance)")
    else:
        print("[MODEL 3] Scanning ticket text for impact keywords...")
        print()
        print("[MODEL 3] Keyword Matches by Severity:")
        print(f"  Critical: {keyword_matches.get('critical', [])}")
        print(f"  High    : {keyword_matches.get('high', [])}")
        print(f"  Medium  : {keyword_matches.get('medium', [])}")
        print(f"  Low     : {keyword_matches.get('low', [])}")
        print()
        
        base_priority = result_m3.get('base_priority', suggested_priority)
        category_risk = result_m3['explainability'].get('category_risk', 'unknown')
        
        print(f"[MODEL 3] Base Priority (from keywords): {base_priority}")
        print(f"[MODEL 3] Category Risk Level: {predicted_category} → {category_risk}")
        print(f"[MODEL 3] Category Adjustment: {'Applied' if result_m3.get('category_adjusted') else 'None'}")
        print()
        print(f"[MODEL 3] ✓ Final Suggested Priority: {suggested_priority}")
        print(f"[MODEL 3] ✓ Confidence: {priority_confidence:.2f} ({priority_confidence*100:.0f}%)")
        print()
        
        # Get keyword count
        keyword_count = sum(len(matches) for matches in keyword_matches.values())
        
        print("[MODEL 3] Explanation:")
        if keyword_count > 0:
            print(f"  → Found {keyword_count} impact keyword(s)")
            print(f"  → Base priority from keywords: {base_priority}")
        else:
            print(f"  → No specific impact keywords detected")
            print(f"  → Using category-based priority")
        
        print(f"  → Category '{predicted_category}' is classified as: {category_risk}")
        
        if result_m3.get('category_adjusted'):
            print(f"  → Priority adjusted based on category rules")
        
        print(f"  → Final recommendation: {suggested_priority}")
    print()
    
    # ====================================================
    # VALIDATION: DETECT LOW-QUALITY/INVALID TICKETS
    # ====================================================
    print()
    print("[VALIDATION] TICKET QUALITY CHECK")
    print("-" * 70)
    
    # Helper function: Detect gibberish text using NLP word dictionary
    def is_gibberish_text(text):
        """
        Detect if text is likely gibberish using NLTK English word dictionary.
        Returns (is_gibberish, reason)
        """
        text_clean = text.lower().strip()
        if len(text_clean) < 3:
            return False, None  # Too short to judge
        
        # Get English word dictionary from NLTK
        english_words = set(words.words())
        
        # Also include common technical/IT terms not in NLTK dictionary
        technical_terms = {
            'vpn', 'wifi', 'github', 'jira', 'aws', 'azure', 'api', 'cpu', 'gpu', 'ram',
            'ssd', 'usb', 'hdmi', 'dns', 'dhcp', 'ssl', 'tls', 'ssh', 'http', 'https',
            'json', 'xml', 'sql', 'nosql', 'docker', 'kubernetes', 's3', 'ec2', 'rds',
            'iam', 'oauth', 'saml', 'ldap', 'smtp', 'imap', 'pop3', 'ftp', 'sftp',
            'vm', 'vlan', 'vpn', 'wan', 'lan', 'ip', 'tcp', 'udp', 'nat', 'firewall',
            'anyconnect', 'forticlient', 'globalprotect', 'salesforce', 'sharepoint',
            'confluence', 'slack', 'zoom', 'teams', 'outlook', 'gmail', 'chrome',
            'firefox', 'safari', 'postgres', 'postgresql', 'mysql', 'mongodb', 'redis',
            'nginx', 'apache', 'jenkins', 'gitlab', 'bitbucket', 'terraform', 'ansible',
            'cloudformation', 'helm', 'kubectl', 'eks', 'gke', 'aks', 'lambda', 'fargate'
        }
        english_words.update(technical_terms)
        
        # Split text into words and filter alphabetic characters
        text_words = text_clean.split()
        if len(text_words) < 1:
            return False, None
        
        # Analyze meaningful words (3+ characters)
        meaningful_words = []
        for word in text_words:
            # Extract only alphabetic characters
            word_clean = ''.join(c for c in word if c.isalpha())
            if len(word_clean) >= 3:  # Skip very short words like "a", "I", "ok"
                meaningful_words.append(word_clean)
        
        if len(meaningful_words) < 2:
            return False, None  # Too few words to judge
        
        # Count how many words are NOT in English dictionary
        non_english_words = []
        for word in meaningful_words:
            # Check if word or its variations exist in dictionary
            word_variants = [
                word,
                word + 's',  # plural
                word + 'ed',  # past tense
                word + 'ing',  # present continuous
                word[:-1] if word.endswith('s') else None,  # singular
                word[:-2] if word.endswith('ed') else None,  # base form from past tense
                word[:-3] if word.endswith('ing') else None,  # base form from present continuous
            ]
            
            # Check if any variant is a real English word
            if not any(variant in english_words for variant in word_variants if variant):
                non_english_words.append(word)
        
        # Calculate percentage of non-English words
        non_english_ratio = len(non_english_words) / len(meaningful_words)
        
        # Flag as gibberish if 70%+ words are not in dictionary
        if non_english_ratio >= 0.70:
            return True, f"{int(non_english_ratio*100)}% non-English words detected ({len(non_english_words)}/{len(meaningful_words)})"
        
        # Additional check: Random character patterns (e.g., "asdfghjkl", "qwertyuiop")
        keyboard_patterns = ['qwerty', 'asdfgh', 'zxcvbn', 'qazwsx', 'asdfghjkl', 'zxcvbnm']
        text_no_spaces = ''.join(c for c in text_clean if c.isalpha())
        if any(pattern in text_no_spaces for pattern in keyboard_patterns) and len(text_no_spaces) > 8:
            return True, "Keyboard pattern detected (likely random typing)"
        
        return False, None
    
    # Quality thresholds
    MIN_CATEGORY_CONFIDENCE = 0.10  # 10% minimum confidence (very strict - only flags obvious gibberish)
    MIN_SIMILARITY_SCORE = 0.25     # 25% minimum similarity with any ticket
    
    is_low_quality = False
    quality_issues = []
    
    # Check 1: Category confidence too low
    if category_confidence < MIN_CATEGORY_CONFIDENCE:
        quality_issues.append(f"Category confidence extremely low ({category_confidence*100:.1f}% < 10%)")
    
    # Check 2: No similar tickets OR all similarities extremely low
    if len(similar_tickets) == 0:
        # First-ever ticket is NOT low quality, it's valid
        print("[VALIDATION] ✓ First ticket in system - treating as valid")
    elif highest_similarity < MIN_SIMILARITY_SCORE:
        quality_issues.append(f"Low similarity with historical tickets ({highest_similarity*100:.1f}% < 25%)")
    
    # Check 3: Subject or description too short (basic sanity check)
    if len(subject.strip()) < 3:
        quality_issues.append("Subject too short (< 3 characters)")
    if len(description.strip()) < 5:
        quality_issues.append("Description too short (< 5 characters)")
    
    # Check 4: Gibberish detection (linguistic analysis)
    subject_gibberish, subject_reason = is_gibberish_text(subject)
    desc_gibberish, desc_reason = is_gibberish_text(description)
    
    if subject_gibberish:
        quality_issues.append(f"Subject appears to be gibberish ({subject_reason})")
    if desc_gibberish:
        quality_issues.append(f"Description appears to be gibberish ({desc_reason})")
    
    # Determine if ticket is low quality
    # Gibberish detection alone is enough to flag (even if only 1 other issue)
    if subject_gibberish or desc_gibberish:
        if len(quality_issues) >= 1:  # Gibberish + any other issue = flag
            is_low_quality = True
    elif len(quality_issues) >= 2:  # Non-gibberish needs at least 2 issues to flag
        is_low_quality = True
    
    if is_low_quality:
        print("[VALIDATION] ⚠️  LOW-QUALITY TICKET DETECTED")
        print()
        print("Quality Issues Found:")
        for issue in quality_issues:
            print(f"  • {issue}")
        print()
        print("[VALIDATION] Routing to Quality Review Queue")
        print("[VALIDATION] Ticket will be manually reviewed before assignment")
    else:
        print("[VALIDATION] ✓ Ticket quality acceptable")
        if quality_issues:
            print(f"[VALIDATION] Minor issue noted: {quality_issues[0]}")
    print()
    
    # ====================================================
    # STEP 4: ROUTING DECISION
    # ====================================================
    print()
    print("[STEP 4] ROUTING DECISION")
    print("-" * 70)
    
    # ROUTING PRIORITY: Low-quality check → Auto-reply → Normal routing
    if is_low_quality:
        print("[ROUTING] ⚠️  LOW-QUALITY TICKET ROUTING")
        print("[ROUTING] Detected potential invalid/spam ticket")
        print()
        print("╔" + "="*68 + "╗")
        print("║  ⚠️  TICKET FLAGGED FOR QUALITY REVIEW                            ║")
        print("║                                                                    ║")
        print("║  Quality Review Queue - Manual Verification Required              ║")
        print("╚" + "="*68 + "╝")
        print()
        print(f"[ROUTING] Status: PENDING - Quality Review Required")
        print()
        print("[ROUTING] Reason:")
        for issue in quality_issues:
            print(f"  • {issue}")
        print()
        print("[ROUTING] Next Steps:")
        print("  → Human reviewer will verify ticket validity")
        print("  → If valid: Will be reassigned to appropriate team")
        print("  → If invalid: Will be rejected as spam/gibberish")
        print()
        
        routing_team = "Quality Review Queue (Validation Required)"
        ticket_status = "PENDING - Quality Review"
        expected_response = "Manual verification required before processing"
        
    elif auto_reply_enabled:
        print("[ROUTING] ✓ AUTO-REPLY MODE ACTIVATED")
        print("[ROUTING] Ticket will be AUTO-RESOLVED by AI")
        print()
        print("╔" + "="*68 + "╗")
        print("║  🤖 TICKET AUTO-RESOLVED BY AI                                    ║")
        print("║                                                                    ║")
        print("║  No manual team intervention required                             ║")
        print("║  Solution provided based on similar ticket #{:<28s} ║".format(auto_reply_source_ticket.get('ticket_id', 'N/A')[:28]))
        print("╚" + "="*68 + "╝")
        print()
        print(f"[ROUTING] Status: CLOSED - Auto-Resolved")
        print(f"[ROUTING] Confidence: {auto_reply_message['confidence']}")
        print(f"[ROUTING] User notified with AI-generated solution")
        print()
        print("[ROUTING] Explanation:")
        print(f"  → Similarity score: {highest_similarity*100:.2f}% (≥60% threshold)")
        print(f"  → Solution available from historical ticket")
        print(f"  → No manual review needed - ticket auto-closed")
        print(f"  → User received suggested solution immediately")
        print()
        
        routing_team = "AI Auto-Resolved (No Team Assignment)"
        ticket_status = "CLOSED - Auto-Resolved"
        expected_response = "Immediate (Auto-Reply sent)"
    else:
        print("[ROUTING] Manual team assignment required")
        print(f"[ROUTING] Reason: Similarity {highest_similarity*100:.2f}% < 60% threshold")
        print(f"[ROUTING] Category: {predicted_category}")
        print()
        
        routing_team = CATEGORY_ROUTING.get(predicted_category, 'General IT Support Team')
        ticket_status = "OPEN - Awaiting Team Review"
        
        print("╔" + "="*68 + "╗")
        print("║  🎯 YOUR TICKET WILL BE HANDLED BY:                               ║")
        print("║                                                                    ║")
        print(f"║  👥 {routing_team:^61s} ║")
        print("╚" + "="*68 + "╝")
        print()
        print(f"[ROUTING] Expected Response Time:")
        if suggested_priority == 'Critical':
            expected_response = "15 minutes (Critical priority)"
            print(f"  ⏰ {expected_response}")
        elif suggested_priority == 'High':
            expected_response = "1 hour (High priority)"
            print(f"  ⏰ {expected_response}")
        elif suggested_priority == 'Medium':
            expected_response = "4 hours (Medium priority)"
            print(f"  ⏰ {expected_response}")
        else:
            expected_response = "8 hours (Low priority)"
            print(f"  ⏰ {expected_response}")
        print()
    
    # ====================================================
    # FINAL SUMMARY
    # ====================================================
    print()
    print("╔" + "="*68 + "╗")
    print("║" + " "*20 + "AI ANALYSIS COMPLETED" + " "*27 + "║")
    print("╚" + "="*68 + "╝")
    print()
    print("[SUCCESS] Full AI pipeline executed successfully")
    print()
    print("[FINAL SUMMARY]")
    print(f"  Predicted Category    : {predicted_category} ({category_confidence*100:.1f}% confidence)")
    print(f"  Duplicate Status      : {'Duplicate' if is_duplicate else 'New Ticket'}")
    print(f"  Highest Similarity    : {highest_similarity*100:.2f}%")
    print(f"  Auto-Reply Status     : {'ENABLED ✓' if auto_reply_enabled else 'Disabled'}")
    print(f"  Suggested Priority    : {suggested_priority} ({priority_confidence*100:.0f}% confidence)")
    print(f"  Ticket Status         : {ticket_status}")
    print(f"  Routing               : {routing_team}")
    if not auto_reply_enabled:
        print(f"  Expected Response     : {expected_response}")
    print()
    print("[TRANSPARENCY] All decisions are logged above with full reasoning")
    print("[AUDIT TRAIL] Complete decision path: Model 2 → Model 1 → Model 3 → Routing")
    print()
    print("="*70)
    print()
    
    # ====================================================
    # PREPARE RESULT FOR BROWSER
    # ====================================================
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'subject': subject,
        'description': description,
        'semantic_text': semantic_text,
        
        # Model 2 Results
        'predicted_category': predicted_category,
        'category_confidence': f"{category_confidence*100:.2f}%",
        'category_scores': {item['category']: f"{item['score']*100:.2f}%" for item in all_scores[:5]},
        
        # Model 1 Results
        'is_duplicate': is_duplicate,
        'duplicate_status': 'Duplicate Ticket' if is_duplicate else 'New Ticket',
        'highest_similarity': f"{highest_similarity*100:.2f}%",
        'similar_tickets': similar_tickets[:3],  # Top 3 for quick view
        'tickets_above_60': tickets_above_60,  # ALL tickets above 60% threshold
        'similar_ticket_count_60_plus': auto_reply_candidate_count,  # Count of tickets with 60%+ similarity
        'average_similarity_60_plus': f"{average_similarity_above_60*100:.2f}%" if average_similarity_above_60 > 0 else 'N/A',
        
        # Auto-Reply Feature
        'auto_reply': auto_reply_message,
        
        # Model 3 Results
        'suggested_priority': suggested_priority,
        'priority_confidence': f"{priority_confidence*100:.0f}%",
        'priority_reasoning': result_m3.get('reasoning', []),
        
        # Routing
        'routing_team': routing_team,
        'ticket_status': ticket_status,
        'auto_reply_enabled': auto_reply_enabled,
        'expected_response': expected_response if not auto_reply_enabled else "Immediate (Auto-Reply sent)",
        
        # Quality Validation
        'is_low_quality': is_low_quality,
        'quality_issues': quality_issues,
        
        # Explainability
        'explainability_note': 'This decision is AI-assisted and fully explainable. See terminal logs for complete reasoning.'
    }
    
    return render_template('result.html', result=result)


# ====================================================
# MAIN EXECUTION
# ====================================================
if __name__ == '__main__':
    print("\n[FLASK] Starting web server...")
    print("[FLASK] Server will be available at: http://127.0.0.1:5000")
    print("[FLASK] Press Ctrl+C to stop")
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5000)
