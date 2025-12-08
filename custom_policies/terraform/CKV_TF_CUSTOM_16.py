"""
Custom Policy: Ensure RDS database has encryption enabled
ID: CKV_TF_CUSTOM_16
Category: ENCRYPTION

This policy checks that RDS database instances have encryption at rest enabled
to protect sensitive data.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class RDSEncryption(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure RDS database has encryption enabled"
        id = "CKV_TF_CUSTOM_16"
        supported_resources = ("aws_db_instance", "aws_rds_cluster")
        categories = (CheckCategories.ENCRYPTION,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for storage_encrypted configuration in RDS instances
        """
        storage_encrypted = conf.get("storage_encrypted")
        
        if storage_encrypted and storage_encrypted[0] is True:
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = RDSEncryption()
