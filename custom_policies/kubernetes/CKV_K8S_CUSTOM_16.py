from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class PrivilegedContainer(BaseK8Check):
    """
    Check that containers are not running in privileged mode
    """

    def __init__(self) -> None:
        name = "Container should not be privileged"
        id = "CKV_K8S_CUSTOM_16"
        supported_kind = ("Pod", "Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job", "CronJob")
        categories = (CheckCategories.KUBERNETES,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Scan the Pod spec configuration for privileged containers
        """
        metadata = conf.get("metadata", {})
        kind = metadata.get("kind", "")
        
        if kind == "Pod":
            spec = conf.get("spec", {})
        elif kind in ["Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job"]:
            spec = conf.get("spec", {}).get("template", {}).get("spec", {})
        elif kind == "CronJob":
            spec = conf.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
        else:
            if "template" in conf.get("spec", {}):
                spec = conf.get("spec", {}).get("template", {}).get("spec", {})
            else:
                spec = conf.get("spec", {})
        
        if not spec or not isinstance(spec, dict):
            return CheckResult.FAILED
        
        containers = spec.get("containers", [])
        if not containers:
            return CheckResult.FAILED
        
        for container in containers:
            if not isinstance(container, dict):
                continue
            security_context = container.get("securityContext", {})
            if isinstance(security_context, dict):
                privileged = security_context.get("privileged", False)
                if privileged is True:
                    return CheckResult.FAILED
        
        return CheckResult.PASSED


check = PrivilegedContainer()