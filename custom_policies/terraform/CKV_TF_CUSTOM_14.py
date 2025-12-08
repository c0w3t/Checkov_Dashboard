"""
Custom Policy: Ensure S3 bucket has MFA delete enabled
ID: CKV_TF_CUSTOM_14
Category: IAM

This policy checks that S3 buckets have MFA delete enabled to provide
an additional layer of security for deletion operations.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class S3BucketMFADelete(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure S3 bucket has MFA delete enabled"
        id = "CKV_TF_CUSTOM_14"
        supported_resources = ("aws_s3_bucket", "aws_s3_bucket_versioning")
        categories = (CheckCategories.IAM,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for MFA delete configuration in S3 bucket versioning
        """
        # Check old-style inline versioning with MFA delete (aws_s3_bucket)
        versioning = conf.get("versioning")
        if versioning and isinstance(versioning, list):
            for version_block in versioning:
                if isinstance(version_block, dict):
                    mfa_delete = version_block.get("mfa_delete")
                    if mfa_delete and mfa_delete[0] is True:
                        return CheckResult.PASSED
        
        # Check new-style separate versioning resource (aws_s3_bucket_versioning)
        versioning_configuration = conf.get("versioning_configuration")
        if versioning_configuration and isinstance(versioning_configuration, list):
            for config in versioning_configuration:
                if isinstance(config, dict):
                    mfa_delete = config.get("mfa_delete")
                    if mfa_delete and mfa_delete[0] == "Enabled":
                        return CheckResult.PASSED
        
        return CheckResult.FAILED


check = S3BucketMFADelete()
