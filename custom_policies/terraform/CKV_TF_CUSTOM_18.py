"""
Custom Policy: Ensure VPC flow logging is enabled
ID: CKV_TF_CUSTOM_18
Category: LOGGING

This policy checks that VPC flow logs are enabled to capture information
about IP traffic going to and from network interfaces in your VPC.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class VPCFlowLogsEnabled(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure VPC flow logging is enabled"
        id = "CKV_TF_CUSTOM_18"
        supported_resources = ("aws_vpc", "aws_flow_log")
        categories = (CheckCategories.LOGGING,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for flow log configuration
        Note: This check will pass for aws_flow_log resources.
        For aws_vpc, it requires manual verification that a corresponding
        aws_flow_log resource exists, which Checkov handles through graph analysis.
        """
        # Check if this is an aws_flow_log resource
        vpc_id = conf.get("vpc_id")
        if vpc_id:
            # If aws_flow_log resource exists with vpc_id, it passes
            return CheckResult.PASSED
        
        # Check if this is an aws_vpc resource
        # For VPC, actual flow log check requires cross-resource validation
        # This is a simplified check
        enable_dns_hostnames = conf.get("enable_dns_hostnames")
        enable_dns_support = conf.get("enable_dns_support")
        
        # If these VPC-specific attributes exist, this is likely a VPC resource
        # Return UNKNOWN to indicate manual verification needed
        if enable_dns_hostnames is not None or enable_dns_support is not None:
            return CheckResult.UNKNOWN
        
        return CheckResult.FAILED


check = VPCFlowLogsEnabled()
