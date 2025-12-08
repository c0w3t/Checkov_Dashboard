"""
Custom Policy: Ensure COPY does not copy entire build context
ID: CKV_CUSTOM_12
Category: SUPPLY_CHAIN

This policy checks that COPY instruction doesn't copy the entire build context
(using patterns like "COPY . ." or "COPY . /app") to prevent accidentally
copying sensitive files like .env, .git, or SSH keys into the Docker image.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class EnsureNoFullCopy(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure COPY does not copy entire build context"
        id = "CKV_CUSTOM_12"
        supported_instructions = ("COPY",)
        categories = (CheckCategories.SUPPLY_CHAIN,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Scan COPY instructions to ensure entire build context is not copied
        """
        for instruction in conf:
            value = instruction.get("value", "")

            # Check if COPY copies entire build context
            # Patterns: "COPY . .", "COPY . /app", "COPY ./ /app"
            if value.strip().startswith(".") or " ." in value or "./" in value:
                return CheckResult.FAILED, [instruction]
        
        return CheckResult.PASSED, None


check = EnsureNoFullCopy()