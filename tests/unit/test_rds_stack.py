"""
Unit tests for RDS stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_rds as rds

from infra.stacks.rds_stack import RdsStack


def test_rds_stack_creation(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that RDS stack is created successfully."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check Aurora cluster is created
    template.resource_count_is("AWS::RDS::DBCluster", 1)

    # Check DB instances are created
    template.resource_count_is("AWS::RDS::DBInstance", 2)  # 1 writer + 1 reader for dev

    # Check subnet group is created
    template.resource_count_is("AWS::RDS::DBSubnetGroup", 1)

    # Check parameter group is created
    # template.resource_count_is("AWS::RDS::DBParameterGroup", 1)


def test_rds_stack_prod_config(app, prod_config, mock_vpc_stack, mock_secrets_stack):
    """Test RDS stack with production configuration."""
    stack = RdsStack(
        app,
        "TestRdsStackProd",
        prod_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check DB instances are created (1 writer + 1 read replica for prod)
    template.resource_count_is("AWS::RDS::DBInstance", 2)


def test_aurora_mysql_engine(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that Aurora MySQL engine is configured correctly."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check Aurora MySQL engine
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "Engine": "aurora-mysql",
            "EngineVersion": "8.0.mysql_aurora.3.02.0",
        },
    )


def test_serverless_v2_config(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that Serverless v2 configuration is applied."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check Serverless v2 scaling configuration
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "ServerlessV2ScalingConfiguration": {
                "MinCapacity": 0.5,
                "MaxCapacity": 2.0,
            },
        },
    )


def test_encryption_enabled(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that encryption is enabled."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check encryption is enabled
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "StorageEncrypted": True,
        },
    )


def test_backup_configuration(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that backup configuration is correct."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check backup retention
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "BackupRetentionPeriod": 7,  # dev config
        },
    )


def test_ssm_parameters_created(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that SSM parameters are created."""
    stack = RdsStack(
        app,
        "TestRdsStack",
        dev_config,
        vpc_stack=mock_vpc_stack,
        secrets_stack=mock_secrets_stack,
    )

    template = assertions.Template.from_stack(
        stack, skip_cyclical_dependencies_check=True
    )

    # Check SSM parameters are created
    template.resource_count_is("AWS::SSM::Parameter", 8)  # endpoints, ARNs, etc.
