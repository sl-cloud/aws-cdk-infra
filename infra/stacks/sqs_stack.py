"""
SQS Stack - Creates SQS queues with Dead Letter Queues and encryption.
"""

from aws_cdk import (
    Stack,
    aws_sqs as sqs,
    aws_kms as kms,
    aws_cloudwatch as cloudwatch,
    Duration,
    Tags,
)
from constructs import Construct

from infra.config import Config
from infra.constructs.ssm_outputs import SsmOutputs
from infra.constants import Constants


class SqsStack(Stack):
    """SQS stack with queues, DLQs, and encryption."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: Config,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        self.config = config

        # Create KMS key for SQS encryption
        self.kms_key = kms.Key(
            self,
            "SqsKmsKey",
            description=f"KMS key for SQS encryption in {config.env_name} environment",
            enable_key_rotation=True,
        )

        # Add tags to KMS key
        Tags.of(self.kms_key).add("Purpose", "SqsEncryption")
        for key, value in self.config.tags.items():
            Tags.of(self.kms_key).add(key, value)

        # Create queues
        self._create_queues()

        # Create SSM outputs
        self._create_outputs()

    def _create_queues(self):
        """Create SQS queues with DLQs."""

        # Dead Letter Queue for general use
        self.dlq = sqs.Queue(
            self,
            "DeadLetterQueue",
            queue_name=self.config.get_resource_name("dlq"),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.kms_key,
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(Constants.DEFAULT_VISIBILITY_TIMEOUT),
        )

        # Main application queue
        self.main_queue = sqs.Queue(
            self,
            "MainQueue",
            queue_name=self.config.get_resource_name("main-queue"),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.kms_key,
            visibility_timeout=Duration.seconds(
                self.config.sqs_visibility_timeout_seconds
            ),
            retention_period=Duration.seconds(
                self.config.sqs_message_retention_seconds
            ),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=self.config.sqs_max_receive_count,
                queue=self.dlq,
            ),
        )

        # High priority queue
        self.high_priority_queue = sqs.Queue(
            self,
            "HighPriorityQueue",
            queue_name=self.config.get_resource_name("high-priority-queue"),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.kms_key,
            visibility_timeout=Duration.seconds(
                self.config.sqs_visibility_timeout_seconds
            ),
            retention_period=Duration.seconds(
                self.config.sqs_message_retention_seconds
            ),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=self.config.sqs_max_receive_count,
                queue=self.dlq,
            ),
        )

        # FIFO queue for ordered processing
        self.fifo_queue = sqs.Queue(
            self,
            "FifoQueue",
            queue_name=f"{self.config.get_resource_name('fifo-queue')}.fifo",
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.kms_key,
            fifo=True,
            content_based_deduplication=True,
            visibility_timeout=Duration.seconds(
                self.config.sqs_visibility_timeout_seconds
            ),
            retention_period=Duration.seconds(
                self.config.sqs_message_retention_seconds
            ),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=self.config.sqs_max_receive_count,
                queue=self.dlq,
            ),
        )

        # Batch processing queue
        self.batch_queue = sqs.Queue(
            self,
            "BatchQueue",
            queue_name=self.config.get_resource_name("batch-queue"),
            encryption=sqs.QueueEncryption.KMS,
            encryption_master_key=self.kms_key,
            visibility_timeout=Duration.seconds(
                Constants.BATCH_QUEUE_VISIBILITY_TIMEOUT
            ),
            retention_period=Duration.seconds(
                self.config.sqs_message_retention_seconds
            ),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=self.config.sqs_max_receive_count,
                queue=self.dlq,
            ),
        )

        # Add tags to all queues
        for queue in [
            self.dlq,
            self.main_queue,
            self.high_priority_queue,
            self.fifo_queue,
            self.batch_queue,
        ]:
            for key, value in self.config.tags.items():
                Tags.of(queue).add(key, value)

        # Create CloudWatch alarms for DLQ
        self._create_dlq_alarms()

    def _create_dlq_alarms(self):
        """Create CloudWatch alarms for Dead Letter Queue monitoring."""

        # Alarm for messages in DLQ
        self.dlq_alarm = cloudwatch.Alarm(
            self,
            "DlqMessagesAlarm",
            metric=self.dlq.metric_approximate_number_of_messages_visible(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Alarm when messages are sent to Dead Letter Queue",
            alarm_name=f"{self.config.get_resource_name('dlq-alarm')}",
        )

        # Alarm for age of oldest message in DLQ
        self.dlq_age_alarm = cloudwatch.Alarm(
            self,
            "DlqAgeAlarm",
            metric=self.dlq.metric_approximate_age_of_oldest_message(),
            threshold=Constants.DLQ_AGE_THRESHOLD_SECONDS,
            evaluation_periods=Constants.EVALUATION_PERIODS,
            alarm_description="Alarm when messages are stuck in DLQ for too long",
            alarm_name=f"{self.config.get_resource_name('dlq-age-alarm')}",
        )

        # Add tags to alarms
        for alarm in [self.dlq_alarm, self.dlq_age_alarm]:
            for key, value in self.config.tags.items():
                Tags.of(alarm).add(key, value)

    def _create_outputs(self):
        """Create SSM parameters and CloudFormation outputs."""

        ssm_outputs = SsmOutputs(
            self,
            "SsmOutputs",
            config=self.config,
            stack_name="sqs",
        )

        # Queue URLs
        ssm_outputs.create_parameter_and_output(
            "main-queue-url",
            self.main_queue.queue_url,
            "Main queue URL",
        )

        ssm_outputs.create_parameter_and_output(
            "high-priority-queue-url",
            self.high_priority_queue.queue_url,
            "High priority queue URL",
        )

        ssm_outputs.create_parameter_and_output(
            "fifo-queue-url",
            self.fifo_queue.queue_url,
            "FIFO queue URL",
        )

        ssm_outputs.create_parameter_and_output(
            "batch-queue-url",
            self.batch_queue.queue_url,
            "Batch queue URL",
        )

        ssm_outputs.create_parameter_and_output(
            "dlq-url",
            self.dlq.queue_url,
            "Dead letter queue URL",
        )

        # Queue ARNs
        ssm_outputs.create_parameter_and_output(
            "main-queue-arn",
            self.main_queue.queue_arn,
            "Main queue ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "high-priority-queue-arn",
            self.high_priority_queue.queue_arn,
            "High priority queue ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "fifo-queue-arn",
            self.fifo_queue.queue_arn,
            "FIFO queue ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "batch-queue-arn",
            self.batch_queue.queue_arn,
            "Batch queue ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "dlq-arn",
            self.dlq.queue_arn,
            "Dead letter queue ARN",
        )

        # KMS key ARN
        ssm_outputs.create_parameter_and_output(
            "kms-key-arn",
            self.kms_key.key_arn,
            "SQS KMS key ARN",
        )

        # Alarm ARNs
        ssm_outputs.create_parameter_and_output(
            "dlq-alarm-arn",
            self.dlq_alarm.alarm_arn,
            "DLQ messages alarm ARN",
        )

        ssm_outputs.create_parameter_and_output(
            "dlq-age-alarm-arn",
            self.dlq_age_alarm.alarm_arn,
            "DLQ age alarm ARN",
        )
