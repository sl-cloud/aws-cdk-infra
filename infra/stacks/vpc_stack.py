"""
VPC Stack - Creates a multi-AZ VPC with public, private, and isolated subnets.
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_iam as iam,
    Tags,
)
from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs
from infra.constants import Constants


class VpcStack(Stack):
    """VPC stack with multi-AZ subnets and flow logs."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr(self.config.vpc_cidr),
            max_azs=2 if self.config.is_dev else Constants.MAX_AZS,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                # Public subnets for load balancers, NAT gateways
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=Constants.SUBNET_CIDR_MASK,
                ),
                # Private subnets for application servers
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=Constants.SUBNET_CIDR_MASK,
                ),
                # Isolated subnets for databases
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=Constants.SUBNET_CIDR_MASK,
                ),
            ],
            nat_gateways=3 if self.config.enable_nat_gateway_per_az else 1,
        )

        # Add tags to VPC
        Tags.of(self.vpc).add("Name", self.config.get_resource_name("vpc"))
        for key, value in self.config.tags.items():
            Tags.of(self.vpc).add(key, value)

        # Create security groups
        self._create_security_groups()

        # Create VPC Flow Logs if enabled
        if self.config.enable_flow_logs:
            self._create_flow_logs()

        # Create SSM outputs
        self._create_outputs()

    def _create_security_groups(self):
        """Create common security groups."""

        # Default security group for VPC
        self.default_security_group = ec2.SecurityGroup(
            self,
            "DefaultSecurityGroup",
            vpc=self.vpc,
            description="Default security group for VPC",
            allow_all_outbound=True,
        )

        # Security group for web servers (ALB)
        self.web_security_group = ec2.SecurityGroup(
            self,
            "WebSecurityGroup",
            vpc=self.vpc,
            description="Security group for web servers",
            allow_all_outbound=True,
        )

        # Allow HTTP and HTTPS from anywhere
        self.web_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(Constants.HTTP_PORT),
            description="Allow HTTP from anywhere",
        )
        self.web_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(Constants.HTTPS_PORT),
            description="Allow HTTPS from anywhere",
        )

        # Security group for application servers
        self.app_security_group = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=self.vpc,
            description="Security group for application servers",
            allow_all_outbound=True,
        )

        # Allow traffic from web security group
        self.app_security_group.add_ingress_rule(
            peer=self.web_security_group,
            connection=ec2.Port.all_tcp(),
            description="Allow traffic from web servers",
        )

        # Security group for databases
        self.db_security_group = ec2.SecurityGroup(
            self,
            "DbSecurityGroup",
            vpc=self.vpc,
            description="Security group for databases",
            allow_all_outbound=False,
        )

        # Allow MySQL/Aurora traffic from app servers
        self.db_security_group.add_ingress_rule(
            peer=self.app_security_group,
            connection=ec2.Port.tcp(Constants.MYSQL_PORT),
            description="Allow MySQL/Aurora from app servers",
        )

        # Security group for OpenSearch
        self.opensearch_security_group = ec2.SecurityGroup(
            self,
            "OpenSearchSecurityGroup",
            vpc=self.vpc,
            description="Security group for OpenSearch",
            allow_all_outbound=True,
        )

        # Allow HTTPS traffic from app servers
        self.opensearch_security_group.add_ingress_rule(
            peer=self.app_security_group,
            connection=ec2.Port.tcp(Constants.HTTPS_PORT),
            description="Allow HTTPS from app servers",
        )

        # Security group for Lambda functions
        self.lambda_security_group = ec2.SecurityGroup(
            self,
            "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions",
            allow_all_outbound=True,
        )

        # Add tags to security groups
        for sg in [
            self.default_security_group,
            self.web_security_group,
            self.app_security_group,
            self.db_security_group,
            self.opensearch_security_group,
            self.lambda_security_group,
        ]:
            for key, value in self.config.tags.items():
                Tags.of(sg).add(key, value)

    def _create_flow_logs(self):
        """Create VPC Flow Logs."""

        # Create CloudWatch Log Group for VPC Flow Logs
        self.flow_log_group = logs.LogGroup(
            self,
            "VpcFlowLogGroup",
            log_group_name=f"/aws/vpc/flowlogs/{self.config.get_resource_name('vpc')}",
            retention=(
                logs.RetentionDays.ONE_MONTH
                if self.config.is_dev
                else logs.RetentionDays.THREE_MONTHS
            ),
        )

        # Create IAM role for VPC Flow Logs
        self.flow_log_role = iam.Role(
            self,
            "VpcFlowLogRole",
            assumed_by=iam.ServicePrincipal("vpc-flowlogs.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/VPCFlowLogsDeliveryRolePolicy"
                ),
            ],
        )

        # Create VPC Flow Logs
        ec2.FlowLog(
            self,
            "VpcFlowLog",
            resource_type=ec2.FlowLogResourceType.from_vpc(self.vpc),
            traffic_type=ec2.FlowLogTrafficType.ALL,
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(
                log_group=self.flow_log_group,
                iam_role=self.flow_log_role,
            ),
        )

        # Add tags
        Tags.of(self.flow_log_group).add(
            "Purpose", Constants.PURPOSE_TAGS["VPC_FLOW_LOGS"]
        )
        for key, value in self.config.tags.items():
            Tags.of(self.flow_log_group).add(key, value)

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="vpc",
        )

        # VPC ID
        ssm_outputs.create_parameter_and_output(
            "vpc-id",
            self.vpc.vpc_id,
            "VPC ID",
        )

        # Subnet IDs
        public_subnet_ids = [subnet.subnet_id for subnet in self.vpc.public_subnets]
        private_subnet_ids = [subnet.subnet_id for subnet in self.vpc.private_subnets]
        isolated_subnet_ids = [subnet.subnet_id for subnet in self.vpc.isolated_subnets]

        ssm_outputs.create_string_list_parameter(
            "public-subnet-ids",
            public_subnet_ids,
            "Public subnet IDs",
        )

        ssm_outputs.create_string_list_parameter(
            "private-subnet-ids",
            private_subnet_ids,
            "Private subnet IDs",
        )

        ssm_outputs.create_string_list_parameter(
            "isolated-subnet-ids",
            isolated_subnet_ids,
            "Isolated subnet IDs",
        )

        # Security Group IDs
        ssm_outputs.create_parameter_and_output(
            "web-security-group-id",
            self.web_security_group.security_group_id,
            "Web security group ID",
        )

        ssm_outputs.create_parameter_and_output(
            "app-security-group-id",
            self.app_security_group.security_group_id,
            "Application security group ID",
        )

        ssm_outputs.create_parameter_and_output(
            "db-security-group-id",
            self.db_security_group.security_group_id,
            "Database security group ID",
        )

        ssm_outputs.create_parameter_and_output(
            "opensearch-security-group-id",
            self.opensearch_security_group.security_group_id,
            "OpenSearch security group ID",
        )

        ssm_outputs.create_parameter_and_output(
            "lambda-security-group-id",
            self.lambda_security_group.security_group_id,
            "Lambda security group ID",
        )

        # Availability Zones
        azs = self.vpc.availability_zones
        ssm_outputs.create_string_list_parameter(
            "availability-zones",
            azs,
            "Availability zones",
        )
