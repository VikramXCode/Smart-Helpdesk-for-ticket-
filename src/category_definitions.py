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
        Physical device hardware equipment problems and failures including computers laptops desktops workstations
        monitors displays screens keyboards mice touchpads printers scanners copiers multifunction devices
        docking stations port replicators USB hubs cables adapters dongles chargers power supplies batteries
        mobile devices smartphones tablets iPads Android phones headphones headsets microphones webcams cameras
        speakers audio equipment external drives hard drives SSDs flash drives memory cards peripherals
        network cards WiFi adapters bluetooth devices graphics cards RAM memory upgrades component replacement
        device not working not powering on boot failures BIOS errors POST errors hardware malfunction
        physical damage broken screen cracked display liquid damage overheating fan noise strange sounds
        connectivity issues port problems device not recognized not detected driver issues firmware problems
        warranty repair RMA replacement request setup installation configuration ergonomic equipment
        standing desk monitor arm keyboard tray wrist rest footrest lumbar support accessories
    """,
    
    "Software": """
        Application software program tool utility installation configuration crashes freezing hanging
        errors bugs glitches exceptions slow performance lag latency response time version updates patches
        upgrades compatibility problems dependencies conflicts DLL errors registry issues corrupted files
        license activation key validation subscription renewal expired trial feature not working
        Microsoft Office Word Excel PowerPoint Outlook OneNote Publisher Access Project Visio
        Adobe Creative Cloud Photoshop Illustrator InDesign Premiere Acrobat Reader PDF issues
        web browsers Chrome Firefox Edge Safari extensions add-ins plugins bookmarks favorites
        email clients Thunderbird Mail Apple Mail calendar contacts synchronization IMAP POP3 SMTP
        communication collaboration Slack Microsoft Teams Zoom WebEx Skype Google Meet chat messaging
        development tools IDEs Visual Studio VS Code IntelliJ Eclipse PyCharm Sublime Text Atom
        version control Git GitHub GitLab Bitbucket SVN Mercurial repository commits branches merges
        business applications ERP CRM SAP Salesforce Oracle NetSuite Workday ServiceNow QuickBooks
        productivity tools Evernote Notion Trello Asana Monday Jira project management task tracking
        antivirus McAfee Norton Symantec Windows Defender malware detection false positive quarantine
        third-party custom in-house legacy proprietary software package application app program tool
    """,
    
    "Network": """
        Network connectivity communication internet connection problems WiFi wireless ethernet wired LAN WAN
        VPN virtual private network remote access Cisco AnyConnect GlobalProtect FortiClient OpenVPN
        connection drops disconnects timeout unstable intermittent slow speed bandwidth throughput latency
        ping packet loss jitter DNS domain name resolution DHCP IP address assignment conflict duplicate
        proxy settings configuration PAC file authentication firewall blocking ports security groups ACL
        cannot access reach connect to websites services resources internal external intranet extranet
        router switch gateway modem access point WAP configuration SSID network name password WPA WPA2
        network drive mapped drive share folder UNC path file server NAS network attached storage SMB CIFS
        load balancer traffic routing BGP OSPF failover redundancy high availability network outage downtime
        VLAN subnet segmentation NAT port forwarding DMZ perimeter firewall rules policies QoS quality of service
        SSL VPN split tunnel full tunnel route propagation network path MTU fragmentation TCP UDP protocols
        network interface card NIC teaming bonding aggregation link speed duplex auto-negotiation
        network monitoring tools ping traceroute nslookup dig netstat ipconfig ifconfig route arp
    """,
    
    "Access": """
        Access control authentication authorization permission denied forbidden 401 403 errors login sign-in
        account lockout locked disabled suspended deactivated expired password reset change forgotten credentials
        username email verification two-factor 2FA multi-factor MFA authentication code token SMS text message
        authenticator app Google Authenticator Microsoft Authenticator Duo push notification biometric fingerprint
        face recognition Touch ID Face ID Windows Hello smart card PKI certificate CAC PIV hardware token
        single sign-on SSO SAML OAuth OpenID Connect Active Directory LDAP domain controller Kerberos NTLM
        access request provisioning onboarding offboarding role assignment permission grant revoke user creation
        group membership security group distribution list role-based access RBAC attribute-based ABAC least privilege
        SharePoint folder library document permissions read write edit full control contribute view-only
        file share network drive mapped drive access denied insufficient permissions unauthorized
        GitHub repository organization team collaborator read write admin maintainer contributor fork clone
        Jira project issue workflow transition screen field permission scheme role administrator user
        Confluence space page restrictions view edit comment can't create delete move rename
        Salesforce profile permission set object field record type layout sharing rules OWD organization-wide
        ServiceNow role group ACL access control list ITIL table form field read write delete
        cloud platform console portal IAM identity access management policy role service account API key
        database user schema table view stored procedure execute grant privilege DBA read-only read-write
        application module feature function screen report dashboard export import data entry approval workflow
    """,
    
    "Security": """
        Security threat vulnerability risk incident breach attack compromise malware virus trojan worm ransomware
        spyware adware rootkit backdoor exploit zero-day CVE common vulnerabilities exposure CVSS score patch
        phishing spear-phishing whaling social engineering suspicious email link attachment sender domain spoofing
        spam junk quarantine blocked malicious harmful dangerous untrusted certificate invalid unknown publisher
        data breach leak exposure exfiltration unauthorized access disclosure PII personal identifiable information
        GDPR compliance SOX HIPAA PCI-DSS SOC2 audit log monitoring SIEM security information event management
        antivirus anti-malware endpoint protection EDR detection response quarantine scan full quick real-time
        firewall IPS IDS intrusion detection prevention WAF web application DDoS denial of service rate limit
        SSL TLS certificate HTTPS encryption secure connection certificate expired self-signed untrusted CA
        certificate authority chain validation handshake failure protocol version mismatch cipher suite
        VPN encryption IPSec IKE tunnel establishment authentication failure certificate revocation CRL OCSP
        password policy complexity length expiration history reuse lockout threshold account security settings
        privilege escalation lateral movement command and control C2 C&C callback beacon IOC indicator of compromise
        security patch update hotfix vulnerability remediation mitigation workaround compensating control
        security scan penetration test pen-test vulnerability assessment findings recommendations remediation
        access log audit trail user activity session monitoring privileged access PAM bastion jump server
        encryption at rest in transit AES RSA key management key rotation HSM hardware security module
        data loss prevention DLP sensitive data classification confidential restricted public internal
    """,
    
    "Facilities": """
        Physical workplace facility building office environment infrastructure premises real estate
        desk workstation cubicle office space seating assignment hot desk hoteling reservation booking
        chair ergonomic lumbar support adjustable height armrest broken uncomfortable replacement request
        lighting fluorescent LED bulbs flickering dim too bright eye strain glare overhead desk lamp
        temperature HVAC heating ventilation air conditioning thermostat too hot too cold climate control
        building access entry badge key card fob PIN code door lock malfunction stuck jammed emergency exit
        parking garage lot space permit validation visitor temporary reserved handicapped EV charging station
        meeting room conference room huddle space booking reservation Outlook calendar double-booked projector
        phone system extension voicemail transfer conference bridge dial tone static noise call quality
        conference equipment AV audio video HDMI cable adapter screen projection whiteboard markers eraser
        building maintenance janitorial cleaning trash recycling restroom supplies soap paper towels toilet
        breakroom kitchen refrigerator microwave coffee maker water cooler vending machine malfunction empty
        security cameras surveillance access control visitor management sign-in reception lobby front desk
        elevator escalator out of service stuck emergency alarm fire alarm evacuation smoke detector sprinkler
        mailroom package delivery courier FedEx UPS mail slot PO box certified registered tracking
        workplace safety ergonomics ADA compliance accessibility ramp wheelchair elevator Braille signage
        noise level sound loud disruptive construction renovation drilling neighbors music headphones policy
        pets service animals emotional support policy registration documentation requirements restrictions
        plants air quality ventilation fresh air circulation stuffy odor smell HVAC filter dust allergens
        office supplies stationery pens paper notebooks folders binders post-it stapler punch shredder
        IT equipment storage closet server room data center cage rack power cooling cable management
        moving relocation office change floor plan layout seating chart new hire onboarding setup
    """,
    
    "Database": """
        Database data persistence storage query SQL NoSQL relational non-relational RDBMS document key-value
        connection connectivity JDBC ODBC driver connection string DSN timeout refused pooling max connections
        PostgreSQL MySQL MariaDB SQL Server Oracle DB2 Sybase SQLite Teradata Snowflake Redshift BigQuery
        MongoDB Cassandra DynamoDB CosmosDB Couchbase Redis Memcached Elasticsearch Neo4j graph time-series
        query performance slow timeout deadlock blocking lock wait latch contention execution plan index scan
        SELECT INSERT UPDATE DELETE JOIN WHERE GROUP BY ORDER BY aggregate function stored procedure trigger
        schema database table view index constraint primary key foreign key unique nullable column data type
        permission grant revoke role user DBA read-only read-write execute owner schema privilege access denied
        backup restore dump export import migration replication synchronization failover high availability HA
        transaction ACID isolation level commit rollback savepoint dirty read phantom read non-repeatable read
        normalization denormalization 1NF 2NF 3NF BCNF data integrity referential constraint check validation
        ETL extract transform load data warehouse OLAP OLTP star schema fact dimension measure data pipeline
        ORM object-relational mapping Entity Framework Hibernate Sequelize ActiveRecord TypeORM Prisma
        connection pool exhausted leak timeout max size min size idle keepalive health check retry circuit breaker
        error code exception SQL state constraint violation duplicate key null value type mismatch overflow
        performance tuning optimization query plan explain analyze statistics histogram cardinality selectivity
        index B-tree hash GiST GIN covering composite partial expression functional unique clustered non-clustered
        partitioning sharding horizontal vertical range hash consistent hashing distributed scaling replication
        master slave primary replica leader follower read replica eventual consistency strong consistency
        concurrency control pessimistic optimistic locking MVCC multi-version snapshot isolation serializable
    """,
    
    "DevOps": """
        DevOps development operations CI CD continuous integration delivery deployment pipeline automation
        Jenkins GitLab CI CircleCI Travis CI GitHub Actions Azure Pipelines Bamboo TeamCity GoCD Drone Concourse
        build compile test package publish deploy release artifact binary JAR WAR Docker image container registry
        Docker Dockerfile container image layer tag push pull registry Hub ECR ACR GCR authorization authentication
        Kubernetes K8s pod deployment service ingress configmap secret volume PV PVC namespace node cluster context
        kubectl apply create delete get describe logs exec port-forward rollout restart scale autoscale HPA VPA
        Helm chart values template release upgrade rollback repository artifact install uninstall dependency
        Terraform infrastructure as code IaC HCL plan apply destroy state backend remote workspace module provider
        Ansible playbook role task handler variable fact inventory group host SSH WinRM YAML configuration management
        Git version control repository commit branch merge rebase pull push clone fetch tag remote origin upstream
        GitHub GitLab Bitbucket pull request merge request code review approval comment conflict resolve cherry-pick
        npm Node.js package manager install update dependency devDependency package.json package-lock node_modules
        Maven Gradle build tool POM XML dependency plugin goal phase lifecycle repository Nexus Artifactory settings
        pip Python package PyPI requirements.txt setup.py wheel virtualenv venv Poetry Pipenv conda anaconda
        Docker Compose YAML service network volume environment port depends_on build image command entrypoint
        container orchestration swarm stack service task replica rolling update blue-green canary deployment strategy
        monitoring observability logging metrics traces Prometheus Grafana ELK Elastic Logstash Kibana Splunk Datadog
        artifact repository Nexus Artifactory JFrog binary storage versioning snapshot release metadata checksum 
        secret management Vault HashiCorp parameter store secrets manager environment variable credential rotation
        deployment strategy blue-green canary rolling recreate A/B testing feature flag progressive delivery
        GitOps Flux ArgoCD declarative sync drift detection reconciliation reconcile apply prune self-heal
        service mesh Istio Linkerd Consul sidecar proxy envoy traffic routing load balancing retry timeout circuit
    """,
    
    "Cloud": """
        Cloud computing platform provider infrastructure service AWS Amazon Web Services Azure Microsoft Google GCP
        EC2 instance virtual machine VM AMI snapshot EBS volume elastic IP security group subnet VPC region AZ zone
        S3 bucket object storage blob file upload download access denied permission IAM policy presigned URL lifecycle
        Lambda function serverless compute event trigger timeout cold start memory execution role layer runtime
        RDS database Aurora MySQL PostgreSQL SQL Server Oracle MariaDB multi-AZ read replica snapshot backup restore
        IAM identity access management user group role policy permission principal resource action effect condition
        CloudFormation template stack resource parameter output drift change set nested stack cross-stack reference
        CloudWatch logs metrics alarms dashboard namespace dimension statistic threshold period datapoints breach
        Route53 DNS domain hosted zone record A CNAME MX TXT health check routing policy geolocation failover latency
        ELB load balancer ALB application NLB network CLB classic target group health check listener rule routing
        VPC virtual private cloud subnet route table internet gateway NAT gateway VPN peering endpoint PrivateLink
        Azure VM virtual machine resource group subscription tenant availability zone region storage account blob
        Azure AD Active Directory user group application enterprise app SAML OAuth SSO conditional access MFA
        Azure DevOps pipeline release artifact repository board work item query sprint backlog deployment stage gate
        Google Cloud GCP project organization folder billing account service account IAM role permission binding
        GCS Google Cloud Storage bucket object signed URL lifecycle retention versioning uniform bucket-level access
        GCE Compute Engine instance template group snapshot disk image network VPC subnet firewall rule route
        GKE Google Kubernetes Engine cluster node pool workload identity autopilot standard managed upgrade channel
        billing cost budget forecast usage spend commitment reservation savings plan spot instance preemptible
        CloudTrail audit log event trail S3 CloudWatch Logs SNS notification API call user activity governance
        auto-scaling group ASG launch template configuration min max desired capacity scale policy metric cooldown
        container service ECS Fargate task definition service cluster scaling scheduling placement constraint strategy
        API Gateway REST WebSocket HTTP integration method resource deployment stage authorizer API key usage plan
        CDN content delivery network CloudFront distribution origin cache behavior TTL invalidation edge location
        certificate SSL TLS ACM certificate manager validation DNS email wildcard SAN subject alternative name renewal
    """,
    
    "Environment": """
        Development testing staging UAT production environment setup configuration management deployment lifecycle
        local development machine workstation IDE setup dependencies libraries packages modules SDK framework runtime
        Docker container image Dockerfile build run exec volume mount bind network port compose orchestration isolation
        virtual machine VM VirtualBox VMware Hyper-V Vagrant box provisioning snapshot clone linked desktop server
        environment variable env var PATH HOME USER config dotenv .env export set unset shell bash profile rc Windows
        sandbox isolated test experimental feature flag toggle canary beta alpha preview early access limited release
        UAT user acceptance testing QA quality assurance integration system end-to-end E2E regression smoke sanity
        staging pre-production mirror production-like data synthetic anonymized masked subset sample representative
        production live prod release stable GA general availability uptime SLA service level agreement high availability
        configuration file settings properties YAML JSON TOML INI XML environment-specific override merge precedence
        deployment slot blue-green swap traffic routing gradual rollout canary percentage weighted A/B testing
        pipeline stage gate approval manual automatic trigger condition dependency parallel sequential serial workflow
        artifact promote deployment package binary executable JAR WAR ZIP TAR bundle release candidate RC versioning
        infrastructure provisioning Terraform CloudFormation ARM template Pulumi CDK code state plan apply automation
        secrets credentials API key token password certificate encryption vault parameter store environment injection
        database seed fixture migration schema version upgrade downgrade rollback baseline initial incremental change
        test data factory faker mock stub synthetic generated anonymized production subset sanitized GDPR compliance
        feature flag toggle launch darkly split configuration runtime dynamic enable disable experiment cohort segment
        rollback revert restore previous switch failover disaster recovery backup snapshot point-in-time restore PITR
        environment parity development production gap discrepancy drift configuration mismatch version difference
        twelve-factor app methodology stateless config environment dependency build run concurrency disposability logs
    """,
    
    "Other": """
        General inquiry information request question how-to guide tutorial documentation knowledge base FAQ wiki
        training onboarding orientation new hire welcome setup account provision access request form submission
        policy procedure guideline rule regulation standard operating procedure SOP workflow approval process
        offboarding exit termination deactivation access removal asset return equipment laptop phone badge key card
        change request modification feature enhancement improvement suggestion feedback idea brainstorm innovation
        service catalog offering menu available options capabilities scope limitations SLA support tier priority
        incident outage downtime degraded service unavailable maintenance window scheduled unplanned emergency
        request type category classification triage assignment routing escalation handoff transfer ownership
        communication notification announcement broadcast email distribution list all-hands town hall meeting update
        compliance audit regulatory requirement certification SOC2 ISO GDPR HIPAA PCI FEDRAMP NIST framework control
        vendor third-party external supplier partner integration API webhook callback synchronization data exchange
        procurement purchase order PO requisition approval budget cost center billing chargeback allocation tagging
        asset management inventory tracking lifecycle acquisition deployment maintenance retirement disposal CMDB
        capacity planning forecasting trend analysis growth projection scalability elasticity resource optimization
        miscellaneous various other general unclassified uncategorized undefined unknown ambiguous unclear vague
        consultation advisory guidance recommendation expert opinion best practice architecture design review pattern
        project initiative program portfolio milestone deliverable timeline deadline sprint iteration release cycle
        reporting analytics dashboard metrics KPI key performance indicator OKR objective result target goal measure
        feedback survey NPS net promoter score satisfaction CSAT rating review comment suggestion improvement request
        documentation update creation maintenance revision version control publication distribution sharing repository
        automation script tool utility helper agent bot RPA robotic process templating code generation scaffolding
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
