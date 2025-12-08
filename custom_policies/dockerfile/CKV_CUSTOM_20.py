"""
Custom Policy: Ensure package manager cache is cleaned after installation
ID: CKV_CUSTOM_20
Category: GENERAL_SECURITY

This policy checks that RUN instructions clean package manager cache
after installing packages to reduce image size and security attack surface.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import re
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class PackageManagerCacheCleanup(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure package manager cache is cleaned after installation"
        id = "CKV_CUSTOM_20"
        supported_instructions = ("RUN",)
        categories = (CheckCategories.GENERAL_SECURITY,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan RUN instructions to ensure package cache cleanup after installation
        """
        failed_instructions = []
        
        # Package manager installation patterns and their cleanup commands
        package_patterns = {
            r'apt-get\s+install': [r'apt-get\s+clean', r'rm\s+-rf\s+/var/lib/apt/lists'],
            r'apk\s+add': [r'apk\s+del\s+.*build-deps', r'rm\s+-rf\s+/var/cache/apk'],
            r'yum\s+install': [r'yum\s+clean\s+all', r'rm\s+-rf\s+/var/cache/yum'],
            r'dnf\s+install': [r'dnf\s+clean\s+all', r'rm\s+-rf\s+/var/cache/dnf'],
            r'pip\s+install': [r'pip\s+cache\s+purge', r'rm\s+-rf\s+/root/\.cache/pip'],
        }
        
        for instruction in conf:
            value = instruction.get("value", "")
            
            # Check each package manager pattern
            for install_pattern, cleanup_patterns in package_patterns.items():
                if re.search(install_pattern, value, re.IGNORECASE):
                    # Check if any cleanup pattern is present
                    has_cleanup = any(
                        re.search(cleanup_pattern, value, re.IGNORECASE) 
                        for cleanup_pattern in cleanup_patterns
                    )
                    
                    if not has_cleanup:
                        failed_instructions.append(instruction)
                        break  # One failure per instruction is enough
        
        if failed_instructions:
            return CheckResult.FAILED, failed_instructions
        
        return CheckResult.PASSED, None


check = PackageManagerCacheCleanup()