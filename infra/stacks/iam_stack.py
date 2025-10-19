"""
IAM Stack - Creates IAM roles and policies with least-privilege access.
"""

from aws_cdk import (
    Stack,
    aws_iam as iam,
    Tags,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra.stacks.rds_stack import RdsStack
    from infra.stacks.sqs_stack import SqsStack
    from infra.stacks.opensearch_stack import OpenSearchStack

from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs


class IamStack(Stack):
    """IAM stack with least-privilege roles and policies."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        rds_stack: "RdsStack",
        sqs_stack: "SqsStack",
        opensearch_stack: "OpenSearchStack",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.rds_stack = rds_stack
        self.sqs_stack = sqs_stack
        self.opensearch_stack = opensearch_stack

        # Create IAM roles and policies
        self._create_roles_and_policies()

        # Create SSM outputs
        self._create_outputs()

    def _create_roles_and_policies(self):
        """Create IAM roles and policies with least-privilege access."""

        # Lambda execution role
        self.lambda_execution_role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name=self.config.get_resource_name("lambda-execution-role"),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for Lambda functions",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )

        # Application role for EC2/ECS tasks
        self.application_role = iam.Role(
            self,
            "ApplicationRole",
            role_name=self.config.get_resource_name("application-role"),
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            description="Role for application services",
        )

        # RDS access policy
        self.rds_access_policy = iam.Policy(
            self,
            "RdsAccessPolicy",
            policy_name=self.config.get_resource_name("rds-access-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "rds:DescribeDBClusters",
                        "rds:DescribeDBInstances",
                        "rds:DescribeDBClusterEndpoints",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                    ],
                    resources=[self.rds_stack.secrets_stack.rds_credentials.secret_arn],
                ),
            ],
        )

        # SQS access policy
        self.sqs_access_policy = iam.Policy(
            self,
            "SqsAccessPolicy",
            policy_name=self.config.get_resource_name("sqs-access-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sqs:SendMessage",
                        "sqs:SendMessageBatch",
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:DeleteMessageBatch",
                        "sqs:GetQueueAttributes",
                        "sqs:GetQueueUrl",
                    ],
                    resources=[
                        self.sqs_stack.main_queue.queue_arn,
                        self.sqs_stack.high_priority_queue.queue_arn,
                        self.sqs_stack.fifo_queue.queue_arn,
                        self.sqs_stack.batch_queue.queue_arn,
                        self.sqs_stack.dlq.queue_arn,
                    ],
                ),
            ],
        )

        # OpenSearch access policy
        self.opensearch_access_policy = iam.Policy(
            self,
            "OpenSearchAccessPolicy",
            policy_name=self.config.get_resource_name("opensearch-access-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "es:ESHttpGet",
                        "es:ESHttpPost",
                        "es:ESHttpPut",
                        "es:ESHttpDelete",
                        "es:ESHttpHead",
                    ],
                    resources=[f"{self.opensearch_stack.domain.domain_arn}/*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "es:DescribeDomain",
                        "es:DescribeDomains",
                    ],
                    resources=[self.opensearch_stack.domain.domain_arn],
                ),
            ],
        )

        # Secrets Manager access policy
        self.secrets_access_policy = iam.Policy(
            self,
            "SecretsAccessPolicy",
            policy_name=self.config.get_resource_name("secrets-access-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                    ],
                    resources=[
                        self.rds_stack.secrets_stack.api_keys.secret_arn,
                        self.rds_stack.secrets_stack.app_config.secret_arn,
                        self.rds_stack.secrets_stack.db_connection_strings.secret_arn,
                    ],
                ),
            ],
        )

        # CloudWatch logs policy
        self.cloudwatch_logs_policy = iam.Policy(
            self,
            "CloudWatchLogsPolicy",
            policy_name=self.config.get_resource_name("cloudwatch-logs-policy"),
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                    ],
                    resources=["*"],
                ),
            ],
        )

        # Attach policies to roles
        self.lambda_execution_role.attach_inline_policy(self.rds_access_policy)
        self.lambda_execution_role.attach_inline_policy(self.sqs_access_policy)
        self.lambda_execution_role.attach_inline_policy(self.opensearch_access_policy)
        self.lambda_execution_role.attach_inline_policy(self.secrets_access_policy)
        self.lambda_execution_role.attach_inline_policy(self.cloudwatch_logs_policy)

        self.application_role.attach_inline_policy(self.rds_access_policy)
        self.application_role.attach_inline_policy(self.sqs_access_policy)
        self.application_role.attach_inline_policy(self.opensearch_access_policy)
        self.application_role.attach_inline_policy(self.secrets_access_policy)
        self.application_role.attach_inline_policy(self.cloudwatch_logs_policy)

        # Add tags to all IAM resources
        for resource in [
            self.lambda_execution_role,
            self.application_role,
            self.rds_access_policy,
            self.sqs_access_policy,
            self.opensearch_access_policy,
            self.secrets_access_policy,
            self.cloudwatch_logs_policy,
        ]:
            for key, value in self.config.tags.items():
                Tags.of(resource).add(key, value)

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="iam",
        )

        # Role ARNs
        ssm_outputs.create_parameter_and_output(
            "lambda-execution-role-arn",
            self.lambda_execution_role.role_arn,
            "Lambda execution role ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "application-role-arn",
            self.application_role.role_arn,
            "Application role ARN",
        )

        # Policy names (inline policies don't have ARNs)
        ssm_outputs.create_parameter_and_output(
            "rds-access-policy-name",
            self.rds_access_policy.policy_name,
            "RDS access policy name",
        )

        ssm_outputs.create_parameter_and_output(
            "sqs-access-policy-name",
            self.sqs_access_policy.policy_name,
            "SQS access policy name",
        )

        ssm_outputs.create_parameter_and_output(
            "opensearch-access-policy-name",
            self.opensearch_access_policy.policy_name,
            "OpenSearch access policy name",
        )

        ssm_outputs.create_parameter_and_output(
            "secrets-access-policy-name",
            self.secrets_access_policy.policy_name,
            "Secrets access policy name",
        )

        ssm_outputs.create_parameter_and_output(
            "cloudwatch-logs-policy-name",
            self.cloudwatch_logs_policy.policy_name,
            "CloudWatch logs policy name",
        )

        # Role names (for applications to reference)
        ssm_outputs.create_parameter_and_output(
            "lambda-execution-role-name",
            self.lambda_execution_role.role_name,
            "Lambda execution role name",
        )

        ssm_outputs.create_parameter_and_output(
            "application-role-name",
            self.application_role.role_name,
            "Application role name",
        )
