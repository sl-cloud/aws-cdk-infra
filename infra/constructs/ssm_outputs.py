"""
SSM Parameter Store helper construct for standardized output publishing.
Provides utilities for creating SSM parameters and CloudFormation outputs.
"""

from typing import Any, Dict, Optional, Union, List
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ssm as ssm,
    aws_kms as kms,
    Tags,
)
from constructs import Construct

from infra.config import Config


class SsmOutputs(Construct):
    """Helper construct for creating SSM parameters and CloudFormation outputs."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        stack_name: str,
        description: Optional[str] = None,
        kms_key: Optional[kms.IKey] = None,
    ):
        super().__init__(scope, construct_id)

        self.config = config
        self.stack_name = stack_name
        self.description = description or f"SSM parameters for {stack_name}"

        self.kms_key: kms.IKey
        if kms_key is None:
            # Create dedicated KMS key for SSM parameter encryption
            self.kms_key = kms.Key(
                self,
                "SsmKmsKey",
                description=f"KMS key for SSM parameters in {stack_name}",
                enable_key_rotation=True,
            )

            # Add tags
            Tags.of(self.kms_key).add("Purpose", "SSMParameterEncryption")
            for key, value in self.config.tags.items():
                Tags.of(self.kms_key).add(key, value)
        else:
            # Reuse provided KMS key (tags assumed to be managed by caller)
            self.kms_key = kms_key

    def create_parameter(
        self,
        parameter_name: str,
        value: Union[str, int, float, bool],
        description: Optional[str] = None,
        parameter_type: ssm.ParameterType = ssm.ParameterType.STRING,
        tier: ssm.ParameterTier = ssm.ParameterTier.STANDARD,
    ) -> ssm.StringParameter:
        """Create an SSM parameter with standardized naming."""

        full_parameter_name = self.config.get_ssm_parameter_name(
            self.stack_name, parameter_name
        )

        param = ssm.StringParameter(
            self,
            f"Parameter{parameter_name.replace('-', '').replace('_', '').title()}",
            parameter_name=full_parameter_name,
            string_value=str(value),
            description=description or f"{parameter_name} for {self.stack_name}",
            type=parameter_type,
            tier=tier,
        )

        # Add tags
        for key, value in self.config.tags.items():
            Tags.of(param).add(key, value)

        return param

    def create_output(
        self,
        output_id: str,
        value: Any,
        description: Optional[str] = None,
        export_name: Optional[str] = None,
    ) -> CfnOutput:
        """Create a CloudFormation output."""

        return CfnOutput(
            self,
            output_id,
            value=str(value),
            description=description or f"{output_id} for {self.stack_name}",
            export_name=export_name,
        )

    def create_parameter_and_output(
        self,
        resource_name: str,
        value: Union[str, int, float, bool],
        description: Optional[str] = None,
        parameter_type: ssm.ParameterType = ssm.ParameterType.STRING,
        tier: ssm.ParameterTier = ssm.ParameterTier.STANDARD,
    ) -> Dict[str, Any]:
        """Create both SSM parameter and CloudFormation output for a resource."""

        # Create SSM parameter
        param = self.create_parameter(
            resource_name,
            value,
            description,
            parameter_type,
            tier,
        )

        # Create CloudFormation output
        output = self.create_output(
            f"{resource_name.replace('-', '').replace('_', '').title()}Output",
            value,
            description,
        )

        return {
            "parameter": param,
            "output": output,
            "parameter_name": param.parameter_name,
            "value": value,
        }

    def create_string_list_parameter(
        self,
        parameter_name: str,
        values: List[str],
        description: Optional[str] = None,
    ) -> ssm.StringListParameter:
        """Create an SSM StringList parameter."""

        full_parameter_name = self.config.get_ssm_parameter_name(
            self.stack_name, parameter_name
        )

        param = ssm.StringListParameter(
            self,
            f"Parameter{parameter_name.replace('-', '').replace('_', '').title()}",
            parameter_name=full_parameter_name,
            string_list_value=[str(v) for v in values],
            description=description or f"{parameter_name} for {self.stack_name}",
        )

        # Add tags
        for key, value in self.config.tags.items():
            Tags.of(param).add(key, value)

        return param

    def create_secure_string_parameter(
        self,
        parameter_name: str,
        value: str,
        description: Optional[str] = None,
    ) -> ssm.StringParameter:
        """Create an SSM SecureString parameter."""

        return self.create_parameter(
            parameter_name,
            value,
            description,
            parameter_type=ssm.ParameterType.SECURE_STRING,
        )


def get_parameter_value(
    config: Config,
    stack_name: str,
    resource_name: str,
    default_value: Optional[str] = None,
) -> str:
    """Helper function to retrieve SSM parameter value (for use in client applications)."""
    import boto3  # type: ignore[import-untyped]

    ssm_client = boto3.client("ssm", region_name=config.region)
    parameter_name = config.get_ssm_parameter_name(stack_name, resource_name)

    try:
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )
        return response["Parameter"]["Value"]
    except ssm_client.exceptions.ParameterNotFound:
        if default_value is not None:
            return default_value
        raise ValueError(
            f"Parameter {parameter_name} not found and no default provided"
        )
