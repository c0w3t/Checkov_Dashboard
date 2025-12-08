"""
Custom Policy: Ensure S3 bucket has versioning enabled
ID: CKV_TF_CUSTOM_11
Category: BACKUP_AND_RECOVERY

This policy checks that S3 buckets have versioning enabled to protect against
accidental deletion and provide data recovery capabilities.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class S3BucketVersioning(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure S3 bucket has versioning enabled"
        id = "CKV_TF_CUSTOM_11"
        supported_resources = ("aws_s3_bucket", "aws_s3_bucket_versioning")
        categories = (CheckCategories.BACKUP_AND_RECOVERY,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for versioning configuration in S3 buckets
        """
        # Check old-style inline versioning configuration (aws_s3_bucket)
        versioning = conf.get("versioning")
        if versioning and isinstance(versioning, list):
            for version_block in versioning:
                if isinstance(version_block, dict):
                    enabled = version_block.get("enabled")
                    if enabled and enabled[0] is True:
                        return CheckResult.PASSED
        
        # Check new-style separate versioning resource (aws_s3_bucket_versioning)
        versioning_configuration = conf.get("versioning_configuration")
        if versioning_configuration and isinstance(versioning_configuration, list):
            for config in versioning_configuration:
                if isinstance(config, dict):
                    status = config.get("status")
                    if status and status[0] == "Enabled":
                        return CheckResult.PASSED
        
        return CheckResult.FAILED


check = S3BucketVersioning()
