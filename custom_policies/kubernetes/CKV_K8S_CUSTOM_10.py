from __future__ import annotations

from typing import Any

from checkov.common.models.enums import CheckResult, CheckCategories
from checkov.kubernetes.checks.resource.base_spec_check import BaseK8Check


class AllowedRegistries(BaseK8Check):
    """
    Check that images are from allowed registries
    """

    def __init__(self) -> None:
        name = "Image should be from allowed registries"
        id = "CKV_K8S_CUSTOM_10"
        supported_kind = ("Pod", "Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job", "CronJob")
        categories = (CheckCategories.KUBERNETES,)
        super().__init__(name=name, id=id, categories=categories, supported_entities=supported_kind)
        
        # Define allowed registries - you can customize this list
        self.allowed_registries = [
            "docker.io",
            "gcr.io",
            "quay.io",
            "registry.k8s.io",
            "ghcr.io",
            # Add your organization's private registry here
            # "mycompany.azurecr.io",
        ]

    def scan_spec_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Scan the Pod spec configuration for image registries
        """
        # For Deployment, DaemonSet, StatefulSet, ReplicaSet, Job, CronJob
        # we need to check spec.template.spec.containers
        # For Pod, we check spec.containers directly
        
        metadata = conf.get("metadata", {})
        kind = metadata.get("kind", "")
        
        # Get the spec based on resource type
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
        
        # Check containers
        containers = spec.get("containers", [])
        if not containers:
            return CheckResult.FAILED
        
        for container in containers:
            if not isinstance(container, dict):
                continue
            image = container.get("image", "")
            if not image:
                return CheckResult.FAILED
            
            # Extract registry from image
            # Image format: [registry/]repository[:tag][@digest]
            registry = self._extract_registry(image)
            
            # Check if registry is in allowed list
            if not self._is_allowed_registry(registry):
                return CheckResult.FAILED
        
        # Check initContainers if present
        init_containers = spec.get("initContainers", [])
        for container in init_containers:
            if not isinstance(container, dict):
                continue
            image = container.get("image", "")
            if image:
                registry = self._extract_registry(image)
                if not self._is_allowed_registry(registry):
                    return CheckResult.FAILED
        
        return CheckResult.PASSED
    
    def _extract_registry(self, image: str) -> str:
        """
        Extract registry from image name
        """
        # Remove tag/digest if present
        if "@" in image:
            image = image.split("@")[0]
        if ":" in image:
            image = image.split(":")[0]
        
        # Check if image has registry prefix
        parts = image.split("/")
        
        # If only one part or first part doesn't look like domain, assume docker.io
        if len(parts) == 1 or ("." not in parts[0] and ":" not in parts[0] and parts[0] != "localhost"):
            return "docker.io"
        
        return parts[0]
    
    def _is_allowed_registry(self, registry: str) -> bool:
        """
        Check if registry is in allowed list
        """
        # Exact match
        if registry in self.allowed_registries:
            return True
        
        # Check for subdomain match (e.g., us.gcr.io matches gcr.io)
        for allowed in self.allowed_registries:
            if registry.endswith("." + allowed):
                return True
        
        return False


check = AllowedRegistries()
