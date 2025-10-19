"""
RDS Stack - Creates Aurora MySQL Serverless v2 cluster with proper security.
"""

from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    Duration,
    Tags,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra.stacks.vpc_stack import VpcStack
    from infra.stacks.secrets_stack import SecretsStack

from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs
from infra.constants import Constants


class RdsStack(Stack):
    """RDS stack with Aurora MySQL Serverless v2 cluster."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        vpc_stack: "VpcStack",
        secrets_stack: "SecretsStack",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.vpc_stack = vpc_stack
        self.secrets_stack = secrets_stack

        # Create KMS key for RDS encryption
        self.kms_key = kms.Key(
            self,
            "RdsKmsKey",
            description=f"KMS key for RDS encryption in {config.env_name} environment",
            enable_key_rotation=True,
        )

        # Add tags to KMS key
        Tags.of(self.kms_key).add("Purpose", "RdsEncryption")
        for key, value in self.config.tags.items():
            Tags.of(self.kms_key).add(key, value)

        # Create Aurora cluster
        self._create_aurora_cluster()

        # Create SSM outputs
        self._create_outputs()

    def _create_aurora_cluster(self):
        """Create Aurora MySQL Serverless v2 cluster."""

        # Create subnet group for Aurora
        self.subnet_group = rds.SubnetGroup(
            self,
            "AuroraSubnetGroup",
            description=f"Aurora subnet group for {self.config.env_name}",
            vpc=self.vpc_stack.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        )

        # Create parameter group for Aurora MySQL
        self.parameter_group = rds.ParameterGroup(
            self,
            "AuroraParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=getattr(
                    rds.AuroraMysqlEngineVersion, Constants.AURORA_MYSQL_ENGINE_VERSION
                ),
            ),
            description=f"Aurora MySQL parameter group for {self.config.env_name}",
            parameters=Constants.AURORA_PARAMETERS,
        )

        # Create Aurora cluster
        self.cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=getattr(
                    rds.AuroraMysqlEngineVersion, Constants.AURORA_MYSQL_ENGINE_VERSION
                ),
            ),
            credentials=rds.Credentials.from_generated_secret(
                Constants.DEFAULT_MASTER_USERNAME,
            ),
            writer=rds.ClusterInstance.serverless_v2(
                "Writer",
                enable_performance_insights=self.config.enable_detailed_monitoring,
                publicly_accessible=False,
            ),
            readers=[
                rds.ClusterInstance.serverless_v2(
                    "Reader",
                    scale_with_writer=True,
                    enable_performance_insights=self.config.enable_detailed_monitoring,
                    publicly_accessible=False,
                ),
            ],
            vpc=self.vpc_stack.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[self.vpc_stack.db_security_group],
            default_database_name=Constants.DEFAULT_DATABASE_NAME,
            parameter_group=self.parameter_group,
            subnet_group=self.subnet_group,
            backup=rds.BackupProps(
                retention=Duration.days(self.config.rds_backup_retention_days),
                preferred_window=f"{Constants.AUTOMATED_SNAPSHOT_START_HOUR:02d}:00-{Constants.AUTOMATED_SNAPSHOT_START_HOUR+1:02d}:00",  # UTC
            ),
            enable_performance_insights=self.config.enable_detailed_monitoring,
            performance_insight_retention=(
                rds.PerformanceInsightRetention.DEFAULT
                if self.config.enable_detailed_monitoring
                else None
            ),
            serverless_v2_min_capacity=self.config.rds_min_capacity,
            serverless_v2_max_capacity=self.config.rds_max_capacity,
            storage_encrypted=True,
            storage_encryption_key=self.kms_key,
            deletion_protection=self.config.is_prod,
        )

        # Add tags to cluster
        Tags.of(self.cluster).add(
            "Name", self.config.get_resource_name("aurora-cluster")
        )
        for key, value in self.config.tags.items():
            Tags.of(self.cluster).add(key, value)

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="rds",
        )

        # Cluster endpoints
        ssm_outputs.create_parameter_and_output(
            "cluster-endpoint",
            self.cluster.cluster_endpoint.hostname,
            "Aurora cluster endpoint",
        )

        ssm_outputs.create_parameter_and_output(
            "cluster-port",
            str(self.cluster.cluster_endpoint.port),
            "Aurora cluster port",
        )

        ssm_outputs.create_parameter_and_output(
            "cluster-reader-endpoint",
            self.cluster.cluster_read_endpoint.hostname,
            "Aurora cluster reader endpoint",
        )

        # Cluster ARN
        ssm_outputs.create_parameter_and_output(
            "cluster-arn",
            self.cluster.cluster_arn,
            "Aurora cluster ARN",
        )

        # Database name
        ssm_outputs.create_parameter_and_output(
            "database-name",
            Constants.DEFAULT_DATABASE_NAME,
            "Default database name",
        )

        # Secret ARN (reference to secrets stack)
        # Note: Secret ARN is available in the secrets stack outputs
        # ssm_outputs.create_parameter_and_output(
        #     "secret-arn",
        #     self.secrets_stack.rds_credentials.secret_arn,
        #     "RDS credentials secret ARN",
        # )

        # KMS key ARN
        ssm_outputs.create_parameter_and_output(
            "kms-key-arn",
            self.kms_key.key_arn,
            "RDS KMS key ARN",
        )

        # Subnet group name
        ssm_outputs.create_parameter_and_output(
            "subnet-group-name",
            self.subnet_group.subnet_group_name,
            "RDS subnet group name",
        )

        # Parameter group name
        ssm_outputs.create_parameter_and_output(
            "parameter-group-name",
            self.parameter_group.node.default_child.ref,
            "RDS parameter group name",
        )
