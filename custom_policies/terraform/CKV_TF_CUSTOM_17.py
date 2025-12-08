"""
Custom Policy: Ensure RDS instances have deletion protection enabled
ID: CKV_TF_CUSTOM_17
Category: BACKUP_AND_RECOVERY

This policy checks that RDS database instances have deletion protection enabled
to prevent accidental deletion of databases.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class RDSDeletionProtection(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure RDS instances have deletion protection enabled"
        id = "CKV_TF_CUSTOM_17"
        supported_resources = ("aws_db_instance", "aws_rds_cluster")
        categories = (CheckCategories.BACKUP_AND_RECOVERY,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for deletion_protection configuration in RDS instances
        """
        deletion_protection = conf.get("deletion_protection")
        
        if deletion_protection and deletion_protection[0] is True:
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = RDSDeletionProtection()
