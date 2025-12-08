"""
Custom Policy: Ensure S3 bucket has access logging enabled
ID: CKV_TF_CUSTOM_12
Category: LOGGING

This policy checks that S3 buckets have access logging enabled to track
requests for access to the bucket.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class S3BucketLogging(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure S3 bucket has access logging enabled"
        id = "CKV_TF_CUSTOM_12"
        supported_resources = ("aws_s3_bucket", "aws_s3_bucket_logging")
        categories = (CheckCategories.LOGGING,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for logging configuration in S3 buckets
        """
        # Check old-style inline logging configuration (aws_s3_bucket)
        logging = conf.get("logging")
        if logging and isinstance(logging, list) and len(logging) > 0:
            for log_config in logging:
                if isinstance(log_config, dict):
                    target_bucket = log_config.get("target_bucket")
                    if target_bucket:
                        return CheckResult.PASSED
        
        # Check new-style separate logging resource (aws_s3_bucket_logging)
        target_bucket = conf.get("target_bucket")
        if target_bucket and len(target_bucket) > 0:
            return CheckResult.PASSED
        
        return CheckResult.FAILED


check = S3BucketLogging()
