"""
Secrets Manager Stack - Creates secrets for RDS credentials and external API keys.
"""

import json
from aws_cdk import (
    Stack,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    Duration,
    Tags,
)
from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs
from infra.constants import Constants


class SecretsStack(Stack):
    """Secrets Manager stack for storing sensitive configuration."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config

        # Create KMS key for secrets encryption
        self.kms_key = kms.Key(
            self,
            "SecretsKmsKey",
            description=f"KMS key for secrets in {config.env_name} environment",
            enable_key_rotation=True,
        )

        # Add tags to KMS key
        Tags.of(self.kms_key).add("Purpose", "SecretsEncryption")
        for key, value in self.config.tags.items():
            Tags.of(self.kms_key).add(key, value)

        # Create secrets
        self._create_secrets()

        # Create SSM outputs
        self._create_outputs()

    def _create_secrets(self):
        """Create secrets for various services."""

        # RDS master credentials
        self.rds_credentials = secretsmanager.Secret(
            self,
            "RdsCredentials",
            secret_name=self.config.get_resource_name("rds-credentials"),
            description="RDS master credentials",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {"username": Constants.DEFAULT_MASTER_USERNAME}
                ),
                generate_string_key="password",
                exclude_characters=Constants.EXCLUDED_PASSWORD_CHARS,
                password_length=Constants.PASSWORD_LENGTH,
            ),
            encryption_key=self.kms_key,
        )

        # External API keys (example)
        self.api_keys = secretsmanager.Secret(
            self,
            "ApiKeys",
            secret_name=self.config.get_resource_name("api-keys"),
            description="External API keys",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "example_api_key": "PLACEHOLDER_UPDATE_ME",
                        "another_service_key": "PLACEHOLDER_UPDATE_ME",
                    }
                ),
                generate_string_key="random_suffix",
                password_length=Constants.RANDOM_SUFFIX_LENGTH,
            ),
            encryption_key=self.kms_key,
        )

        # Application configuration secrets
        self.app_config = secretsmanager.Secret(
            self,
            "AppConfig",
            secret_name=self.config.get_resource_name("app-config"),
            description="Application configuration secrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "jwt_secret": "PLACEHOLDER_UPDATE_ME",
                        "encryption_key": "PLACEHOLDER_UPDATE_ME",
                        "session_secret": "PLACEHOLDER_UPDATE_ME",
                    }
                ),
                generate_string_key="random_suffix",
                password_length=Constants.RANDOM_SUFFIX_LENGTH,
            ),
            encryption_key=self.kms_key,
        )

        # Database connection strings (will be updated by applications)
        self.db_connection_strings = secretsmanager.Secret(
            self,
            "DbConnectionStrings",
            secret_name=self.config.get_resource_name("db-connection-strings"),
            description="Database connection strings",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(
                    {
                        "primary": "mysql://PLACEHOLDER_USER:PLACEHOLDER_PASS@PLACEHOLDER_HOST:3306/PLACEHOLDER_DB",
                        "read_replica": "mysql://PLACEHOLDER_USER:PLACEHOLDER_PASS@PLACEHOLDER_HOST:3306/PLACEHOLDER_DB",
                    }
                ),
                generate_string_key="random_suffix",
                password_length=Constants.RANDOM_SUFFIX_LENGTH,
            ),
            encryption_key=self.kms_key,
        )

        # Add tags to all secrets
        for secret in [
            self.rds_credentials,
            self.api_keys,
            self.app_config,
            self.db_connection_strings,
        ]:
            for key, value in self.config.tags.items():
                Tags.of(secret).add(key, value)

        # Set up automatic rotation for RDS credentials (if not dev)
        if not self.config.is_dev:
            self.rds_credentials.add_rotation_schedule(
                "RdsRotationSchedule",
                automatically_after=Duration.days(self.config.secrets_rotation_days),
                hosted_rotation=secretsmanager.HostedRotation.mysql_single_user(),
            )

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="secrets",
        )

        # Secret ARNs
        ssm_outputs.create_parameter_and_output(
            "rds-credentials-arn",
            self.rds_credentials.secret_arn,
            "RDS credentials secret ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "api-keys-arn",
            self.api_keys.secret_arn,
            "API keys secret ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "app-config-arn",
            self.app_config.secret_arn,
            "Application config secret ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "db-connection-strings-arn",
            self.db_connection_strings.secret_arn,
            "Database connection strings secret ARN",
        )

        # KMS key ARN
        ssm_outputs.create_parameter_and_output(
            "secrets-kms-key-arn",
            self.kms_key.key_arn,
            "Secrets KMS key ARN",
        )

        # Secret names (for applications to reference)
        ssm_outputs.create_parameter_and_output(
            "rds-credentials-name",
            self.rds_credentials.secret_name,
            "RDS credentials secret name",
        )

        ssm_outputs.create_parameter_and_output(
            "api-keys-name",
            self.api_keys.secret_name,
            "API keys secret name",
        )

        ssm_outputs.create_parameter_and_output(
            "app-config-name",
            self.app_config.secret_name,
            "Application config secret name",
        )

        ssm_outputs.create_parameter_and_output(
            "db-connection-strings-name",
            self.db_connection_strings.secret_name,
            "Database connection strings secret name",
        )
