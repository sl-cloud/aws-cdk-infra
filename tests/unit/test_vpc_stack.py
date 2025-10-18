"""
Unit tests for VPC stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_ec2 as ec2

from infra.stacks.vpc_stack import VpcStack


def test_vpc_stack_creation(app, dev_config):
    """Test that VPC stack is created successfully."""
    stack = VpcStack(app, "TestVpcStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check VPC is created
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16",
        "EnableDnsHostnames": True,
        "EnableDnsSupport": True,
    })
    
    # Check security groups are created
    template.resource_count_is("AWS::EC2::SecurityGroup", 6)  # 5 custom + 1 default
    
    # Check NAT gateways (1 for dev)
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_vpc_stack_prod_config(app, prod_config):
    """Test VPC stack with production configuration."""
    stack = VpcStack(app, "TestVpcStackProd", prod_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check NAT gateways (2 for prod with 2 AZs)
    template.resource_count_is("AWS::EC2::NatGateway", 2)


def test_vpc_security_groups(app, dev_config):
    """Test that security groups are created."""
    stack = VpcStack(app, "TestVpcStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check that security groups are created
    template.resource_count_is("AWS::EC2::SecurityGroup", 6)  # 5 custom + 1 default


def test_vpc_flow_logs(app, dev_config):
    """Test that VPC flow logs are created."""
    stack = VpcStack(app, "TestVpcStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check flow log is created
    template.has_resource_properties("AWS::EC2::FlowLog", {
        "ResourceType": "VPC",
        "TrafficType": "ALL",
    })


def test_vpc_subnets(app, dev_config):
    """Test that subnets are created correctly."""
    stack = VpcStack(app, "TestVpcStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check subnets are created
    template.resource_count_is("AWS::EC2::Subnet", 6)  # 2 AZs * 3 subnet types
    
    # Check public subnets
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": True,
    })


def test_ssm_parameters_created(app, dev_config):
    """Test that SSM parameters are created."""
    stack = VpcStack(app, "TestVpcStack", dev_config)
    
    template = assertions.Template.from_stack(stack)
    
    # Check SSM parameters are created
    template.resource_count_is("AWS::SSM::Parameter", 10)  # VPC ID + 5 security group IDs + 4 subnet/AZ lists
