"""
Pytest configuration and fixtures for CDK infrastructure tests.
"""

import pytest
from aws_cdk import App, Stack
from constructs import Construct

from infra.config import Config


@pytest.fixture
def app():
    """Create a CDK app for testing."""
    return App()


@pytest.fixture
def dev_config():
    """Create a dev environment configuration."""
    return Config("dev")


@pytest.fixture
def staging_config():
    """Create a staging environment configuration."""
    return Config("staging")


@pytest.fixture
def prod_config():
    """Create a prod environment configuration."""
    return Config("prod")


@pytest.fixture
def test_stack(app, dev_config):
    """Create a test stack for testing constructs."""
    return Stack(app, "TestStack", env=dev_config)


class MockVpcStack(Stack):
    """Mock VPC stack for testing other stacks."""

    def __init__(self, scope: Construct, construct_id: str, config: Config, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        from aws_cdk import aws_ec2 as ec2

        # Create a mock VPC with all subnet types
        self.vpc = ec2.Vpc(
            self,
            "MockVpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            nat_gateways=1,
        )

        # Create mock security groups
        self.web_security_group = ec2.SecurityGroup(
            self,
            "MockWebSecurityGroup",
            vpc=self.vpc,
            description="Mock web security group",
        )

        self.app_security_group = ec2.SecurityGroup(
            self,
            "MockAppSecurityGroup",
            vpc=self.vpc,
            description="Mock app security group",
        )

        self.db_security_group = ec2.SecurityGroup(
            self,
            "MockDbSecurityGroup",
            vpc=self.vpc,
            description="Mock db security group",
        )

        self.opensearch_security_group = ec2.SecurityGroup(
            self,
            "MockOpenSearchSecurityGroup",
            vpc=self.vpc,
            description="Mock OpenSearch security group",
        )

        self.lambda_security_group = ec2.SecurityGroup(
            self,
            "MockLambdaSecurityGroup",
            vpc=self.vpc,
            description="Mock Lambda security group",
        )


class MockSecretsStack(Stack):
    """Mock Secrets stack for testing other stacks."""

    def __init__(self, scope: Construct, construct_id: str, config: Config, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        from aws_cdk import aws_secretsmanager as secretsmanager

        # Create mock secrets
        self.rds_credentials = secretsmanager.Secret(
            self,
            "MockRdsCredentials",
            secret_name="mock-rds-credentials",
        )

        self.api_keys = secretsmanager.Secret(
            self,
            "MockApiKeys",
            secret_name="mock-api-keys",
        )

        self.app_config = secretsmanager.Secret(
            self,
            "MockAppConfig",
            secret_name="mock-app-config",
        )

        self.db_connection_strings = secretsmanager.Secret(
            self,
            "MockDbConnectionStrings",
            secret_name="mock-db-connection-strings",
        )


@pytest.fixture
def mock_vpc_stack(app, dev_config):
    """Create a mock VPC stack for testing."""
    return MockVpcStack(app, "MockVpcStack", dev_config)


@pytest.fixture
def mock_secrets_stack(app, dev_config):
    """Create a mock Secrets stack for testing."""
    return MockSecretsStack(app, "MockSecretsStack", dev_config)
