"""
Unit tests for Secrets stack.
"""

import pytest
from aws_cdk import assertions
from aws_cdk import aws_secretsmanager as secretsmanager

from infra.stacks.secrets_stack import SecretsStack


def test_secrets_stack_creation(app, dev_config):
    """Test that Secrets stack is created successfully."""
    stack = SecretsStack(app, "TestSecretsStack", dev_config)

    template = assertions.Template.from_stack(stack)

    # Check secrets are created
    template.resource_count_is("AWS::SecretsManager::Secret", 4)

    # Check KMS key is created
    template.resource_count_is(
        "AWS::KMS::Key", 2
    )  # Secrets KMS key + SSM outputs KMS key


def test_rds_credentials_secret(app, dev_config):
    """Test that RDS credentials secret is created with correct properties."""
    stack = SecretsStack(app, "TestSecretsStack", dev_config)

    template = assertions.Template.from_stack(stack)

    # Check RDS credentials secret
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "GenerateSecretString": {
                "SecretStringTemplate": '{"username": "admin"}',
                "GenerateStringKey": "password",
                "ExcludeCharacters": " %+~`#$&*()|[]{}:;<>?!'/\\\"@",
                "PasswordLength": 32,
            },
        },
    )


def test_secrets_encryption(app, dev_config):
    """Test that secrets are encrypted with KMS."""
    stack = SecretsStack(app, "TestSecretsStack", dev_config)

    template = assertions.Template.from_stack(stack)

    # Check that secrets have KMS key reference
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "KmsKeyId": assertions.Match.any_value(),
        },
    )


def test_secrets_rotation_prod(app, prod_config):
    """Test that secrets rotation is enabled in production."""
    stack = SecretsStack(app, "TestSecretsStackProd", prod_config)

    template = assertions.Template.from_stack(stack)

    # Check rotation schedule is created for prod
    template.resource_count_is("AWS::SecretsManager::RotationSchedule", 1)


def test_secrets_rotation_dev(app, dev_config):
    """Test that secrets rotation is disabled in dev."""
    stack = SecretsStack(app, "TestSecretsStackDev", dev_config)

    template = assertions.Template.from_stack(stack)

    # Check rotation schedule is NOT created for dev
    template.resource_count_is("AWS::SecretsManager::RotationSchedule", 0)


def test_ssm_parameters_created(app, dev_config):
    """Test that SSM parameters are created for secrets."""
    stack = SecretsStack(app, "TestSecretsStack", dev_config)

    template = assertions.Template.from_stack(stack)

    # Check SSM parameters are created
    template.resource_count_is(
        "AWS::SSM::Parameter", 9
    )  # 4 ARNs + 4 names + 1 KMS key ARN
