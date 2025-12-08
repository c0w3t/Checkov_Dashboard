"""
Custom Policy: Ensure Instance Metadata Service Version 1 is not enabled
ID: CKV_TF_CUSTOM_15
Category: NETWORKING

This policy checks that EC2 instances use IMDSv2 (token-required) instead of IMDSv1
to prevent SSRF attacks and improve security.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class IMDSv2Required(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure Instance Metadata Service Version 1 is not enabled"
        id = "CKV_TF_CUSTOM_15"
        supported_resources = ("aws_instance", "aws_launch_template", "aws_launch_configuration")
        categories = (CheckCategories.NETWORKING,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for metadata_options configuration requiring IMDSv2
        """
        metadata_options = conf.get("metadata_options")
        
        if not metadata_options:
            # If metadata_options is not specified, IMDSv1 is enabled by default
            return CheckResult.FAILED
        
        if isinstance(metadata_options, list):
            for options in metadata_options:
                if isinstance(options, dict):
                    http_tokens = options.get("http_tokens")
                    # Check if http_tokens is set to "required" (IMDSv2)
                    if http_tokens and http_tokens[0] == "required":
                        return CheckResult.PASSED
            return CheckResult.FAILED
        
        return CheckResult.FAILED


check = IMDSv2Required()
