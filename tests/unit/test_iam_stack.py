"""
Unit tests for IAM stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_iam as iam

from infra.stacks.iam_stack import IamStack


def test_iam_stack_creation(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that IAM stack is created successfully."""
    # Create mock stacks for dependencies
    from tests.conftest import MockVpcStack, MockSecretsStack

    mock_rds_stack = type("MockRdsStack", (), {"secrets_stack": mock_secrets_stack})()

    mock_sqs_stack = type(
        "MockSqsStack",
        (),
        {
            "main_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-queue"},
            )(),
            "high_priority_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-hp-queue"},
            )(),
            "fifo_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-fifo-queue"},
            )(),
            "batch_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-batch-queue"},
            )(),
            "dlq": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-dlq"},
            )(),
        },
    )()

    mock_opensearch_stack = type(
        "MockOpenSearchStack",
        (),
        {
            "domain": type(
                "MockDomain",
                (),
                {"domain_arn": "arn:aws:es:us-east-1:123456789012:domain/test-domain"},
            )()
        },
    )()

    stack = IamStack(
        app,
        "TestIamStack",
        dev_config,
        rds_stack=mock_rds_stack,
        sqs_stack=mock_sqs_stack,
        opensearch_stack=mock_opensearch_stack,
    )

    template = assertions.Template.from_stack(stack)

    # Check IAM roles are created
    template.resource_count_is(
        "AWS::IAM::Role", 2
    )  # Lambda execution + Application roles

    # Check IAM policies are created
    template.resource_count_is("AWS::IAM::Policy", 5)  # 5 inline policies


def test_lambda_execution_role(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that Lambda execution role is created with correct properties."""
    # Create mock stacks for dependencies
    mock_rds_stack = type("MockRdsStack", (), {"secrets_stack": mock_secrets_stack})()

    mock_sqs_stack = type(
        "MockSqsStack",
        (),
        {
            "main_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-queue"},
            )(),
            "high_priority_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-hp-queue"},
            )(),
            "fifo_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-fifo-queue"},
            )(),
            "batch_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-batch-queue"},
            )(),
            "dlq": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-dlq"},
            )(),
        },
    )()

    mock_opensearch_stack = type(
        "MockOpenSearchStack",
        (),
        {
            "domain": type(
                "MockDomain",
                (),
                {"domain_arn": "arn:aws:es:us-east-1:123456789012:domain/test-domain"},
            )()
        },
    )()

    stack = IamStack(
        app,
        "TestIamStack",
        dev_config,
        rds_stack=mock_rds_stack,
        sqs_stack=mock_sqs_stack,
        opensearch_stack=mock_opensearch_stack,
    )

    template = assertions.Template.from_stack(stack)

    # Check Lambda execution role
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ]
            },
            "ManagedPolicyArns": assertions.Match.any_value(),
        },
    )


def test_application_role(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that Application role is created with correct properties."""
    # Create mock stacks for dependencies
    mock_rds_stack = type("MockRdsStack", (), {"secrets_stack": mock_secrets_stack})()

    mock_sqs_stack = type(
        "MockSqsStack",
        (),
        {
            "main_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-queue"},
            )(),
            "high_priority_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-hp-queue"},
            )(),
            "fifo_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-fifo-queue"},
            )(),
            "batch_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-batch-queue"},
            )(),
            "dlq": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-dlq"},
            )(),
        },
    )()

    mock_opensearch_stack = type(
        "MockOpenSearchStack",
        (),
        {
            "domain": type(
                "MockDomain",
                (),
                {"domain_arn": "arn:aws:es:us-east-1:123456789012:domain/test-domain"},
            )()
        },
    )()

    stack = IamStack(
        app,
        "TestIamStack",
        dev_config,
        rds_stack=mock_rds_stack,
        sqs_stack=mock_sqs_stack,
        opensearch_stack=mock_opensearch_stack,
    )

    template = assertions.Template.from_stack(stack)

    # Check Application role
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    },
                ]
            },
        },
    )


def test_sqs_access_policy(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that SQS access policy has correct permissions."""
    # Create mock stacks for dependencies
    mock_rds_stack = type("MockRdsStack", (), {"secrets_stack": mock_secrets_stack})()

    mock_sqs_stack = type(
        "MockSqsStack",
        (),
        {
            "main_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-queue"},
            )(),
            "high_priority_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-hp-queue"},
            )(),
            "fifo_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-fifo-queue"},
            )(),
            "batch_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-batch-queue"},
            )(),
            "dlq": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-dlq"},
            )(),
        },
    )()

    mock_opensearch_stack = type(
        "MockOpenSearchStack",
        (),
        {
            "domain": type(
                "MockDomain",
                (),
                {"domain_arn": "arn:aws:es:us-east-1:123456789012:domain/test-domain"},
            )()
        },
    )()

    stack = IamStack(
        app,
        "TestIamStack",
        dev_config,
        rds_stack=mock_rds_stack,
        sqs_stack=mock_sqs_stack,
        opensearch_stack=mock_opensearch_stack,
    )

    template = assertions.Template.from_stack(stack)

    # Check SQS access policy
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:SendMessage",
                            "sqs:SendMessageBatch",
                            "sqs:ReceiveMessage",
                            "sqs:DeleteMessage",
                            "sqs:DeleteMessageBatch",
                            "sqs:GetQueueAttributes",
                            "sqs:GetQueueUrl",
                        ],
                        "Resource": assertions.Match.any_value(),
                    }
                ]
            },
        },
    )


def test_ssm_parameters_created(app, dev_config, mock_vpc_stack, mock_secrets_stack):
    """Test that SSM parameters are created."""
    # Create mock stacks for dependencies
    mock_rds_stack = type("MockRdsStack", (), {"secrets_stack": mock_secrets_stack})()

    mock_sqs_stack = type(
        "MockSqsStack",
        (),
        {
            "main_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-queue"},
            )(),
            "high_priority_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-hp-queue"},
            )(),
            "fifo_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-fifo-queue"},
            )(),
            "batch_queue": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-batch-queue"},
            )(),
            "dlq": type(
                "MockQueue",
                (),
                {"queue_arn": "arn:aws:sqs:us-east-1:123456789012:test-dlq"},
            )(),
        },
    )()

    mock_opensearch_stack = type(
        "MockOpenSearchStack",
        (),
        {
            "domain": type(
                "MockDomain",
                (),
                {"domain_arn": "arn:aws:es:us-east-1:123456789012:domain/test-domain"},
            )()
        },
    )()

    stack = IamStack(
        app,
        "TestIamStack",
        dev_config,
        rds_stack=mock_rds_stack,
        sqs_stack=mock_sqs_stack,
        opensearch_stack=mock_opensearch_stack,
    )

    template = assertions.Template.from_stack(stack)

    # Check SSM parameters are created
    template.resource_count_is(
        "AWS::SSM::Parameter", 9
    )  # role ARNs + policy ARNs + role names
