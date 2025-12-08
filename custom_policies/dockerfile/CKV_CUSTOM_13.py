"""
Custom Policy: Ensure debug port 9229 is not exposed
ID: CKV_CUSTOM_13
Category: NETWORKING

This policy checks that Node.js debug port 9229 is not exposed in production
images, as this can allow remote debugging access and potential security breaches.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class NoDebugPortExposed(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure debug port 9229 is not exposed"
        id = "CKV_CUSTOM_13"
        supported_instructions = ("EXPOSE",)
        categories = (CheckCategories.NETWORKING,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan EXPOSE instructions to ensure debug port 9229 is not exposed
        """
        for instruction in conf:
            value = instruction.get("value", "")
            
            # Check if debug port 9229 is exposed
            if "9229" in value:
                return CheckResult.FAILED, [instruction]
        
        return CheckResult.PASSED, None


check = NoDebugPortExposed()
