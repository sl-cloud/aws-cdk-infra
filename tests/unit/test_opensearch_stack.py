"""
Unit tests for OpenSearch stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_opensearchservice as opensearch

from infra.stacks.opensearch_stack import OpenSearchStack


def test_opensearch_stack_creation(app, dev_config, mock_vpc_stack):
    """Test that OpenSearch stack is created successfully."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check OpenSearch domain is created
    template.resource_count_is("AWS::OpenSearch::Domain", 1)

    # Check KMS key is created
    template.resource_count_is("AWS::KMS::Key", 1)

    # Check log group is created
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_opensearch_version(app, dev_config, mock_vpc_stack):
    """Test that OpenSearch version is correct."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check OpenSearch version
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "EngineVersion": "OpenSearch_2.11",
        },
    )


def test_opensearch_capacity_dev(app, dev_config, mock_vpc_stack):
    """Test OpenSearch capacity configuration for dev."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check capacity configuration for dev
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": "t3.small.search",
            },
        },
    )


def test_opensearch_capacity_prod(app, prod_config, mock_vpc_stack):
    """Test OpenSearch capacity configuration for prod."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStackProd", prod_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check capacity configuration for prod
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "ClusterConfig": {
                "InstanceCount": 3,
                "InstanceType": "r6g.large.search",
                "MultiAZWithStandbyEnabled": True,
            },
        },
    )


def test_opensearch_encryption(app, dev_config, mock_vpc_stack):
    """Test that encryption is enabled."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check encryption is enabled
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "EncryptionAtRestOptions": {
                "Enabled": True,
            },
            "NodeToNodeEncryptionOptions": {
                "Enabled": True,
            },
        },
    )


def test_opensearch_vpc_configuration(app, dev_config, mock_vpc_stack):
    """Test that VPC configuration is correct."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check VPC configuration
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "VPCOptions": assertions.Match.any_value(),
        },
    )


def test_opensearch_logging(app, dev_config, mock_vpc_stack):
    """Test that logging is configured."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check logging configuration
    template.has_resource_properties(
        "AWS::OpenSearch::Domain",
        {
            "LogPublishingOptions": assertions.Match.any_value(),
        },
    )


def test_ssm_parameters_created(app, dev_config, mock_vpc_stack):
    """Test that SSM parameters are created."""
    stack = OpenSearchStack(
        app, "TestOpenSearchStack", dev_config, vpc_stack=mock_vpc_stack
    )

    template = assertions.Template.from_stack(stack)

    # Check SSM parameters are created
    template.resource_count_is("AWS::SSM::Parameter", 8)  # endpoints, ARNs, etc.
