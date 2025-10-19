"""
Environment configuration module for AWS CDK infrastructure.
Provides environment-specific settings for dev, staging, and prod deployments.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""

    # Environment name
    name: str

    # AWS region
    region: str = "ap-southeast-2"

    # Project name for resource naming
    project_name: str = "aws-cdk-infra"

    # VPC Configuration
    vpc_cidr: str = "10.0.0.0/16"
    enable_nat_gateway_per_az: bool = False
    enable_flow_logs: bool = True

    # RDS Configuration
    rds_instance_class: str = "db.serverless"
    rds_min_capacity: float = 0.5
    rds_max_capacity: float = 16.0
    rds_backup_retention_days: int = 7
    rds_multi_az: bool = False

    # OpenSearch Configuration
    opensearch_instance_type: str = "t3.small.search"
    opensearch_instance_count: int = 1
    opensearch_ebs_volume_size: int = 20

    # SQS Configuration
    sqs_visibility_timeout_seconds: int = 30
    sqs_message_retention_seconds: int = 1209600  # 14 days
    sqs_max_receive_count: int = 3

    # Secrets Configuration
    secrets_rotation_days: int = 30

    # Feature flags
    enable_xray_tracing: bool = True
    enable_detailed_monitoring: bool = False


class Config:
    """Main configuration class that provides environment-specific settings."""

    # Environment configurations
    ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
        "dev": EnvironmentConfig(
            name="dev",
            enable_nat_gateway_per_az=False,
            rds_min_capacity=0.5,
            rds_max_capacity=2.0,
            rds_backup_retention_days=7,
            rds_multi_az=False,
            opensearch_instance_type="t3.small.search",
            opensearch_instance_count=1,
            opensearch_ebs_volume_size=20,
            enable_detailed_monitoring=False,
        ),
        "staging": EnvironmentConfig(
            name="staging",
            enable_nat_gateway_per_az=True,
            rds_min_capacity=1.0,
            rds_max_capacity=8.0,
            rds_backup_retention_days=14,
            rds_multi_az=True,
            opensearch_instance_type="r6g.large.search",
            opensearch_instance_count=2,
            opensearch_ebs_volume_size=100,
            enable_detailed_monitoring=True,
        ),
        "prod": EnvironmentConfig(
            name="prod",
            enable_nat_gateway_per_az=True,
            rds_min_capacity=2.0,
            rds_max_capacity=16.0,
            rds_backup_retention_days=30,
            rds_multi_az=True,
            opensearch_instance_type="r6g.large.search",
            opensearch_instance_count=3,
            opensearch_ebs_volume_size=200,
            enable_detailed_monitoring=True,
        ),
    }

    env_name: str
    env_config: EnvironmentConfig

    # Commonly accessed attributes exposed directly on the config
    region: str
    project_name: str
    vpc_cidr: str
    enable_nat_gateway_per_az: bool
    enable_flow_logs: bool
    rds_instance_class: str
    rds_min_capacity: float
    rds_max_capacity: float
    rds_backup_retention_days: int
    rds_multi_az: bool
    opensearch_instance_type: str
    opensearch_instance_count: int
    opensearch_ebs_volume_size: int
    sqs_visibility_timeout_seconds: int
    sqs_message_retention_seconds: int
    sqs_max_receive_count: int
    secrets_rotation_days: int
    enable_xray_tracing: bool
    enable_detailed_monitoring: bool

    def __init__(self, env_name: str):
        """Initialize configuration for the specified environment."""
        if env_name not in self.ENVIRONMENTS:
            raise ValueError(
                f"Unknown environment: {env_name}. Available: {list(self.ENVIRONMENTS.keys())}"
            )

        self.env_name = env_name
        self.env_config = self.ENVIRONMENTS[env_name]

        # Set attributes for easy access
        for field_name, field_value in self.env_config.__dict__.items():
            setattr(self, field_name, field_value)

    @property
    def is_prod(self) -> bool:
        """Check if this is a production environment."""
        return self.env_name == "prod"

    @property
    def is_dev(self) -> bool:
        """Check if this is a development environment."""
        return self.env_name == "dev"

    @property
    def tags(self) -> Dict[str, str]:
        """Get common tags for this environment."""
        return {
            "Environment": self.env_name,
            "Project": self.project_name,
            "ManagedBy": "CDK",
        }

    def get_resource_name(
        self, resource_type: str, suffix: Optional[str] = None
    ) -> str:
        """Generate a standardized resource name."""
        name_parts = [self.project_name, resource_type, self.env_name]
        if suffix:
            name_parts.append(suffix)
        return "-".join(name_parts)

    def get_ssm_parameter_name(self, stack_name: str, resource_name: str) -> str:
        """Generate SSM parameter name following the pattern: /infra/{env}/{stack}/{resource}."""
        return f"/infra/{self.env_name}/{stack_name}/{resource_name}"
