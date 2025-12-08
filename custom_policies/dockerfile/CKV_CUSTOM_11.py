"""
Custom Policy: Ensure apt-get clean after apt-get install
ID: CKV_CUSTOM_11
Category: SUPPLY_CHAIN

This policy checks that apt-get clean is used after apt-get install
to reduce Docker image size by removing package cache.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class EnsureAptGetClean(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure apt-get clean is used after apt-get install"
        id = "CKV_CUSTOM_11"
        supported_instructions = ("RUN",)
        categories = (CheckCategories.SUPPLY_CHAIN,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan RUN instructions to ensure apt-get clean follows apt-get install
        """
        for instruction in conf:
            value = instruction.get("value", "")
            
            # Check if this RUN contains apt-get install
            if "apt-get install" in value:
                # Verify apt-get clean is also present
                if "apt-get clean" not in value:
                    return CheckResult.FAILED, [instruction]
        
        return CheckResult.PASSED, None


check = EnsureAptGetClean()
