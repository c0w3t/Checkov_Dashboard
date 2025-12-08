"""
Custom Policy: Ensure WORKDIR uses absolute path
ID: CKV_CUSTOM_16
Category: CONVENTION

This policy checks that WORKDIR instruction uses absolute paths rather than
relative paths to ensure consistent and predictable working directory behavior.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class WorkdirAbsolutePath(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure WORKDIR uses absolute path"
        id = "CKV_CUSTOM_16"
        supported_instructions = ("WORKDIR",)
        categories = (CheckCategories.CONVENTION,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan WORKDIR instructions to ensure they use absolute paths
        """
        for instruction in conf:
            value = instruction.get("value", "").strip()
            
            # Check if WORKDIR path is relative (doesn't start with /)
            if value and not value.startswith("/"):
                return CheckResult.FAILED, [instruction]
        
        return CheckResult.PASSED, None


check = WorkdirAbsolutePath()