"""
Custom Policy: Ensure Security Groups do not allow unrestricted ingress on critical ports
ID: CKV_TF_CUSTOM_19
Category: NETWORKING

This policy checks that security groups do not allow unrestricted access (0.0.0.0/0)
on critical ports like SSH (22), RDP (3389), database ports, etc.
"""

from __future__ import annotations
from typing import Any
from checkov.common.models.enums import CheckCategories, CheckResult
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck


class SecurityGroupRestrictedPorts(BaseResourceCheck):
    def __init__(self) -> None:
        name = "Ensure Security Groups do not allow unrestricted ingress on critical ports"
        id = "CKV_TF_CUSTOM_19"
        supported_resources = ("aws_security_group", "aws_security_group_rule")
        categories = (CheckCategories.NETWORKING,)
        super().__init__(name=name, id=id, categories=categories, supported_resources=supported_resources)
        
        # Critical ports that should not be open to 0.0.0.0/0
        self.critical_ports = [
            22,    # SSH
            3389,  # RDP
            3306,  # MySQL
            5432,  # PostgreSQL
            1433,  # MSSQL
            27017, # MongoDB
            6379,  # Redis
            9200,  # Elasticsearch
            5601,  # Kibana
        ]

    def scan_resource_conf(self, conf: dict[str, Any]) -> CheckResult:
        """
        Looks for unrestricted ingress rules on critical ports
        """
        # Check inline ingress rules (aws_security_group)
        ingress_rules = conf.get("ingress")
        if ingress_rules and isinstance(ingress_rules, list):
            for rule in ingress_rules:
                if isinstance(rule, dict):
                    if self._is_unrestricted_critical_port(rule):
                        return CheckResult.FAILED
            return CheckResult.PASSED
        
        # Check standalone security group rule (aws_security_group_rule)
        rule_type = conf.get("type")
        if rule_type and rule_type[0] == "ingress":
            if self._is_unrestricted_critical_port(conf):
                return CheckResult.FAILED
            return CheckResult.PASSED
        
        return CheckResult.PASSED

    def _is_unrestricted_critical_port(self, rule: dict[str, Any]) -> bool:
        """
        Check if rule allows unrestricted access to critical ports
        """
        # Check CIDR blocks
        cidr_blocks = rule.get("cidr_blocks", [])
        if cidr_blocks and "0.0.0.0/0" in cidr_blocks:
            # Check if port is in critical ports list
            from_port = rule.get("from_port")
            to_port = rule.get("to_port")
            
            if from_port and to_port:
                from_port_val = from_port[0] if isinstance(from_port, list) else from_port
                to_port_val = to_port[0] if isinstance(to_port, list) else to_port
                
                # Check if any critical port falls within the range
                for critical_port in self.critical_ports:
                    if from_port_val <= critical_port <= to_port_val:
                        return True
        
        # Check IPv6 CIDR blocks
        ipv6_cidr_blocks = rule.get("ipv6_cidr_blocks", [])
        if ipv6_cidr_blocks and "::/0" in ipv6_cidr_blocks:
            from_port = rule.get("from_port")
            to_port = rule.get("to_port")
            
            if from_port and to_port:
                from_port_val = from_port[0] if isinstance(from_port, list) else from_port
                to_port_val = to_port[0] if isinstance(to_port, list) else to_port
                
                for critical_port in self.critical_ports:
                    if from_port_val <= critical_port <= to_port_val:
                        return True
        
        return False


check = SecurityGroupRestrictedPorts()
