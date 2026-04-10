"""Secret detection patterns and regex rules"""
import re
from typing import Dict, List, Tuple

class SecretPatterns:
    """Collection of regex patterns to detect various secret types"""
    
    # AWS Access Key - format: AKIA + 16 alphanumeric characters
    AWS_ACCESS_KEY = {
        "pattern": r"AKIA[0-9A-Z]{16}",
        "type": "aws_key",
        "confidence": 0.95,
        "description": "AWS Access Key ID"
    }
    
    # AWS Secret Key - typically 40 characters, alphanumeric with +/
    AWS_SECRET_KEY = {
        "pattern": r"aws_secret_access_key.*(?i)[\s=]*[a-zA-Z0-9/+=]{40}",
        "type": "aws_secret",
        "confidence": 0.85,
        "description": "AWS Secret Access Key"
    }
    
    # Google API Key - AIza format
    GOOGLE_API_KEY = {
        "pattern": r"AIza[0-9A-Za-z\-_]{35}",
        "type": "google_api_key",
        "confidence": 0.90,
        "description": "Google API Key"
    }
    
    # Google Service Account
    GOOGLE_SERVICE_ACCOUNT = {
        "pattern": r"\"type\"\s*:\s*\"service_account\"",
        "type": "google_service_account",
        "confidence": 0.80,
        "description": "Google Service Account JSON"
    }
    
    # OpenAI API Key - sk- format
    OPENAI_API_KEY = {
        "pattern": r"sk-[a-zA-Z0-9]{20,}",
        "type": "openai_key",
        "confidence": 0.90,
        "description": "OpenAI API Key"
    }
    
    # Claude API Key
    CLAUDE_API_KEY = {
        "pattern": r"claude-[a-zA-Z0-9]{20,}",
        "type": "claude_key",
        "confidence": 0.90,
        "description": "Anthropic Claude API Key"
    }
    
    # Gemini API Key
    GEMINI_API_KEY = {
        "pattern": r"AIza[0-9A-Za-z\-_]{35}",  # Similar to Google API Key
        "type": "gemini_key",
        "confidence": 0.85,
        "description": "Google Gemini API Key"
    }
    
    # GitHub Token - ghp_ format (Personal Access Token)
    GITHUB_TOKEN = {
        "pattern": r"ghp_[a-zA-Z0-9]{36}",
        "type": "github_token",
        "confidence": 0.95,
        "description": "GitHub Personal Access Token"
    }
    
    # GitHub OAuth Token
    GITHUB_OAUTH_TOKEN = {
        "pattern": r"ghu_[a-zA-Z0-9]{36}",
        "type": "github_oauth",
        "confidence": 0.95,
        "description": "GitHub OAuth Token"
    }
    
    # GitHub App Token
    GITHUB_APP_TOKEN = {
        "pattern": r"ghs_[a-zA-Z0-9]{36}",
        "type": "github_app_token",
        "confidence": 0.95,
        "description": "GitHub App Token"
    }
    
    # Slack Bot Token
    SLACK_BOT_TOKEN = {
        "pattern": r"xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9_-]{32}",
        "type": "slack_bot_token",
        "confidence": 0.90,
        "description": "Slack Bot Token"
    }
    
    # Slack User Token
    SLACK_USER_TOKEN = {
        "pattern": r"xoxp-[0-9]+-[0-9]+-[0-9]+-[a-zA-Z0-9_-]{32}",
        "type": "slack_user_token",
        "confidence": 0.90,
        "description": "Slack User Token"
    }
    
    # Slack Webhook
    SLACK_WEBHOOK = {
        "pattern": r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_-]+/B[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+",
        "type": "slack_webhook",
        "confidence": 0.95,
        "description": "Slack Webhook URL"
    }
    
    # SSH Private Key
    SSH_PRIVATE_KEY = {
        "pattern": r"-----BEGIN\s+(RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY",
        "type": "ssh_private_key",
        "confidence": 0.99,
        "description": "SSH Private Key"
    }
    
    # PGP Private Key
    PGP_PRIVATE_KEY = {
        "pattern": r"-----BEGIN\s+PGP\s+PRIVATE\s+KEY",
        "type": "pgp_private_key",
        "confidence": 0.99,
        "description": "PGP Private Key"
    }
    
    # Database Connection Strings
    MONGODB_URI = {
        "pattern": r"mongodb(\+srv)?://[a-zA-Z0-9_\-:]+@[a-zA-Z0-9_\-.:]+",
        "type": "mongodb_uri",
        "confidence": 0.85,
        "description": "MongoDB Connection String"
    }
    
    # PostgreSQL Connection String
    POSTGRES_URI = {
        "pattern": r"postgres(ql)?://[a-zA-Z0-9_\-:]+@[a-zA-Z0-9_\-.:]+(?:/[a-zA-Z0-9_\-]+)?",
        "type": "postgres_uri",
        "confidence": 0.85,
        "description": "PostgreSQL Connection String"
    }
    
    # MySQL Connection String
    MYSQL_URI = {
        "pattern": r"mysql://[a-zA-Z0-9_\-:]+@[a-zA-Z0-9_\-.:]+(?:/[a-zA-Z0-9_\-]+)?",
        "type": "mysql_uri",
        "confidence": 0.85,
        "description": "MySQL Connection String"
    }
    
    # JWT Token
    JWT_TOKEN = {
        "pattern": r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}",
        "type": "jwt_token",
        "confidence": 0.75,
        "description": "JWT Token"
    }
    
    # API Key (generic)
    API_KEY_GENERIC = {
        "pattern": r"api[_-]?key[\s=:]*['\"]?[a-zA-Z0-9_\-]{20,}['\"]?",
        "type": "api_key",
        "confidence": 0.60,
        "description": "Generic API Key"
    }
    
    # Bearer Token
    BEARER_TOKEN = {
        "pattern": r"bearer[\s]+[a-zA-Z0-9_\-\.]{20,}",
        "type": "bearer_token",
        "confidence": 0.65,
        "description": "Bearer Token"
    }
    
    # Password in connection string
    PASSWORD_HARDCODED = {
        "pattern": r"password[\s=:]*['\"]?[a-zA-Z0-9_\-!@#$%^&*()]{8,}['\"]?",
        "type": "hardcoded_password",
        "confidence": 0.70,
        "description": "Hardcoded Password"
    }

class PatternMatcher:
    """Matcher for detecting secrets in code"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    @staticmethod
    def _load_patterns() -> Dict[str, Dict]:
        """Load all secret patterns"""
        patterns = {}
        for attr_name in dir(SecretPatterns):
            if not attr_name.startswith('_'):
                attr = getattr(SecretPatterns, attr_name)
                if isinstance(attr, dict) and 'pattern' in attr:
                    patterns[attr_name] = attr
        return patterns
    
    def find_secrets(self, content: str) -> List[Tuple[str, str, float, int, str]]:
        """
        Find secrets in content
        
        Returns:
            List of tuples: (secret_type, matched_value, confidence, line_number, pattern_name)
        """
        secrets = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern_name, pattern_info in self.patterns.items():
                try:
                    regex = re.compile(pattern_info['pattern'], re.IGNORECASE | re.MULTILINE)
                    matches = regex.finditer(line)
                    
                    for match in matches:
                        secret_type = pattern_info['type']
                        matched_value = match.group(0)[:100]  # First 100 chars
                        confidence = pattern_info['confidence']
                        
                        # Skip false positives
                        if not self._is_likely_false_positive(matched_value, secret_type):
                            secrets.append((
                                secret_type,
                                matched_value,
                                confidence,
                                line_num,
                                pattern_name
                            ))
                except re.error:
                    continue
        
        return secrets
    
    @staticmethod
    def _is_likely_false_positive(value: str, secret_type: str) -> bool:
        """Check if the matched value is likely a false positive"""
        # Examples and placeholder patterns
        false_positive_indicators = [
            'example',
            'placeholder',
            'sample',
            'test',
            'dummy',
            'fake',
            'xxx',
            'xxxxxxx',
            'your_',
            '<',
            '>',
            '${',
            '{{',
        ]
        
        value_lower = value.lower()
        for indicator in false_positive_indicators:
            if indicator in value_lower:
                return True
        
        return False
