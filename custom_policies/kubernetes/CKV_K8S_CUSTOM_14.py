from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class ContainerReadOnlyRootFilesystem(BaseK8Check):
    """
    Check that containers use read-only root filesystem
    """

    def __init__(self) -> None:
        name = "Ensure containers use read-only root filesystem"
        id = "CKV_K8S_CUSTOM_14"
        supported_kind = ("Pod", "Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job", "CronJob")
        categories = (CheckCategories.GENERAL_SECURITY,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Scan the Pod spec configuration to ensure containers use read-only root filesystem
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
            # Fallback: try to find containers in the config
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
            if not isinstance(security_context, dict):
                return CheckResult.FAILED
            
            read_only_root_filesystem = security_context.get("readOnlyRootFilesystem")
            if read_only_root_filesystem is not True:
                return CheckResult.FAILED
        
        # Check initContainers if present
        init_containers = spec.get("initContainers", [])
        for container in init_containers:
            if not isinstance(container, dict):
                continue
            security_context = container.get("securityContext", {})
            if isinstance(security_context, dict):
                read_only_root_filesystem = security_context.get("readOnlyRootFilesystem")
                if read_only_root_filesystem is not True:
                    return CheckResult.FAILED
            else:
                return CheckResult.FAILED
        
        return CheckResult.PASSED


check = ContainerReadOnlyRootFilesystem()