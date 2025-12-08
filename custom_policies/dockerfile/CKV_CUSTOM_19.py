"""
Custom Policy: Ensure COPY/ADD instructions use --chown flag when copying files
ID: CKV_CUSTOM_19
Category: IAM

This policy checks that COPY and ADD instructions use the --chown flag to 
explicitly set file ownership, preventing security issues from default root ownership.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class CopyAddWithChown(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure COPY/ADD instructions use --chown flag"
        id = "CKV_CUSTOM_19"
        supported_instructions = ("COPY", "ADD")
        categories = (CheckCategories.IAM,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan COPY/ADD instructions to ensure they use --chown flag
        """
        failed_instructions = []
        
        for instruction in conf:
            value = instruction.get("value", "").strip()
            
            # Skip if instruction copies from another stage (multi-stage builds)
            if "--from=" in value:
                continue
                
            # Check if --chown flag is present
            if "--chown=" not in value:
                failed_instructions.append(instruction)
        
        if failed_instructions:
            return CheckResult.FAILED, failed_instructions
        
        return CheckResult.PASSED, None


check = CopyAddWithChown()