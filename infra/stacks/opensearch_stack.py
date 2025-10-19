"""
OpenSearch Stack - Creates OpenSearch domain with VPC configuration.
"""

from aws_cdk import (
    Stack,
    CfnResource,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_logs as logs,
    RemovalPolicy,
    Tags,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra.stacks.vpc_stack import VpcStack

from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs
from infra.constants import Constants


class OpenSearchStack(Stack):
    """OpenSearch stack with VPC configuration and fine-grained access control."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        vpc_stack: "VpcStack",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.vpc_stack = vpc_stack

        # Create KMS key for OpenSearch encryption
        self.kms_key = kms.Key(
            self,
            "OpenSearchKmsKey",
            description=f"KMS key for OpenSearch encryption in {config.env_name} environment",
            enable_key_rotation=True,
        )

        # Add tags to KMS key
        Tags.of(self.kms_key).add("Purpose", "OpenSearchEncryption")
        for key, value in self.config.tags.items():
            Tags.of(self.kms_key).add(key, value)

        # Create OpenSearch domain
        self._create_opensearch_domain()

        # Create SSM outputs
        self._create_outputs()

    def _create_opensearch_domain(self):
        """Create OpenSearch domain with VPC configuration."""

        # Create CloudWatch Log Group for OpenSearch logs
        self.log_group = logs.LogGroup(
            self,
            "OpenSearchLogGroup",
            log_group_name=f"/aws/opensearch/domains/{self.config.get_resource_name('opensearch')}",
            retention=(
                logs.RetentionDays.ONE_MONTH
                if self.config.is_dev
                else logs.RetentionDays.THREE_MONTHS
            ),
        )

        # Add tags to log group
        Tags.of(self.log_group).add(
            "Purpose", Constants.PURPOSE_TAGS["OPENSEARCH_LOGS"]
        )
        for key, value in self.config.tags.items():
            Tags.of(self.log_group).add(key, value)

        # Create master password secret
        self.master_password_secret = self._create_master_password_secret()

        subnet_ids = self.vpc_stack.vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
        ).subnet_ids

        cluster_config = {
            "InstanceCount": self.config.opensearch_instance_count,
            "InstanceType": self.config.opensearch_instance_type,
        }
        if self.config.opensearch_instance_count > 1:
            cluster_config["ZoneAwarenessEnabled"] = True
            cluster_config["ZoneAwarenessConfig"] = {
                "AvailabilityZoneCount": max(
                    2, min(3, self.config.opensearch_instance_count)
                ),
            }
        if self.config.is_prod:
            cluster_config["MultiAZWithStandbyEnabled"] = True

        domain_tags = [
            {"Key": "Name", "Value": self.config.get_resource_name("opensearch")},
        ]
        domain_tags.extend(
            {"Key": key, "Value": value} for key, value in self.config.tags.items()
        )

        self.domain = CfnResource(
            self,
            "OpenSearchDomain",
            type="AWS::OpenSearch::Domain",
            properties={
                "DomainName": self.config.get_resource_name("opensearch"),
                "EngineVersion": "OpenSearch_2.11",
                "ClusterConfig": cluster_config,
                "EBSOptions": {
                    "EBSEnabled": True,
                    "VolumeSize": self.config.opensearch_ebs_volume_size,
                    "VolumeType": "gp3",
                },
                "EncryptionAtRestOptions": {
                    "Enabled": True,
                    "KmsKeyId": self.kms_key.key_arn,
                },
                "NodeToNodeEncryptionOptions": {
                    "Enabled": True,
                },
                "AdvancedSecurityOptions": {
                    "Enabled": True,
                    "InternalUserDatabaseEnabled": True,
                    "MasterUserOptions": {
                        "MasterUserName": Constants.DEFAULT_MASTER_USERNAME,
                        "MasterUserPassword": self.master_password_secret.secret_value_from_json(
                            "password"
                        ).to_string(),
                    },
                },
                "DomainEndpointOptions": {
                    "EnforceHTTPS": True,
                    "TLSSecurityPolicy": "Policy-Min-TLS-1-2-2019-07",
                },
                "VPCOptions": {
                    "SubnetIds": subnet_ids,
                    "SecurityGroupIds": [
                        self.vpc_stack.opensearch_security_group.security_group_id,
                    ],
                },
                "LogPublishingOptions": {
                    "ES_APPLICATION_LOGS": {
                        "CloudWatchLogsLogGroupArn": self.log_group.log_group_arn,
                        "Enabled": True,
                    },
                },
                "AdvancedOptions": Constants.OPENSEARCH_ADVANCED_OPTIONS,
                "Tags": domain_tags,
            },
        )
        self.domain.apply_removal_policy(
            RemovalPolicy.DESTROY if self.config.is_dev else RemovalPolicy.RETAIN
        )

        self.domain_endpoint = self.domain.get_att("DomainEndpoint").to_string()
        self.domain_arn = self.domain.get_att("Arn").to_string()
        self.domain_name = self.config.get_resource_name("opensearch")

    def _create_master_password_secret(self):
        """Create a secure master password secret for OpenSearch."""
        from aws_cdk import aws_secretsmanager as secretsmanager

        # Generate password securely in Secrets Manager
        master_password_secret = secretsmanager.Secret(
            self,
            "OpenSearchMasterPassword",
            secret_name=self.config.get_resource_name("opensearch-master-password"),
            description="OpenSearch master user password",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"admin"}',
                generate_string_key="password",
                exclude_characters=Constants.EXCLUDED_PASSWORD_CHARS,
                password_length=Constants.PASSWORD_LENGTH,
            ),
            encryption_key=self.kms_key,
        )

        # Add tags to secret
        for key, value in self.config.tags.items():
            Tags.of(master_password_secret).add(key, value)

        return master_password_secret

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="opensearch",
            kms_key=self.kms_key,
        )

        # Domain endpoint
        ssm_outputs.create_parameter_and_output(
            "domain-endpoint",
            self.domain_endpoint,
            "OpenSearch domain endpoint",
        )

        # Domain ARN
        ssm_outputs.create_parameter_and_output(
            "domain-arn",
            self.domain_arn,
            "OpenSearch domain ARN",
        )

        # Domain name
        ssm_outputs.create_parameter_and_output(
            "domain-name",
            self.domain_name,
            "OpenSearch domain name",
        )

        # Kibana endpoint
        # Note: Kibana endpoint is the same as domain endpoint for OpenSearch
        # ssm_outputs.create_parameter_and_output(
        #     "kibana-endpoint",
        #     self.domain_endpoint,
        #     "Kibana endpoint",
        # )

        # KMS key ARN
        ssm_outputs.create_parameter_and_output(
            "kms-key-arn",
            self.kms_key.key_arn,
            "OpenSearch KMS key ARN",
        )

        # Log group ARN
        ssm_outputs.create_parameter_and_output(
            "log-group-arn",
            self.log_group.log_group_arn,
            "OpenSearch log group ARN",
        )

        # Master user info
        ssm_outputs.create_parameter_and_output(
            "master-username",
            Constants.DEFAULT_MASTER_USERNAME,
            "OpenSearch master username",
        )

        # Security group ID (reference to VPC stack)
        ssm_outputs.create_parameter_and_output(
            "security-group-id",
            self.vpc_stack.opensearch_security_group.security_group_id,
            "OpenSearch security group ID",
        )

        # Master password secret ARN
        ssm_outputs.create_parameter_and_output(
            "master-password-secret-arn",
            self.master_password_secret.secret_arn,
            "OpenSearch master password secret ARN",
        )
