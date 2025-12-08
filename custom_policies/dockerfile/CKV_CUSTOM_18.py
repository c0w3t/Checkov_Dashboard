"""
Custom Policy: Ensure non-root user is created and used
ID: CKV_CUSTOM_18
Category: IAM

This policy checks that Dockerfile creates and uses a non-root user
to follow security best practices and principle of least privilege.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class NonRootUserRequired(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure non-root user is created and used"
        id = "CKV_CUSTOM_18"
        supported_instructions = ("USER", "RUN")
        categories = (CheckCategories.IAM,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan instructions to ensure non-root user is created and used
        """
        has_user_creation = False
        has_user_switch = False
        
        for instruction in conf:
            instruction_type = instruction.get("instruction", "").upper()
            value = instruction.get("value", "").lower()
            
            # Check for user creation in RUN instruction
            if instruction_type == "RUN":
                if any(cmd in value for cmd in ["useradd", "adduser", "groupadd"]):
                    has_user_creation = True
            
            # Check for USER instruction switching to non-root
            if instruction_type == "USER":
                if value.strip() not in ["", "root", "0"]:
                    has_user_switch = True
        
        # Pass if both user creation and switch are found
        if has_user_creation and has_user_switch:
            return CheckResult.PASSED, None
        
        # If no non-root user setup found, fail
        return CheckResult.FAILED, None


check = NonRootUserRequired()