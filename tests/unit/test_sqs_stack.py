"""
Unit tests for SQS stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_sqs as sqs

from infra.stacks.sqs_stack import SqsStack


def test_sqs_stack_creation(app, dev_config):
    """Test that SQS stack is created successfully."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check queues are created
    template.resource_count_is("AWS::SQS::Queue", 5)  # main, high-priority, fifo, batch, dlq
    
    # Check KMS key is created
    template.resource_count_is("AWS::KMS::Key", 2)  # SQS KMS key + SSM outputs KMS key


def test_queue_encryption(app, dev_config):
    """Test that queues are encrypted with KMS."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check that queues have KMS encryption
    template.has_resource_properties("AWS::SQS::Queue", {
        "KmsMasterKeyId": assertions.Match.any_value(),
    })


def test_dlq_configuration(app, dev_config):
    """Test that Dead Letter Queue is configured correctly."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check DLQ properties
    template.has_resource_properties("AWS::SQS::Queue", {
        "MessageRetentionPeriod": 1209600,  # 14 days
    })


def test_fifo_queue_properties(app, dev_config):
    """Test that FIFO queue has correct properties."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check FIFO queue properties
    template.has_resource_properties("AWS::SQS::Queue", {
        "FifoQueue": True,
        "ContentBasedDeduplication": True,
    })


def test_cloudwatch_alarms(app, dev_config):
    """Test that CloudWatch alarms are created for DLQ."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check CloudWatch alarms are created
    template.resource_count_is("AWS::CloudWatch::Alarm", 2)  # DLQ messages and age alarms


def test_ssm_parameters_created(app, dev_config):
    """Test that SSM parameters are created."""
    stack = SqsStack(app, "TestSqsStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check SSM parameters are created
    template.resource_count_is("AWS::SSM::Parameter", 13)  # URLs + ARNs + KMS key + alarms
