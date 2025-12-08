"""
Custom Policy: Ensure no hardcoded secrets in ENV instructions
ID: CKV_CUSTOM_17
Category: SECRETS

This policy checks that ENV instructions don't contain hardcoded secrets
like API keys, passwords, or tokens which should be passed at runtime instead.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import re
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class NoHardcodedSecrets(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure no hardcoded secrets in ENV instructions"
        id = "CKV_CUSTOM_17"
        supported_instructions = ("ENV",)
        categories = (CheckCategories.SECRETS,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan ENV instructions for potential hardcoded secrets
        """
        # Common secret patterns
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'auth\s*=\s*["\'][^"\']+["\']',
        ]
        
        for instruction in conf:
            value = instruction.get("value", "").lower()
            
            # Check for secret patterns
            for pattern in secret_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return CheckResult.FAILED, [instruction]
        
        return CheckResult.PASSED, None


check = NoHardcodedSecrets()