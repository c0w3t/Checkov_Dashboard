"""
Custom Policy: Ensure all data stored in EBS is securely encrypted
ID: CKV_TF_CUSTOM_10
Category: ENCRYPTION

This policy checks that all EBS volumes have encryption enabled.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class EBSEncryption(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure all data stored in EBS is securely encrypted"
        id = "CKV_TF_CUSTOM_10"
        supported_resources = ("aws_ebs_volume", "aws_instance")
        categories = (CheckCategories.ENCRYPTION,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for encryption configuration in EBS volumes
        """
        # Check if this is an aws_ebs_volume with direct encryption attribute
        encrypted = conf.get("encrypted")
        if encrypted and encrypted[0] is True:
            return CheckResult.PASSED
        elif encrypted is not None:
            # If encrypted attribute exists and is False, fail
            return CheckResult.FAILED
        
        # Check if EC2 instance has encrypted root block device
        root_block_device = conf.get("root_block_device")
        if root_block_device and isinstance(root_block_device, list):
            for device in root_block_device:
                if isinstance(device, dict):
                    encrypted = device.get("encrypted")
                    if not encrypted or encrypted[0] is not True:
                        return CheckResult.FAILED
            return CheckResult.PASSED
        
        # Check ebs_block_device
        ebs_block_device = conf.get("ebs_block_device")
        if ebs_block_device and isinstance(ebs_block_device, list):
            for device in ebs_block_device:
                if isinstance(device, dict):
                    encrypted = device.get("encrypted")
                    if not encrypted or encrypted[0] is not True:
                        return CheckResult.FAILED
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = EBSEncryption()
