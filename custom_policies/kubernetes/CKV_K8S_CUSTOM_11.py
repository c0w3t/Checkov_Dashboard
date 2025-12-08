from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class ServiceAccountTokens(BaseK8Check):
    """
    Check that service account tokens are only mounted where necessary
    """

    def __init__(self) -> None:
        name = "Ensure Service Account Tokens are only mounted where necessary"
        id = "CKV_K8S_CUSTOM_11"
        supported_kind = ("Pod", "Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job", "CronJob")
        categories = (CheckCategories.KUBERNETES,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Scan the Pod spec configuration for automountServiceAccountToken
        """
        # Get the spec based on resource type
        metadata = conf.get("metadata", {})
        kind = metadata.get("kind", "")
        
        # Navigate to the correct spec location
        if kind == "Pod":
            spec = conf.get("spec", {})
        elif kind in ["Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job"]:
            spec = conf.get("spec", {}).get("template", {}).get("spec", {})
        elif kind == "CronJob":
            spec = conf.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
        else:
            # Fallback: try to find spec
            if "template" in conf.get("spec", {}):
                spec = conf.get("spec", {}).get("template", {}).get("spec", {})
            else:
                spec = conf.get("spec", {})
        
        if not spec or not isinstance(spec, dict):
            return CheckResult.FAILED
        
        # Check if automountServiceAccountToken is explicitly set to false
        automount_service_account_token = spec.get("automountServiceAccountToken")
        
        # If explicitly set to False, pass
        if automount_service_account_token is False:
            return CheckResult.PASSED
        
        # If not set or set to True, fail (defaults to True in K8s)
        return CheckResult.FAILED


check = ServiceAccountTokens()