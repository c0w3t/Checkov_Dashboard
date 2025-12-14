"""
AI Service supporting multiple providers (OpenAI, Gemini)
Provides AI-powered features:
1. Auto-generate custom Checkov policies
2. Suggest code fixes for vulnerabilities
3. Edit files with AI assistance
"""
import os
from openai import OpenAI
from typing import Dict, Any, Optional
import logging
try:
    import google.generativeai as genai
except Exception:
    genai = None

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # OpenAI
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        if not self.client:
            logger.warning("OpenAI API key not configured. OpenAI features disabled.")

        # Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.gemini_client_available = False
        if self.gemini_api_key and genai:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Lazy model creation per call; just mark available
                self.gemini_client_available = True
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")

    def is_available(self) -> bool:
        """Check if any AI provider is available"""
        return bool(self.client or self.gemini_client_available)

    def _use_provider(self, provider: Optional[str]) -> str:
        """Resolve provider to use: 'openai' or 'gemini'"""
        prov = (provider or "openai").lower()
        if prov == "gemini" and self.gemini_client_available:
            return "gemini"
        return "openai"

    def generate_custom_policy(
        self,
        policy_name: str,
        description: str,
        framework: str,
        example_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a custom Checkov policy based on user requirements

        Args:
            policy_name: Name of the policy (e.g., "No hardcoded API keys")
            description: Detailed description of what to check
            framework: Target framework (terraform, kubernetes, dockerfile)
            example_code: Optional example of code that should fail the policy

        Returns:
            Dict with policy_code and explanation
        """
        if not self.client:
            raise Exception("OpenAI not available. Please configure OPENAI_API_KEY")

        prompt = f"""Generate a Checkov custom policy in Python.

**Requirements:**
- Policy Name: {policy_name}
- Description: {description}
- Framework: {framework}
- Check ID: CKV_CUSTOM_AI_{framework.upper()}_XXX (replace XXX with appropriate number)

**Guidelines:**
1. Use Checkov's base check classes for {framework}
2. Include proper imports
3. Add detailed check message
4. Handle edge cases
5. Return PASSED or FAILED appropriately

{f'**Example code that should FAIL:**\\n```\\n{example_code}\\n```' if example_code else ''}

**Output format:**
```python
from checkov.common.models.enums import CheckResult, CheckCategories
# ... (add appropriate imports for {framework})

class Check{policy_name.replace(' ', '')}(BaseCheck):
    def __init__(self):
        name = "{policy_name}"
        id = "CKV_CUSTOM_AI_{framework.upper()}_XXX"
        supported_resources = [...]  # List appropriate resources
        categories = [CheckCategories.SECURITY]  # or other category
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf, entity_type):
        # Implementation here
        # Return CheckResult.PASSED or CheckResult.FAILED
        pass

check = Check{policy_name.replace(' ', '')}()
```

Generate ONLY the Python code, no explanations before or after."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in security policy development for Checkov, a static code analysis tool. Generate clean, working Python code for custom policies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent code generation
            )

            policy_code = response.choices[0].message.content

            # Clean up code blocks if present
            if "```python" in policy_code:
                policy_code = policy_code.split("```python")[1].split("```")[0].strip()
            elif "```" in policy_code:
                policy_code = policy_code.split("```")[1].split("```")[0].strip()

            return {
                "success": True,
                "policy_code": policy_code,
                "explanation": f"Generated custom {framework} policy: {policy_name}",
                "model_used": self.model
            }

        except Exception as e:
            logger.error(f"Failed to generate policy: {e}")
            return {
                "success": False,
                "error": str(e),
                "policy_code": None
            }

    def suggest_fix_for_vulnerability(
        self,
        vulnerability: Dict[str, Any],
        file_content: str,
        file_path: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest code fix for a vulnerability

        Args:
            vulnerability: Vulnerability details (check_id, check_name, description, etc.)
            file_content: Current file content
            file_path: Path to the file

        Returns:
            Dict with suggested_fix (code diff or full content) and explanation
        """
        provider_to_use = self._use_provider(provider)
        if provider_to_use == "openai" and not self.client:
            raise Exception("OpenAI service not available. Please configure OPENAI_API_KEY")
        if provider_to_use == "gemini" and not self.gemini_client_available:
            raise Exception("Gemini service not available. Please configure GEMINI_API_KEY")

        check_id = vulnerability.get('check_id', 'Unknown')
        check_name = vulnerability.get('check_name', 'Unknown')
        description = vulnerability.get('description', 'Security issue')
        line_number = vulnerability.get('line_number', 0)

        # Get file extension to determine language
        file_ext = file_path.split('.')[-1]
        language_map = {
            'tf': 'Terraform',
            'yaml': 'Kubernetes YAML',
            'yml': 'Kubernetes YAML',
            'dockerfile': 'Dockerfile',
            'Dockerfile': 'Dockerfile'
        }
        language = language_map.get(file_ext, 'configuration file')

        prompt = f"""Fix a security vulnerability in a {language}.

**Vulnerability Details:**
- Check ID: {check_id}
- Issue: {check_name}
- Description: {description}
- Location: Line {line_number} in {file_path}

**Current File Content:**
```
{file_content}
```

**Task:**
1. Identify the exact security issue
2. Provide the fixed version of the ENTIRE file
3. Explain what was changed and why

**Output format:**
EXPLANATION:
[Brief explanation of the issue and fix]

FIXED_CODE:
```
[Complete fixed file content]
```

Generate ONLY the explanation and fixed code as specified above."""

        try:
            if provider_to_use == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a security expert specializing in fixing infrastructure-as-code vulnerabilities. Always provide complete, working code fixes."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                model_used = self.model
            else:
                # Gemini
                model = genai.GenerativeModel(self.gemini_model_name)
                resp = model.generate_content([
                    {"role": "system", "parts": ["You are a security expert specializing in fixing infrastructure-as-code vulnerabilities. Always provide complete, working code fixes."]},
                    {"role": "user", "parts": [prompt]},
                ])
                content = getattr(resp, "text", "")
                model_used = self.gemini_model_name

            # Parse response
            explanation = ""
            fixed_code = file_content  # Fallback to original

            if "EXPLANATION:" in content and "FIXED_CODE:" in content:
                parts = content.split("FIXED_CODE:")
                explanation = parts[0].replace("EXPLANATION:", "").strip()

                code_part = parts[1].strip()
                if "```" in code_part:
                    fixed_code = code_part.split("```")[1].split("```")[0].strip()
                else:
                    fixed_code = code_part.strip()
            else:
                # Fallback parsing
                explanation = "AI suggested fix (parsing may be incomplete)"
                if "```" in content:
                    fixed_code = content.split("```")[1].split("```")[0].strip()

            return {
                "success": True,
                "explanation": explanation,
                "fixed_code": fixed_code,
                "original_code": file_content,
                "changes_made": True,
                "model_used": model_used,
            }

        except Exception as e:
            logger.error(f"Failed to suggest fix: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixed_code": None
            }

    def edit_file_with_ai(
        self,
        file_content: str,
        file_path: str,
        user_instruction: str
    ) -> Dict[str, Any]:
        """
        Edit a file based on user's natural language instruction

        Args:
            file_content: Current file content
            file_path: Path to the file
            user_instruction: What the user wants to change (e.g., "Add encryption to S3 bucket")

        Returns:
            Dict with edited_content and explanation
        """
        if not self.client:
            raise Exception("OpenAI not available. Please configure OPENAI_API_KEY")

        file_ext = file_path.split('.')[-1]
        language_map = {
            'tf': 'Terraform',
            'yaml': 'Kubernetes YAML',
            'yml': 'Kubernetes YAML',
            'dockerfile': 'Dockerfile',
            'Dockerfile': 'Dockerfile'
        }
        language = language_map.get(file_ext, 'configuration file')

        prompt = f"""Edit a {language} based on user instruction.

**File:** {file_path}

**Current Content:**
```
{file_content}
```

**User Instruction:**
{user_instruction}

**Task:**
1. Apply the requested changes to the file
2. Maintain correct syntax and formatting
3. Preserve comments and structure where possible
4. Explain what was changed

**Output format:**
CHANGES:
[Brief summary of changes made]

EDITED_CODE:
```
[Complete edited file content]
```

Generate ONLY the changes summary and edited code as specified above."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert {language} developer. Edit files precisely according to user instructions while maintaining best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content

            # Parse response
            changes = ""
            edited_code = file_content  # Fallback

            if "CHANGES:" in content and "EDITED_CODE:" in content:
                parts = content.split("EDITED_CODE:")
                changes = parts[0].replace("CHANGES:", "").strip()

                code_part = parts[1].strip()
                if "```" in code_part:
                    edited_code = code_part.split("```")[1].split("```")[0].strip()
                else:
                    edited_code = code_part.strip()
            else:
                # Fallback parsing
                changes = "AI made edits (parsing may be incomplete)"
                if "```" in content:
                    edited_code = content.split("```")[1].split("```")[0].strip()

            return {
                "success": True,
                "changes": changes,
                "edited_content": edited_code,
                "original_content": file_content,
                "model_used": self.model
            }

        except Exception as e:
            logger.error(f"Failed to edit file: {e}")
            return {
                "success": False,
                "error": str(e),
                "edited_content": None
            }

    def analyze_vulnerability_severity(
        self,
        check_id: str,
        check_name: str,
        resource_type: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Use AI to analyze and explain vulnerability severity

        Returns:
            Dict with severity_analysis, potential_impact, remediation_steps
        """
        if not self.client:
            raise Exception("OpenAI not available")

        prompt = f"""Analyze this security vulnerability:

**Check ID:** {check_id}
**Check:** {check_name}
**Resource:** {resource_type}
**Description:** {description}

Provide:
1. **Severity Analysis**: Why this is important
2. **Potential Impact**: What could happen if exploited
3. **Remediation Steps**: How to fix it (numbered list)

Be concise and practical."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing infrastructure vulnerabilities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
            )

            content = response.choices[0].message.content

            return {
                "success": True,
                "analysis": content,
                "model_used": self.model
            }

        except Exception as e:
            logger.error(f"Failed to analyze vulnerability: {e}")
            return {
                "success": False,
                "error": str(e)
            }
