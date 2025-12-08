"""
Custom Policy: Ensure S3 bucket has server side encryption enabled
ID: CKV_TF_CUSTOM_13
Category: ENCRYPTION

This policy checks that S3 buckets have server-side encryption enabled
to protect data at rest.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class S3BucketEncryption(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure S3 bucket has server side encryption enabled"
        id = "CKV_TF_CUSTOM_13"
        supported_resources = ("aws_s3_bucket", "aws_s3_bucket_server_side_encryption_configuration")
        categories = (CheckCategories.ENCRYPTION,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for server-side encryption configuration in S3 buckets
        """
        # Check old-style inline encryption configuration (aws_s3_bucket)
        server_side_encryption_configuration = conf.get("server_side_encryption_configuration")
        if server_side_encryption_configuration and isinstance(server_side_encryption_configuration, list):
            for encryption_config in server_side_encryption_configuration:
                if isinstance(encryption_config, dict):
                    rule = encryption_config.get("rule")
                    if rule and isinstance(rule, list):
                        for rule_item in rule:
                            if isinstance(rule_item, dict):
                                apply_server_side_encryption_by_default = rule_item.get("apply_server_side_encryption_by_default")
                                if apply_server_side_encryption_by_default and isinstance(apply_server_side_encryption_by_default, list):
                                    for default_encryption in apply_server_side_encryption_by_default:
                                        if isinstance(default_encryption, dict):
                                            sse_algorithm = default_encryption.get("sse_algorithm")
                                            if sse_algorithm:
                                                return CheckResult.PASSED
        
        # Check new-style separate encryption resource (aws_s3_bucket_server_side_encryption_configuration)
        rule = conf.get("rule")
        if rule and isinstance(rule, list):
            for rule_item in rule:
                if isinstance(rule_item, dict):
                    apply_server_side_encryption_by_default = rule_item.get("apply_server_side_encryption_by_default")
                    if apply_server_side_encryption_by_default and isinstance(apply_server_side_encryption_by_default, list):
                        for default_encryption in apply_server_side_encryption_by_default:
                            if isinstance(default_encryption, dict):
                                sse_algorithm = default_encryption.get("sse_algorithm")
                                if sse_algorithm:
                                    return CheckResult.PASSED
        
        return CheckResult.FAILED


check = S3BucketEncryption()
