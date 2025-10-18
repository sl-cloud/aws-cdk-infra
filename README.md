# AWS CDK Infrastructure

A modular AWS CDK infrastructure project providing VPC, RDS (Aurora MySQL), SQS, OpenSearch, Secrets Manager, and IAM resources with environment-specific configurations and comprehensive outputs.

## 🏗️ Architecture Overview

This project creates a complete AWS infrastructure stack with the following components:

- **VPC**: Multi-AZ VPC with public, private, and isolated subnets
- **RDS**: Aurora MySQL Serverless v2 cluster with read replicas
- **SQS**: Multiple queues with Dead Letter Queues and encryption
- **OpenSearch**: Search and analytics domain with VPC configuration
- **Secrets Manager**: Secure storage for credentials and API keys
- **IAM**: Least-privilege roles and policies for service access

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js (for CDK CLI)
- Python 3.11+
- AWS CDK CLI: `npm install -g aws-cdk`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aws-cdk-infra
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Bootstrap CDK (if not already done):
```bash
cdk bootstrap aws://ACCOUNT-NUMBER/ap-southeast-2
```

### Deployment

Deploy to different environments:

```bash
# Development environment
cdk deploy --context env=dev --all

# Staging environment
cdk deploy --context env=staging --all

# Production environment
cdk deploy --context env=prod --all
```

## 📋 Environment Configurations

### Development (`dev`)
- Single NAT Gateway
- Aurora Serverless v2: 0.5-2.0 ACU
- OpenSearch: 1 node (t3.small)
- Backup retention: 7 days
- No deletion protection

### Staging (`staging`)
- Multi-AZ NAT Gateways
- Aurora Serverless v2: 1.0-8.0 ACU
- OpenSearch: 2 nodes (r6g.large)
- Backup retention: 14 days
- Multi-AZ enabled

### Production (`prod`)
- Multi-AZ NAT Gateways
- Aurora Serverless v2: 2.0-16.0 ACU
- OpenSearch: 3 nodes (r6g.large)
- Backup retention: 30 days
- Deletion protection enabled
- Multi-AZ with standby

## 🔧 Configuration

Environment-specific settings are managed in `infra/config.py`. Key configuration options:

- **VPC CIDR**: `10.0.0.0/16`
- **Region**: `ap-southeast-2` (Sydney)
- **RDS Engine**: Aurora MySQL 8.0
- **OpenSearch Version**: 2.11
- **Encryption**: KMS encryption for all resources

## 📊 SSM Parameter Reference

All infrastructure outputs are stored in SSM Parameter Store with the pattern:
`/infra/{environment}/{stack}/{resource}`

### VPC Stack (`/infra/{env}/vpc/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `vpc-id` | VPC ID | String |
| `public-subnet-ids` | Public subnet IDs | StringList |
| `private-subnet-ids` | Private subnet IDs | StringList |
| `isolated-subnet-ids` | Isolated subnet IDs | StringList |
| `web-security-group-id` | Web security group ID | String |
| `app-security-group-id` | Application security group ID | String |
| `db-security-group-id` | Database security group ID | String |
| `opensearch-security-group-id` | OpenSearch security group ID | String |
| `lambda-security-group-id` | Lambda security group ID | String |
| `availability-zones` | Availability zones | StringList |

### RDS Stack (`/infra/{env}/rds/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `cluster-endpoint` | Aurora cluster endpoint | String |
| `cluster-port` | Aurora cluster port | String |
| `cluster-reader-endpoint` | Aurora reader endpoint | String |
| `cluster-arn` | Aurora cluster ARN | String |
| `database-name` | Default database name | String |
| `secret-arn` | RDS credentials secret ARN | String |
| `kms-key-arn` | RDS KMS key ARN | String |
| `subnet-group-name` | RDS subnet group name | String |
| `parameter-group-name` | RDS parameter group name | String |
| `read-replica-endpoint` | Read replica endpoint (staging/prod) | String |
| `read-replica-port` | Read replica port (staging/prod) | String |

### SQS Stack (`/infra/{env}/sqs/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `main-queue-url` | Main queue URL | String |
| `high-priority-queue-url` | High priority queue URL | String |
| `fifo-queue-url` | FIFO queue URL | String |
| `batch-queue-url` | Batch queue URL | String |
| `dlq-url` | Dead letter queue URL | String |
| `main-queue-arn` | Main queue ARN | String |
| `high-priority-queue-arn` | High priority queue ARN | String |
| `fifo-queue-arn` | FIFO queue ARN | String |
| `batch-queue-arn` | Batch queue ARN | String |
| `dlq-arn` | Dead letter queue ARN | String |
| `kms-key-arn` | SQS KMS key ARN | String |
| `dlq-alarm-arn` | DLQ messages alarm ARN | String |
| `dlq-age-alarm-arn` | DLQ age alarm ARN | String |

### OpenSearch Stack (`/infra/{env}/opensearch/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `domain-endpoint` | OpenSearch domain endpoint | String |
| `domain-arn` | OpenSearch domain ARN | String |
| `domain-name` | OpenSearch domain name | String |
| `kibana-endpoint` | Kibana endpoint | String |
| `kms-key-arn` | OpenSearch KMS key ARN | String |
| `log-group-arn` | OpenSearch log group ARN | String |
| `master-username` | OpenSearch master username | String |
| `security-group-id` | OpenSearch security group ID | String |

### Secrets Stack (`/infra/{env}/secrets/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `rds-credentials-arn` | RDS credentials secret ARN | String |
| `api-keys-arn` | API keys secret ARN | String |
| `app-config-arn` | Application config secret ARN | String |
| `db-connection-strings-arn` | DB connection strings secret ARN | String |
| `secrets-kms-key-arn` | Secrets KMS key ARN | String |
| `rds-credentials-name` | RDS credentials secret name | String |
| `api-keys-name` | API keys secret name | String |
| `app-config-name` | Application config secret name | String |
| `db-connection-strings-name` | DB connection strings secret name | String |

### IAM Stack (`/infra/{env}/iam/`)
| Parameter | Description | Type |
|-----------|-------------|------|
| `lambda-execution-role-arn` | Lambda execution role ARN | String |
| `application-role-arn` | Application role ARN | String |
| `rds-access-policy-arn` | RDS access policy ARN | String |
| `sqs-access-policy-arn` | SQS access policy ARN | String |
| `opensearch-access-policy-arn` | OpenSearch access policy ARN | String |
| `secrets-access-policy-arn` | Secrets access policy ARN | String |
| `cloudwatch-logs-policy-arn` | CloudWatch logs policy ARN | String |
| `lambda-execution-role-name` | Lambda execution role name | String |
| `application-role-name` | Application role name | String |

## 💻 Usage Examples

### Retrieving Parameters in Applications

```python
import boto3
from infra.config import Config
from infra.constructs.ssm_outputs import get_parameter_value

# Initialize configuration
config = Config("dev")  # or "staging", "prod"

# Get VPC ID
vpc_id = get_parameter_value(config, "vpc", "vpc-id")

# Get RDS endpoint
rds_endpoint = get_parameter_value(config, "rds", "cluster-endpoint")

# Get SQS queue URL
queue_url = get_parameter_value(config, "sqs", "main-queue-url")
```

### Using IAM Roles

```python
import boto3

# Assume the application role
sts_client = boto3.client('sts')
response = sts_client.assume_role(
    RoleArn='arn:aws:iam::ACCOUNT:role/aws-cdk-infra-application-role-dev',
    RoleSessionName='application-session'
)

# Use the temporary credentials
session = boto3.Session(
    aws_access_key_id=response['Credentials']['AccessKeyId'],
    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
    aws_session_token=response['Credentials']['SessionToken']
)

# Now you can access RDS, SQS, OpenSearch, etc.
```

### Connecting to Aurora MySQL

```python
import pymysql
import boto3
import json

# Get database credentials from Secrets Manager
secrets_client = boto3.client('secretsmanager')
secret_response = secrets_client.get_secret_value(
    SecretId='aws-cdk-infra-rds-credentials-dev'
)
credentials = json.loads(secret_response['SecretString'])

# Get RDS endpoint from SSM
ssm_client = boto3.client('ssm')
endpoint_response = ssm_client.get_parameter(
    Name='/infra/dev/rds/cluster-endpoint'
)
endpoint = endpoint_response['Parameter']['Value']

# Connect to database
connection = pymysql.connect(
    host=endpoint,
    user=credentials['username'],
    password=credentials['password'],
    database='appdb',
    port=3306
)
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=infra --cov-report=html
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow provides:

1. **Testing**: Linting, type checking, and unit tests
2. **Synthesis**: CDK synth for all environments
3. **Diff**: CDK diff against deployed stacks (PRs only)
4. **Deployment**: Automatic deployment based on branch

### Workflow Triggers

- **Push to `develop`**: Deploys to dev environment
- **Push to `main`**: Deploys to staging and prod environments
- **Pull Requests**: Runs tests and shows diff

### Required Secrets

Configure these secrets in your GitHub repository:

- `AWS_ACCESS_KEY_ID`: AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for deployment

## 🛠️ Development

### Project Structure

```
aws-cdk-infra/
├── app.py                    # CDK app entry point
├── cdk.json                  # CDK configuration
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Dev dependencies
├── README.md                 # This file
├── .github/workflows/ci.yml  # GitHub Actions workflow
├── infra/
│   ├── config.py            # Environment configurations
│   ├── stacks/              # Infrastructure stacks
│   │   ├── vpc_stack.py
│   │   ├── rds_stack.py
│   │   ├── sqs_stack.py
│   │   ├── opensearch_stack.py
│   │   ├── secrets_stack.py
│   │   └── iam_stack.py
│   └── constructs/          # Reusable constructs
│       └── ssm_outputs.py
└── tests/                   # Test suite
    ├── conftest.py
    └── unit/
        ├── test_vpc_stack.py
        ├── test_rds_stack.py
        ├── test_sqs_stack.py
        ├── test_opensearch_stack.py
        ├── test_secrets_stack.py
        └── test_iam_stack.py
```

### Adding New Resources

1. Create a new stack in `infra/stacks/`
2. Add configuration options to `infra/config.py`
3. Update `app.py` to include the new stack
4. Add unit tests in `tests/unit/`
5. Update this README with new SSM parameters

### Environment-Specific Changes

Modify `infra/config.py` to add new environment-specific settings:

```python
@dataclass
class EnvironmentConfig:
    # Add your new configuration option
    new_feature_enabled: bool = False

# Update environment configurations
ENVIRONMENTS = {
    "dev": EnvironmentConfig(
        new_feature_enabled=False,
        # ... other settings
    ),
    "prod": EnvironmentConfig(
        new_feature_enabled=True,
        # ... other settings
    ),
}
```

## 🔒 Security

- All resources are encrypted at rest using KMS
- Least-privilege IAM policies
- VPC-based network isolation
- Secrets stored in AWS Secrets Manager
- Fine-grained access control for OpenSearch
- Security groups with minimal required access

## 📈 Monitoring

- VPC Flow Logs enabled
- CloudWatch alarms for SQS DLQ
- OpenSearch slow query logging
- Aurora Performance Insights (staging/prod)
- Detailed monitoring for production resources

## 🚨 Troubleshooting

### Common Issues

1. **CDK Bootstrap Required**
   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/ap-southeast-2
   ```

2. **Permission Denied**
   - Ensure AWS credentials have sufficient permissions
   - Check IAM policies for CDK deployment

3. **Resource Already Exists**
   - Use `cdk destroy` to remove existing resources
   - Check for naming conflicts

4. **OpenSearch Domain Creation Fails**
   - Ensure VPC has sufficient subnets
   - Check security group rules

### Debug Commands

```bash
# Check CDK context
cdk context

# View synthesized CloudFormation
cdk synth --context env=dev

# Check differences
cdk diff --context env=dev

# List all stacks
cdk list --context env=dev
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Check the troubleshooting section
- Review AWS CDK documentation
