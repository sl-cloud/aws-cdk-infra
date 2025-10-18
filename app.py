#!/usr/bin/env python3
"""
AWS CDK Infrastructure Application
Entry point for deploying modular AWS infrastructure stacks.
"""

import os
from aws_cdk import App, Environment, Tags

from infra.config import Config
from infra.stacks.vpc_stack import VpcStack
from infra.stacks.secrets_stack import SecretsStack
from infra.stacks.rds_stack import RdsStack
from infra.stacks.sqs_stack import SqsStack
from infra.stacks.opensearch_stack import OpenSearchStack
from infra.stacks.iam_stack import IamStack


def main():
    app = App()
    
    # Get environment from context or default to dev
    env_name = app.node.try_get_context("env") or "dev"
    config = Config(env_name)
    
    # AWS Environment
    aws_env = Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=config.region
    )
    
    # Add common tags
    Tags.of(app).add("Environment", env_name)
    Tags.of(app).add("Project", "aws-cdk-infra")
    Tags.of(app).add("ManagedBy", "CDK")
    
    # Create stacks with dependencies
    vpc_stack = VpcStack(
        app, f"{config.project_name}-vpc-{env_name}",
        config=config,
        env=aws_env,
        description=f"VPC infrastructure for {env_name} environment"
    )
    
    secrets_stack = SecretsStack(
        app, f"{config.project_name}-secrets-{env_name}",
        config=config,
        env=aws_env,
        description=f"Secrets Manager for {env_name} environment"
    )
    
    rds_stack = RdsStack(
        app, f"{config.project_name}-rds-{env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        env=aws_env,
        description=f"Aurora MySQL cluster for {env_name} environment"
    )
    
    sqs_stack = SqsStack(
        app, f"{config.project_name}-sqs-{env_name}",
        config=config,
        env=aws_env,
        description=f"SQS queues for {env_name} environment"
    )
    
    opensearch_stack = OpenSearchStack(
        app, f"{config.project_name}-opensearch-{env_name}",
        config=config,
        vpc_stack=vpc_stack,
        env=aws_env,
        description=f"OpenSearch domain for {env_name} environment"
    )
    
    iam_stack = IamStack(
        app, f"{config.project_name}-iam-{env_name}",
        config=config,
        rds_stack=rds_stack,
        sqs_stack=sqs_stack,
        opensearch_stack=opensearch_stack,
        env=aws_env,
        description=f"IAM roles and policies for {env_name} environment"
    )
    
    app.synth()


if __name__ == "__main__":
    main()
