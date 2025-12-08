"""
Custom Policy: Ensure npm cache is cleaned after npm install
ID: CKV_CUSTOM_14
Category: SUPPLY_CHAIN

This policy checks that npm cache is cleaned after npm install commands
to reduce image size and prevent potential security issues from cached data.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.dockerfile.base_dockerfile_check import BaseDockerfileCheck

if TYPE_CHECKING:
    from dockerfile_parse.parser import _Instruction


class NpmCacheCleanAfterInstall(BaseDockerfileCheck):
    def __init__(self) -> None:
        name = "Ensure npm cache is cleaned after npm install"
        id = "CKV_CUSTOM_14"
        supported_instructions = ("RUN",)
        categories = (CheckCategories.SUPPLY_CHAIN,)
        super().__init__(
            name=name,
            id=id,
            categories=categories,
            supported_instructions=supported_instructions,
        )

    def scan_resource_conf(self, conf: list[_Instruction]) -> tuple[CheckResult, list[_Instruction] | None]:
        """
        Fail only if a RUN line contains 'npm install' without 'npm cache clean'
        """
        for instruction in conf:
            val = instruction.get("value", "").lower()

            # Chỉ fail nếu dòng đó có 'npm install' mà không có 'npm cache clean'
            if "npm install" in val and "npm cache clean" not in val:
                return CheckResult.FAILED, [instruction]

        return CheckResult.PASSED, None


check = NpmCacheCleanAfterInstall()
