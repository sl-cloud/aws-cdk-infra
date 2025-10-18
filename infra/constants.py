"""
Constants for AWS CDK infrastructure project.
Centralizes magic numbers and configuration values.
"""

from typing import Dict, Any


class Constants:
    """Centralized constants for the infrastructure project."""
    
    # Password and Security Constants
    PASSWORD_LENGTH = 32
    RANDOM_SUFFIX_LENGTH = 16
    EXCLUDED_PASSWORD_CHARS = " %+~`#$&*()|[]{}:;<>?!'/\\\"@"
    
    # Time Constants (in seconds)
    DLQ_AGE_THRESHOLD_SECONDS = 3600  # 1 hour
    BATCH_QUEUE_VISIBILITY_TIMEOUT = 300  # 5 minutes
    DEFAULT_VISIBILITY_TIMEOUT = 30  # 30 seconds
    MESSAGE_RETENTION_SECONDS = 1209600  # 14 days
    
    # Backup Constants
    DEV_BACKUP_RETENTION_DAYS = 7
    STAGING_BACKUP_RETENTION_DAYS = 14
    PROD_BACKUP_RETENTION_DAYS = 30
    
    # Rotation Constants
    SECRETS_ROTATION_DAYS = 30
    
    # Monitoring Constants
    CPU_THRESHOLD_PERCENT = 80
    EVALUATION_PERIODS = 2
    DLQ_EVALUATION_PERIODS = 1
    
    # Aurora MySQL Constants
    AURORA_MYSQL_VERSION = "8.0.mysql_aurora.3.02_0"
    AURORA_MYSQL_ENGINE_VERSION = "VER_3_02_0"
    
    # OpenSearch Constants
    OPENSEARCH_VERSION = "OPENSEARCH_2_11"
    
    # Network Constants
    VPC_CIDR = "10.0.0.0/16"
    SUBNET_CIDR_MASK = 24
    MAX_AZS = 3
    
    # Port Constants
    HTTP_PORT = 80
    HTTPS_PORT = 443
    MYSQL_PORT = 3306
    
    # Snapshot Constants
    AUTOMATED_SNAPSHOT_START_HOUR = 3  # UTC
    AUTOMATED_SNAPSHOT_START_MINUTE = 0
    
    # Aurora Parameter Constants
    AURORA_PARAMETERS: Dict[str, str] = {
        "innodb_buffer_pool_size": "{DBInstanceClassMemory*3/4}",
        "max_connections": "1000",
        "slow_query_log": "1",
        "long_query_time": "2",
    }
    
    # OpenSearch Advanced Options
    OPENSEARCH_ADVANCED_OPTIONS: Dict[str, str] = {
        "rest.action.multi.allow_explicit_index": "true",
        "indices.fielddata.cache.size": "20%",
        "indices.query.bool.max_clause_count": "1024",
    }
    
    # Resource Name Constants
    DEFAULT_DATABASE_NAME = "appdb"
    DEFAULT_MASTER_USERNAME = "admin"
    
    # Tag Constants
    COMMON_TAGS: Dict[str, str] = {
        "ManagedBy": "CDK",
        "Project": "aws-cdk-infra",
    }
    
    # Purpose Tags
    PURPOSE_TAGS: Dict[str, str] = {
        "SSM_PARAMETER_ENCRYPTION": "SSMParameterEncryption",
        "RDS_ENCRYPTION": "RdsEncryption",
        "SQS_ENCRYPTION": "SqsEncryption",
        "OPENSEARCH_ENCRYPTION": "OpenSearchEncryption",
        "SECRETS_ENCRYPTION": "SecretsEncryption",
        "VPC_FLOW_LOGS": "VpcFlowLogs",
        "OPENSEARCH_LOGS": "OpenSearchLogs",
    }
