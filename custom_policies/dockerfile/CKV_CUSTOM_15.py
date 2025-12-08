"""
Custom Policy: Ensure LABEL metadata exists
ID: CKV_CUSTOM_15
Category: CONVENTION

This policy checks that Dockerfile contains LABEL instructions to provide
metadata about the image, which is important for image management and documentation.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class LabelMetadataRequired(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure LABEL metadata exists"
        id = "CKV_CUSTOM_15"
        supported_instructions = ("LABEL",)
        categories = (CheckCategories.CONVENTION,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Check if Dockerfile has LABEL instruction
        """
        for instruction in conf:
            value = instruction.get("value", "")
            
            # If we find any LABEL instruction with content, pass
            if value.strip():
                return CheckResult.PASSED, None
        
        # No LABEL found or empty LABEL
        return CheckResult.FAILED, None


check = LabelMetadataRequired()
