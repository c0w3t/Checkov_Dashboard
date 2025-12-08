"""
Severity Mapping for Checkov Checks

Since Checkov open-source doesn't return severity without Prisma Cloud API key,
we maintain our own severity mapping based on security best practices.

Severity Levels:
- CRITICAL: Immediate risk of data breach, credential exposure, or system compromise
- HIGH: Significant security risk that should be fixed soon
- MEDIUM: Moderate security issue, recommended to fix
- LOW: Minor security improvement or best practice
- INFO: Informational, no immediate security impact
"""

# ============================================================================
# CRITICAL SEVERITY - Immediate security risks
# ============================================================================
CRITICAL_CHECKS = {
    # Secrets & Credentials
    'CKV_SECRET_*',  # All secret scanning checks
    'CKV_AWS_1',     # Root account usage
    'CKV_AWS_19',    # S3 encryption at rest
    'CKV_AWS_21',    # S3 versioning (prevents data loss)
    'CKV_AWS_40',    # IAM policy attached to users
    'CKV_AWS_41',    # IAM policy attached to groups or roles
    'CKV_AWS_61',    # IAM password policy - require symbols
    'CKV_AWS_62',    # IAM password policy - require numbers

    # Kubernetes Security - Built-in
    'CKV_K8S_16',    # Container should not be privileged
    'CKV_K8S_17',    # Containers should not share the host process ID namespace
    'CKV_K8S_18',    # Containers should not share the host IPC namespace
    'CKV_K8S_19',    # Containers should not share the host network namespace

    # Kubernetes Security - Custom Policies (CRITICAL privilege escalation risks)
    'CKV_K8S_CUSTOM_13',  # Ensure containers run as non-root user
    'CKV_K8S_CUSTOM_15',  # Containers should not run with allowPrivilegeEscalation
    'CKV_K8S_CUSTOM_16',  # Container should not be privileged

    # Docker - Custom Policies (CRITICAL secrets exposure)
    'CKV_CUSTOM_17',  # Ensure no hardcoded secrets in ENV instructions

    # Docker
    'CKV_DOCKER_7',  # Ensure the base image uses a non latest version tag
}

# ============================================================================
# HIGH SEVERITY - Significant security risks
# ============================================================================
HIGH_CHECKS = {
    # Encryption
    'CKV_AWS_4',     # Ensure all data stored in the Launch configuration EBS is securely encrypted
    'CKV_AWS_7',     # Ensure rotation for customer created CMKs is enabled
    'CKV_AWS_18',    # Ensure the S3 bucket has access logging enabled
    'CKV_AWS_26',    # Ensure all data stored in the SNS topic is encrypted
    'CKV_AWS_27',    # Ensure all data stored in the SQS queue is encrypted
    'CKV_AWS_33',    # Ensure KMS key policy does not contain wildcard principal

    # IAM & Access Control
    'CKV_AWS_109',   # Ensure IAM policies does not allow permissions management
    'CKV_AWS_110',   # Ensure IAM policies does not allow privilege escalation
    'CKV_AWS_111',   # Ensure IAM policies does not allow write access without constraints
    'CKV_AWS_283',   # Ensure no IAM policies allow ALL or any AWS principal
    'CKV_AWS_356',   # Ensure no IAM policies documents allow "*" as statement's resource

    # Database Security
    'CKV_AWS_16',    # Ensure all data stored in the RDS is securely encrypted at rest
    'CKV_AWS_17',    # Ensure all data stored in RDS is not publicly accessible
    'CKV_AWS_23',    # Ensure RDS database has encryption at rest enabled
    'CKV_AWS_118',   # Ensure that enhanced monitoring is enabled for Amazon RDS instances

    # Network Security
    'CKV_AWS_23',    # Ensure every security group rule has a description
    'CKV_AWS_24',    # Ensure no security groups allow ingress from 0.0.0.0:0 to port 22
    'CKV_AWS_25',    # Ensure no security groups allow ingress from 0.0.0.0:0 to port 3389
    'CKV_AWS_260',   # Ensure no security groups allow ingress from 0.0.0.0:0 to port 80

    # Kubernetes
    'CKV_K8S_20',    # Containers should not run with allowPrivilegeEscalation
    'CKV_K8S_23',    # Minimize the admission of root containers
    'CKV_K8S_28',    # Minimize the admission of containers with NET_RAW capability
    'CKV_K8S_29',    # Apply security context to your pods and containers
    'CKV_K8S_30',    # Apply security context to your containers
    'CKV_K8S_37',    # Minimize the admission of containers with capabilities assigned

    # ========== CUSTOM POLICIES - HIGH SEVERITY ==========

    # Terraform - Encryption (Custom)
    'CKV_TF_CUSTOM_10',  # Ensure all data stored in EBS is securely encrypted
    'CKV_TF_CUSTOM_13',  # Ensure S3 bucket has server side encryption enabled
    'CKV_TF_CUSTOM_16',  # Ensure RDS database has encryption enabled

    # Terraform - IAM (Custom)
    'CKV_TF_CUSTOM_14',  # Ensure S3 bucket has MFA delete enabled

    # Terraform - Networking (Custom) - High risk exposure
    'CKV_TF_CUSTOM_15',  # Ensure Instance Metadata Service Version 1 is not enabled (IMDSv2 required)
    'CKV_TF_CUSTOM_19',  # Ensure no public IPs are assigned (direct internet exposure)

    # Dockerfile - IAM (Custom)
    'CKV_CUSTOM_18',  # Ensure non-root user is created and used
    'CKV_CUSTOM_19',  # Ensure least privilege principles are followed

    # Dockerfile - Networking (Custom) - RCE risk
    'CKV_CUSTOM_13',  # Ensure debug port 9229 is not exposed (Node.js remote debugging)
}

# ============================================================================
# MEDIUM SEVERITY - Moderate security issues
# ============================================================================
MEDIUM_CHECKS = {
    # Logging & Monitoring
    'CKV_AWS_6',     # Ensure all S3 buckets have server access logging enabled
    'CKV_AWS_18',    # Ensure the S3 bucket has access logging enabled
    'CKV_AWS_35',    # Ensure CloudTrail logs are encrypted at rest using KMS CMKs
    'CKV_AWS_36',    # Ensure CloudTrail log file validation is enabled
    'CKV_AWS_67',    # Ensure that CloudWatch Log Group specifies retention days

    # Backup & Recovery
    'CKV_AWS_10',    # Ensure that RDS instances have backup enabled
    'CKV_AWS_129',   # Ensure that respective logs of Amazon Relational Database Service are enabled
    'CKV_AWS_133',   # Ensure that RDS instances has backup policy
    'CKV_AWS_144',   # Ensure that S3 bucket has cross-region replication enabled
    'CKV_AWS_145',   # Ensure that S3 buckets are encrypted with KMS by default

    # Network Configuration
    'CKV_AWS_20',    # S3 Bucket has an ACL defined which allows public READ access
    'CKV_AWS_21',    # Ensure all data stored in the S3 bucket have versioning enabled
    'CKV_AWS_53',    # Ensure S3 bucket has block public ACLS enabled
    'CKV_AWS_54',    # Ensure S3 bucket has block public policy enabled
    'CKV_AWS_55',    # Ensure S3 bucket has ignore public ACLs enabled
    'CKV_AWS_56',    # Ensure S3 bucket has 'restrict_public_bucket' enabled

    # Kubernetes
    'CKV_K8S_8',     # Liveness Probe Should be Configured
    'CKV_K8S_9',     # Readiness Probe Should be Configured
    'CKV_K8S_10',    # CPU requests should be set
    'CKV_K8S_11',    # CPU limits should be set
    'CKV_K8S_12',    # Memory requests should be set
    'CKV_K8S_13',    # Memory limits should be set
    'CKV_K8S_14',    # Image Tag should be fixed - not latest or blank
    'CKV_K8S_21',    # The default namespace should not be used
    'CKV_K8S_22',    # Use read-only filesystem for containers where possible
    'CKV_K8S_31',    # Ensure that the seccomp profile is set to docker/default
    'CKV_K8S_38',    # Ensure that Service Account Tokens are only mounted where necessary
    'CKV_K8S_40',    # Containers should run as a high UID to avoid host conflict
    'CKV_K8S_43',    # Image should use digest
    'CKV2_K8S_6',    # Minimize the admission of pods which lack NetworkPolicy

    # Docker
    'CKV_DOCKER_1',  # Ensure port 22 is not exposed
    'CKV_DOCKER_2',  # Ensure that HEALTHCHECK instructions have been added
    'CKV_DOCKER_3',  # Ensure that a user for the container has been created
    'CKV_DOCKER_8',  # Ensure the last USER is not root
    'CKV2_DOCKER_8', # Ensure apt-get not use --allow-unauthenticated

    # ========== CUSTOM POLICIES - MEDIUM SEVERITY ==========

    # Terraform - Logging (Custom)
    'CKV_TF_CUSTOM_12',  # Ensure CloudTrail logging is enabled
    'CKV_TF_CUSTOM_18',  # Ensure VPC flow logs are enabled

    # Terraform - Backup & Recovery (Custom)
    'CKV_TF_CUSTOM_11',  # Ensure S3 bucket has versioning enabled
    'CKV_TF_CUSTOM_17',  # Ensure RDS database has backup enabled

    # Dockerfile - Supply Chain (Custom)
    'CKV_CUSTOM_11',  # Ensure apt-get clean after apt-get install
    'CKV_CUSTOM_12',  # Ensure COPY does not copy entire build context
    'CKV_CUSTOM_14',  # Ensure secure base image is used

    # Kubernetes - Supply Chain & Security (Custom)
    'CKV_K8S_CUSTOM_10',  # Image should be from allowed registries
    'CKV_K8S_CUSTOM_11',  # Ensure Service Account Tokens are only mounted where necessary
    'CKV_K8S_CUSTOM_12',  # Ensure resource limits are set
    'CKV_K8S_CUSTOM_14',  # Ensure containers use read-only root filesystem
    'CKV_K8S_CUSTOM_17',  # Ensure NetworkPolicy is defined
    'CKV_K8S_CUSTOM_18',  # Ensure PodSecurityPolicy is configured
    'CKV_K8S_CUSTOM_19',  # Ensure RBAC is properly configured

    # Dockerfile - General Security (Custom)
    'CKV_CUSTOM_20',  # Ensure Dockerfile follows general security best practices
}

# ============================================================================
# LOW SEVERITY - Best practices and conventions
# ============================================================================
LOW_CHECKS = {
    # General Best Practices
    'CKV_AWS_126',   # Ensure that RDS instances use tags
    'CKV_AWS_153',   # Ensure that S3 buckets are encrypted with KMS by default
    'CKV_AWS_195',   # Ensure Glue Data Catalog Connection is set to encrypt connection passwords

    # Tagging & Organization
    'CKV_AWS_8',     # Ensure all resources that can be tagged have tags

    # Kubernetes
    'CKV_K8S_35',    # Prefer using secrets as files over secrets as environment variables

    # ========== CUSTOM POLICIES - LOW SEVERITY ==========

    # Dockerfile - Convention (Custom)
    'CKV_CUSTOM_15',  # Ensure LABEL metadata exists
    'CKV_CUSTOM_16',  # Ensure Dockerfile follows naming conventions
}


def get_severity_for_check(check_id: str, category: str = None) -> str:
    """
    Get severity level for a Checkov check ID with context-aware logic

    Args:
        check_id: Checkov check ID (e.g., "CKV_AWS_1")
        category: Optional category from Checkov (e.g., "ENCRYPTION")

    Returns:
        Severity level: CRITICAL, HIGH, MEDIUM, LOW, or INFO
    """
    # Check explicit mappings first (highest priority)
    if check_id in CRITICAL_CHECKS:
        return 'CRITICAL'

    if check_id in HIGH_CHECKS:
        return 'HIGH'

    if check_id in MEDIUM_CHECKS:
        return 'MEDIUM'

    if check_id in LOW_CHECKS:
        return 'LOW'

    # Check wildcard patterns
    if check_id.startswith('CKV_SECRET'):
        return 'CRITICAL'

    # ========== Context-aware logic for custom policies ==========

    # Kubernetes Security Context - Privilege Escalation (CRITICAL)
    if category and category.upper() == 'KUBERNETES':
        check_id_lower = check_id.lower()
        # Check for privilege-related patterns
        if any(keyword in check_id_lower for keyword in ['root', 'privileged', 'escalation']):
            return 'CRITICAL'
        # Check for host access patterns
        if any(keyword in check_id_lower for keyword in ['hostnetwork', 'hostpid', 'hostipc']):
            return 'CRITICAL'
        # Check for capability/security context patterns
        if any(keyword in check_id_lower for keyword in ['capability', 'securitycontext', 'token']):
            return 'HIGH'

    # Networking - Exposure & Attack Surface (HIGH)
    if category and category.upper() == 'NETWORKING':
        check_id_lower = check_id.lower()
        # Debug ports, IMDS, public exposure
        if any(keyword in check_id_lower for keyword in ['debug', 'imds', 'public', 'expose', '0.0.0.0']):
            return 'HIGH'
        # SSH, RDP, sensitive ports
        if any(keyword in check_id_lower for keyword in ['22', '3389', 'ssh', 'rdp']):
            return 'HIGH'

    # Dockerfile IAM - Non-root user (HIGH)
    if category and category.upper() == 'IAM':
        check_id_lower = check_id.lower()
        if 'custom' in check_id_lower and 'docker' in check_id_lower:
            # Dockerfile IAM policies should be HIGH
            return 'HIGH'

    # ========== Fallback to category-based mapping ==========

    if category:
        category_upper = category.upper()

        # CRITICAL keywords
        if any(word in category_upper for word in ['SECRET', 'PASSWORD', 'CREDENTIAL', 'KEY']):
            return 'CRITICAL'

        # HIGH keywords
        if any(word in category_upper for word in ['ENCRYPTION', 'IAM', 'RBAC', 'AUTHENTICATION']):
            return 'HIGH'

        # MEDIUM keywords
        if any(word in category_upper for word in ['NETWORKING', 'LOGGING', 'MONITORING', 'BACKUP', 'RECOVERY']):
            return 'MEDIUM'

        # LOW keywords
        if any(word in category_upper for word in ['CONVENTION', 'GENERAL', 'BEST_PRACTICE']):
            return 'LOW'

        # Check CATEGORY_SEVERITY_MAP
        if category_upper in CATEGORY_SEVERITY_MAP:
            return CATEGORY_SEVERITY_MAP[category_upper]

    # Default to MEDIUM if unknown
    return 'MEDIUM'


# ============================================================================
# Category-based severity mapping (fallback)
# ============================================================================
CATEGORY_SEVERITY_MAP = {
    # Critical categories - Immediate security risks
    'SECRETS': 'CRITICAL',

    # High severity categories - Significant security risks
    'IAM': 'HIGH',
    'ENCRYPTION': 'HIGH',
    'AUTHENTICATION': 'HIGH',
    'RBAC': 'HIGH',

    # Medium severity categories - Moderate security issues
    'NETWORKING': 'MEDIUM',
    'LOGGING': 'MEDIUM',
    'MONITORING': 'MEDIUM',
    'BACKUP': 'MEDIUM',
    'BACKUP_AND_RECOVERY': 'MEDIUM',
    'SUPPLY_CHAIN': 'MEDIUM',
    'KUBERNETES': 'MEDIUM',  # Default for K8s - specific checks override this
    'GENERAL_SECURITY': 'MEDIUM',

    # Low severity categories - Best practices
    'GENERAL': 'LOW',
    'CONVENTION': 'LOW',
    'BEST_PRACTICE': 'LOW',
}
