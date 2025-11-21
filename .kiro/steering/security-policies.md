# Security & Compliance Policies

## Overview

This document outlines security policies, data protection requirements, and compliance guidelines for the Customer Personalization Orchestrator.

---

## Authentication & Authorization

### API Key Management

**Policy**: Never hardcode credentials in source code.

```python
# ❌ WRONG - Never do this
api_key = "sk-abc123..."

# ✅ CORRECT - Use environment variables
import os
api_key = os.getenv("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found in environment")
```

### Secure Storage

- **Development**: Use `.env` file (never commit to git)
- **Production**: Use Azure Key Vault or Managed Identity

```python
# Azure Key Vault integration (production)
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
vault_url = "https://my-keyvault.vault.azure.net/"
client = SecretClient(vault_url=vault_url, credential=credential)

api_key = client.get_secret("openai-api-key").value
```

### Managed Identity (Preferred)

```python
# No credentials needed - uses Azure Managed Identity
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()

client = AzureOpenAI(
    azure_endpoint=endpoint,
    credential=credential  # Secure, no keys in code
)
```

---

## Data Privacy & PII Protection

### PII Handling Policy

**Policy**: Minimize PII in logs, never store PII in artifacts.

### Allowed Data
- Customer ID (anonymized/hashed)
- Aggregate statistics
- Segment characteristics

### Prohibited Data
- Email addresses
- Full names
- Phone numbers
- Payment information
- Precise geolocation

### Implementation

```python
import hashlib

def anonymize_customer_id(customer_id: str) -> str:
    """Hash customer ID for logging."""
    return hashlib.sha256(customer_id.encode()).hexdigest()[:12]

# Usage in logs
logger.info(f"Processing customer {anonymize_customer_id(customer_id)}")
```

### Log Sanitization

```python
import re

def sanitize_log_entry(message: str) -> str:
    """Remove PII from log messages."""
    # Remove email addresses
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
    
    # Remove phone numbers
    message = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', message)
    
    # Remove credit card numbers
    message = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD]', message)
    
    return message

# Custom log handler
class SanitizingHandler(logging.Handler):
    def emit(self, record):
        record.msg = sanitize_log_entry(str(record.msg))
        super().emit(record)
```

---

## Content Safety Policy

### Safety Categories

**Policy**: Block any content with severity > Medium (4) in any category.

| Category | Description | Examples |
|----------|-------------|----------|
| **Hate** | Discrimination, slurs, hate speech | Racist, sexist content |
| **Violence** | Violent content, threats | Graphic violence, threats |
| **Self-Harm** | Self-injury, suicide | Promotion of self-harm |
| **Sexual** | Sexual content | Explicit sexual content |

### Severity Thresholds

```yaml
# config/safety_thresholds.yaml
safety_policy:
  threshold: 4  # Medium
  
  action_by_severity:
    safe: approve
    low: approve_with_warning
    medium: block
    high: block_and_alert
  
  escalation:
    high_severity_count: 3
    alert_email: compliance@example.com
```

### Audit Requirements

**Policy**: Log every safety check decision with immutable audit trail.

```python
def log_safety_decision(variant_id: str, result: dict, audit_file: str = "logs/safety_audit.log"):
    """Append safety decision to immutable audit log."""
    import hashlib
    import json
    from datetime import datetime
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "variant_id": variant_id,
        "status": result["status"],
        "severity_scores": result["severity_scores"],
        "blocked_categories": result.get("blocked_categories", [])
    }
    
    # Calculate hash for integrity
    entry_str = json.dumps(entry, sort_keys=True)
    entry["hash"] = hashlib.sha256(entry_str.encode()).hexdigest()
    
    # Append only (never modify existing entries)
    with open(audit_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")
```

---

## Data Encryption

### Data at Rest

**Policy**: Encrypt sensitive data files.

```python
from cryptography.fernet import Fernet
import os

def encrypt_file(input_file: str, output_file: str, key: bytes = None):
    """Encrypt file with Fernet symmetric encryption."""
    if key is None:
        key = os.getenv("ENCRYPTION_KEY").encode()
    
    fernet = Fernet(key)
    
    with open(input_file, 'rb') as f:
        data = f.read()
    
    encrypted = fernet.encrypt(data)
    
    with open(output_file, 'wb') as f:
        f.write(encrypted)

# Generate key (do once, store securely)
key = Fernet.generate_key()
# Store in Azure Key Vault or .env
```

### Data in Transit

**Policy**: All API calls must use HTTPS.

```python
# Azure SDKs enforce HTTPS by default
# Verify endpoint uses https://
assert endpoint.startswith("https://"), "Endpoint must use HTTPS"
```

---

## Access Control

### File Permissions

```bash
# Restrict access to sensitive files
chmod 600 .env                    # Owner read/write only
chmod 600 config/azure_config.yaml
chmod 400 logs/safety_audit.log   # Owner read-only (immutable)
```

### Code Access

```python
import os
import stat

def ensure_secure_permissions(filepath: str):
    """Ensure file has secure permissions."""
    # Get current permissions
    current_perms = os.stat(filepath).st_mode
    
    # Set to 0600 (owner read/write only)
    secure_perms = stat.S_IRUSR | stat.S_IWUSR
    os.chmod(filepath, secure_perms)
    
    logger.info(f"Secured file: {filepath}")
```

---

## Secrets Management

### Environment Variables (.env)

```bash
# .env file (never commit to git)
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_KEY=sk-xxx
AZURE_SEARCH_ENDPOINT=https://xxx.search.windows.net
AZURE_SEARCH_API_KEY=xxx
AZURE_CONTENT_SAFETY_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_API_KEY=xxx
ENCRYPTION_KEY=xxx
```

### Loading Secrets Securely

```python
from dotenv import load_dotenv
import os

# Load from .env
load_dotenv()

# Validate all required secrets present
required_secrets = [
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_CONTENT_SAFETY_ENDPOINT"
]

missing = [s for s in required_secrets if not os.getenv(s)]
if missing:
    raise EnvironmentError(f"Missing secrets: {missing}")

# Never print secrets
logger.info("✓ All secrets loaded")
# ❌ logger.info(f"API key: {api_key}")  # NEVER DO THIS
```

---

## Compliance Requirements

### GDPR Compliance

**Right to Erasure**: Implement customer data deletion.

```python
def delete_customer_data(customer_id: str):
    """Delete all data for a customer (GDPR compliance)."""
    # Remove from datasets
    customers_df = customers_df[customers_df['customer_id'] != customer_id]
    
    # Remove generated variants
    variants = [v for v in variants if v['customer_id'] != customer_id]
    
    # Remove from experiment results
    # ... remove from all data stores
    
    logger.info(f"Deleted all data for customer {anonymize_customer_id(customer_id)}")
```

**Data Portability**: Export customer data on request.

```python
def export_customer_data(customer_id: str) -> dict:
    """Export all data for a customer (GDPR compliance)."""
    return {
        "customer_profile": get_customer_profile(customer_id),
        "segments": get_customer_segments(customer_id),
        "messages_received": get_customer_messages(customer_id),
        "engagement_history": get_customer_engagement(customer_id)
    }
```

### Audit Trail Requirements

**Policy**: Maintain complete, immutable audit logs for 7 years.

```python
class ImmutableAuditLog:
    """Append-only audit log with integrity checking."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.previous_hash = self._load_last_hash()
    
    def append(self, entry: dict):
        """Append entry with integrity chain."""
        entry["previous_hash"] = self.previous_hash
        entry["timestamp"] = datetime.utcnow().isoformat()
        
        entry_str = json.dumps(entry, sort_keys=True)
        current_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["hash"] = current_hash
        
        with open(self.filepath, 'a') as f:
            f.write(json.dumps(entry) + "\n")
        
        self.previous_hash = current_hash
    
    def _load_last_hash(self) -> str:
        """Load hash of last entry."""
        if not os.path.exists(self.filepath):
            return "0" * 64  # Genesis hash
        
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
            if lines:
                last_entry = json.loads(lines[-1])
                return last_entry.get("hash", "0" * 64)
        return "0" * 64
```

---

## Secure Development Practices

### Code Review Checklist

- [ ] No hardcoded credentials
- [ ] All API calls use HTTPS
- [ ] PII is anonymized in logs
- [ ] Secrets loaded from environment
- [ ] Error messages don't leak sensitive info
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (if using SQL)
- [ ] XSS prevention (if generating HTML)

### Dependency Security

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
```

### Git Security

```bash
# .gitignore - Never commit these
.env
*.key
*.pem
credentials.json
config/secrets/
logs/
data/raw/  # May contain PII
```

```bash
# Check for accidentally committed secrets
git secrets --install
git secrets --register-aws
git secrets --scan
```

---

## Incident Response

### Security Incident Procedure

1. **Detect**: Anomaly detection, alerts
2. **Contain**: Disable compromised credentials immediately
3. **Investigate**: Review audit logs, identify scope
4. **Remediate**: Rotate credentials, patch vulnerabilities
5. **Document**: Record incident, lessons learned
6. **Notify**: Inform affected parties if PII exposed

### Credential Rotation

```python
def rotate_api_key(service: str):
    """Rotate API key for a service."""
    # 1. Generate new key in Azure Portal
    new_key = input("Enter new API key: ")
    
    # 2. Update in Key Vault / environment
    os.environ[f"AZURE_{service.upper()}_API_KEY"] = new_key
    
    # 3. Test with new key
    test_service_connection(service, new_key)
    
    # 4. Revoke old key in Azure Portal
    logger.info(f"✓ Rotated {service} API key")
```

---

## Testing Security

### Security Test Cases

```python
def test_no_pii_in_logs():
    """Verify logs don't contain PII."""
    with open('logs/system.log', 'r') as f:
        logs = f.read()
    
    # Check for email patterns
    assert not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', logs)
    
    # Check for phone numbers
    assert not re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', logs)

def test_api_keys_not_in_code():
    """Verify no API keys in source code."""
    import glob
    
    for filepath in glob.glob('src/**/*.py', recursive=True):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for patterns like "sk-", "api_key = "
        assert 'sk-' not in content
        assert 'api_key = "' not in content

def test_https_endpoints():
    """Verify all endpoints use HTTPS."""
    with open('config/azure_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    for service, settings in config.items():
        if 'endpoint' in settings:
            assert settings['endpoint'].startswith('https://'), \
                f"{service} endpoint must use HTTPS"
```

---

## Compliance Checklist

### Pre-Deployment

- [ ] All credentials stored securely (Key Vault or env vars)
- [ ] No PII in logs
- [ ] Safety screening enabled for all messages
- [ ] Audit logging configured and immutable
- [ ] HTTPS enforced for all API calls
- [ ] Data encryption at rest configured
- [ ] Access controls in place
- [ ] Incident response plan documented
- [ ] Security tests passing
- [ ] Dependencies scanned for vulnerabilities

### Ongoing

- [ ] Regular security audits
- [ ] Credential rotation every 90 days
- [ ] Audit log review monthly
- [ ] Dependency updates quarterly
- [ ] Penetration testing annually
- [ ] Compliance training for team

---

## Security Contact

For security concerns or to report vulnerabilities:
- **Email**: security@example.com
- **Escalation**: On-call security team
- **Response Time**: Critical issues within 4 hours