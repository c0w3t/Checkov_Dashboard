from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class RunAsNonRoot(BaseK8Check):
    """
    Check that containers run as non-root user
    """

    def __init__(self) -> None:
        name = "Ensure containers run as non-root user"
        id = "CKV_K8S_CUSTOM_13"
        supported_kind = ("Pod", "Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job", "CronJob")
        categories = (CheckCategories.KUBERNETES,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Scan the Pod spec configuration to ensure containers run as non-root
        """
        # Get the spec based on resource type
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
        
        # Check pod-level securityContext first
        pod_security_context = spec.get("securityContext", {})
        if isinstance(pod_security_context, dict):
            run_as_non_root = pod_security_context.get("runAsNonRoot")
            if run_as_non_root is True:
                return CheckResult.PASSED
        
        # Check container-level securityContext
        containers = spec.get("containers", [])
        if not containers:
            return CheckResult.FAILED
        
        for container in containers:
            if not isinstance(container, dict):
                continue
            
            security_context = container.get("securityContext", {})
            if isinstance(security_context, dict):
                run_as_non_root = security_context.get("runAsNonRoot")
                run_as_user = security_context.get("runAsUser")
                
                # Must have runAsNonRoot=true OR runAsUser > 0
                if run_as_non_root is True or (run_as_user is not None and run_as_user > 0):
                    continue
                else:
                    return CheckResult.FAILED
            else:
                return CheckResult.FAILED
        
        # Check initContainers if present
        init_containers = spec.get("initContainers", [])
        for container in init_containers:
            if not isinstance(container, dict):
                continue
            security_context = container.get("securityContext", {})
            if isinstance(security_context, dict):
                run_as_non_root = security_context.get("runAsNonRoot")
                run_as_user = security_context.get("runAsUser")
                if not (run_as_non_root is True or (run_as_user is not None and run_as_user > 0)):
                    return CheckResult.FAILED
            else:
                return CheckResult.FAILED
        
        return CheckResult.PASSED


check = RunAsNonRoot()