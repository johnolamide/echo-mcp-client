# GitHub Actions CI/CD Setup for Echo MCP Client

This guide explains how to set up automated deployment of the Echo MCP Client using GitHub Actions, AWS ECR, and ECS.

## 🚀 Overview

The CI/CD pipeline automatically:
- **Tests** code on pull requests
- **Builds** Docker images on push to main/master
- **Pushes** images to AWS ECR
- **Deploys** to ECS Fargate
- **Verifies** deployment health

## � Repository Structure

This repository is kept **lean** and focused on the core application code. Infrastructure setup scripts and deployment automation scripts have been removed to maintain a clean codebase.

### What's Included:
- ✅ Core application code (`src/`)
- ✅ Docker configuration (`Dockerfile`, `docker-compose.yml`)
- ✅ CI/CD pipeline (`.github/workflows/`)
- ✅ Configuration files (`.env*`, `requirements.txt`)
- ✅ Documentation (`README.md`, `CI_CD_README.md`)

### What's Not Included:
- ❌ Infrastructure setup scripts (`.sh` files)
- ❌ CloudFormation templates (`infrastructure.yml`)
- ❌ CodeDeploy configuration (`appspec.yml`)
- ❌ Deployment automation scripts

### Manual Setup Required:
You'll need to set up AWS infrastructure manually or use your preferred IaC tool (Terraform, CloudFormation, etc.).

## 🔧 Setup Steps

### Step 1: Set up AWS ECR Repository

**Manual Setup (since setup scripts are not included):**

```bash
# Create ECR repository
aws ecr create-repository --repository-name echo-mcp-client --region us-east-1

# Set up lifecycle policy (optional)
aws ecr put-lifecycle-configuration \
  --repository-name echo-mcp-client \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "description": "Keep last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {"type": "expire"}
    }]
  }'
```

**Alternative: Use AWS Console**
1. Go to Amazon ECR in AWS Console
2. Create repository named `echo-mcp-client`
3. Enable image scanning

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | Your AWS secret key |
| `OPENAI_API_KEY` | OpenAI API Key | Your OpenAI API key |

### Step 3: Set up AWS Infrastructure

**Manual Setup (since setup scripts are not included):**

You'll need to create these AWS resources manually:

1. **VPC and Networking:**
   - Create VPC with public/private subnets
   - Internet Gateway and NAT Gateway
   - Route tables and security groups

2. **ECS Cluster:**
   ```bash
   aws ecs create-cluster --cluster-name echo-mcp-client-cluster
   ```

3. **Application Load Balancer:**
   - Create ALB in public subnets
   - Configure target group for port 8000
   - Set up health checks

4. **ECS Service:**
   - Create service in the cluster
   - Configure Fargate launch type
   - Attach to the ALB target group

**Alternative: Use AWS Console or CloudFormation**
- Use the AWS Console to create resources step-by-step
- Or deploy using CloudFormation templates (not included in this repo)

### Step 4: Push to GitHub

```bash
# Add, commit, and push your changes
git add .
git commit -m "Add CI/CD pipeline for automated deployment"
git push origin main
```

## 🔄 CI/CD Pipeline Flow

### On Pull Request
```
Pull Request → Code Checkout → Test → Coverage Report
```

### On Push to Main/Master
```
Push → Code Checkout → AWS Auth → ECR Login → Build Image → Push to ECR → Update ECS → Deploy → Verify
```

## 📁 Pipeline Configuration

### Workflow Triggers
- **Pull Requests**: Runs tests and coverage
- **Push to main/master**: Full build and deploy
- **Manual Dispatch**: Allows manual deployment with environment selection

### Environment Variables
```yaml
AWS_REGION: us-east-1
ECR_REPOSITORY: echo-mcp-client
IMAGE_TAG: ${{ github.sha }}
```

### Job Structure

#### 1. Test Job
- Runs on pull requests only
- Executes unit tests with pytest
- Generates coverage reports
- Uploads to Codecov

#### 2. Build Job
- Runs on push to main/master
- Authenticates with AWS
- Creates ECR repository if needed
- Builds multi-platform Docker image
- Pushes to ECR with multiple tags
- Generates build attestation

#### 3. Deploy Job
- Depends on successful build
- Updates ECS task definition
- Deploys to ECS service
- Waits for service stability
- Verifies deployment health

## 🏷️ Docker Image Tagging Strategy

The pipeline creates multiple tags for each build:

| Tag Type | Example | Description |
|----------|---------|-------------|
| SHA | `abc1234` | Unique identifier for each commit |
| Branch | `main` | Current branch name |
| Latest | `latest` | Latest build (only for main branch) |
| PR | `pr-123` | Pull request number |

## 🔍 Monitoring and Debugging

### View Pipeline Logs
1. Go to GitHub repository → Actions tab
2. Click on the workflow run
3. View logs for each job/step

### Check AWS Resources
```bash
# Check ECR images
aws ecr list-images --repository-name echo-mcp-client

# Check ECS service status
aws ecs describe-services --cluster echo-mcp-client-cluster --services echo-mcp-client-service

# View CloudWatch logs
aws logs tail /ecs/echo-mcp-client --follow
```

### Common Issues

#### 1. AWS Authentication Failed
- Check GitHub secrets are correctly set
- Verify AWS credentials have required permissions
- Ensure AWS region matches the pipeline configuration

#### 2. ECR Repository Not Found
- Run `./setup_ecr.sh` to create the repository
- Check repository name matches in workflow file

#### 3. ECS Deployment Failed
- Verify infrastructure is set up correctly
- Check CloudFormation stack status
- Review ECS service events

#### 4. Health Check Failed
- Check application logs in CloudWatch
- Verify environment variables are set correctly
- Test the health endpoint manually

## 🔐 Security Features

### AWS IAM Permissions
The pipeline uses minimal required permissions:
- ECR: Read/Write access to repository
- ECS: Update service and register task definitions
- CloudWatch: Write logs

### Image Security
- **Vulnerability Scanning**: Enabled on ECR
- **Build Attestation**: Cryptographic proof of build integrity
- **Multi-platform**: Supports multiple architectures

### Secrets Management
- **GitHub Secrets**: Encrypted storage for sensitive data
- **AWS Secrets Manager**: For runtime secrets (OpenAI API key)

## 🚀 Deployment Environments

### Production (Default)
- Deploys on push to `main` branch
- Uses production infrastructure
- Requires manual approval for sensitive changes

### Staging (Optional)
- Can be triggered manually
- Uses separate infrastructure
- For testing new features

## 📊 Metrics and Monitoring

### Pipeline Metrics
- Build success/failure rates
- Deployment frequency
- Time to deploy
- Test coverage trends

### Application Metrics
- ECS CPU/Memory utilization
- ALB request count and latency
- WebSocket connection count
- Error rates

## 🔄 Rollback Strategy

### Automatic Rollback
- ECS keeps previous task definition
- Can rollback via AWS Console or CLI

### Manual Rollback
```bash
# List task definitions
aws ecs list-task-definitions --family-prefix echo-mcp-client

# Update service to previous version
aws ecs update-service \
  --cluster echo-mcp-client-cluster \
  --service echo-mcp-client-service \
  --task-definition echo-mcp-client:123
```

## 📝 Customization

### Adding New Tests
```yaml
# In .github/workflows/deploy.yml
- name: Run integration tests
  run: |
    python -m pytest tests/integration/ -v
```

### Adding New Environments
```yaml
# Add to workflow_dispatch inputs
- environment:
    description: 'Environment to deploy to'
    required: true
    default: 'production'
    type: choice
    options:
    - production
    - staging
    - development
```

### Custom Build Steps
```yaml
# Add to build job
- name: Run security scan
  run: |
    docker run --rm -v $(pwd):/app \
      securecodebox/engine:latest \
      /app
```

## 🎯 Best Practices

1. **Branch Protection**: Require status checks before merging
2. **Code Reviews**: Require PR reviews for main branch
3. **Testing**: Maintain high test coverage
4. **Security**: Regular dependency updates
5. **Monitoring**: Set up alerts for deployment failures
6. **Documentation**: Keep deployment docs updated

## 📞 Support

For issues with the CI/CD pipeline:
1. Check GitHub Actions logs
2. Review AWS service logs
3. Verify configuration files
4. Check AWS service health status

---

**🎉 Your Echo MCP Client is now set up for automated deployment!**

Every push to the main branch will automatically build, test, and deploy your application to AWS ECS.
