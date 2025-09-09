# AWS ECS Deployment Guide for Echo MCP Client

## Repository Structure

This repository is kept **lean** and focused on core application functionality. Infrastructure automation scripts have been removed to maintain clean, maintainable code.

### What's Included:
- ✅ Core application code with WebSocket support
- ✅ Docker containerization
- ✅ GitHub Actions CI/CD pipeline
- ✅ Configuration management
- ✅ Documentation

### What's Not Included:
- ❌ Shell scripts for infrastructure setup
- ❌ CloudFormation templates
- ❌ Deployment automation scripts

### Infrastructure Setup:
Set up AWS resources manually or use your preferred IaC tool. The CI/CD pipeline will handle container builds and deployments once infrastructure is in place.

## Architecture
The Echo MCP Client provides WebSocket-based real-time communication for AI agents, featuring:
- **WebSocket Endpoints**: Real-time agent communication
- **AI Integration**: OpenAI-powered command processing
- **User Isolation**: Per-user agent instances
- **Authentication**: JWT-based secure connections

## Prerequisites

### AWS Account Setup
1. **AWS CLI**: Install and configure AWS CLI
   ```bash
   aws configure
   ```

2. **Required Permissions**: Ensure your AWS user has these permissions:
   - CloudFormation: Full access
   - ECS: Full access
   - ECR: Full access
   - IAM: Full access
   - Route 53: Full access
   - Certificate Manager: Full access
   - Secrets Manager: Full access
   - ELB (Elastic Load Balancing): Full access

### Domain Setup
1. **Route 53 Hosted Zone**: Ensure you have a hosted zone for `qkiu.tech` in Route 53
2. **Domain Ownership**: Verify you own the `qkiu.tech` domain

### Environment Configuration
1. Copy production environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the following variables in `.env`:
   ```bash
   # Application settings
   ENVIRONMENT=production
   DEBUG=false
   APP_NAME=Echo MCP Client
   APP_VERSION=1.0.0
   PORT=8000

   # Server connection settings
   API_BASE_URL=https://api.echo-mcp-server.qkiu.tech
   SERVER_BASE_URL=https://api.echo-mcp-server.qkiu.tech

   # JWT settings
   JWT_SECRET_KEY=your-32-char-secret-key
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

   # OpenAI settings
   OPENAI_API_KEY=your-openai-api-key

   # Logging
   LOG_LEVEL=INFO

   # CORS settings
   CORS_ORIGINS=["https://echo-mcp-client.qkiu.tech"]
   CORS_ALLOW_CREDENTIALS=true
   ```

## Quick Deployment

### Step 1: Manual Infrastructure Setup
Since this repository is kept lean, you'll need to set up AWS infrastructure manually:

```bash
# 1. Create ECR Repository
aws ecr create-repository --repository-name echo-mcp-client --region us-east-1

# 2. Create ECS Cluster
aws ecs create-cluster --cluster-name echo-mcp-client-cluster

# 3. Set up VPC, Subnets, Security Groups, and ALB manually via AWS Console
#    or use your preferred IaC tool (Terraform, CloudFormation, etc.)
```

### Step 2: Configure Environment
```bash
# Copy environment file
cp .env.example .env

# Update with your values
# - API_BASE_URL: Your deployed Echo MCP Server URL
# - OPENAI_API_KEY: Your OpenAI API key
# - JWT_SECRET_KEY: Random secret key
```

### Step 3: Deploy via GitHub Actions
```bash
# Push to trigger automated deployment
git add .
git commit -m "Deploy Echo MCP Client"
git push origin main
```

**Note:** The automated deployment scripts have been removed to keep the repository lean. Use GitHub Actions for CI/CD and manual AWS setup for infrastructure.

## Manual Setup (Detailed)

### 1. Environment Configuration
The application uses the following environment variables:

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `API_BASE_URL`: URL of the deployed Echo MCP Server
- `JWT_SECRET_KEY`: Secret key for JWT token signing

**Optional:**
- `DEBUG`: Set to `false` for production
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed origins for CORS

### 2. AWS Secrets Manager
Create secrets for sensitive data:
```bash
# OpenAI API Key
aws secretsmanager create-secret --name echo-mcp/openai-key \
    --secret-string '{"OPENAI_API_KEY":"your-key"}'
```

### 3. Docker Build and Push
Build and push the Docker image to ECR:
```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Build Docker image
docker build -t echo-mcp-client:latest .

# Tag and push to ECR
docker tag echo-mcp-client:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/echo-mcp-client:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/echo-mcp-client:latest
```

### 4. ECS Task Definition
Update `taskdef.json` with your account ID and region:
```bash
# Replace placeholders
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" taskdef.json
sed -i "s/REGION/$REGION/g" taskdef.json
```

### 5. CI/CD Pipeline
The GitHub Actions workflow (`.github/workflows/deploy.yml`) will:
- Run tests on pull requests
- Build and push Docker images on main branch pushes
- Deploy to ECS automatically

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `OPENAI_API_KEY`: OpenAI API key

## API Endpoints

Once deployed, the following endpoints will be available:

### WebSocket Endpoints
- `wss://echo-mcp-client.qkiu.tech/ws/agent/{user_id}` - Real-time agent communication

### REST Endpoints
- `https://echo-mcp-client.qkiu.tech/health` - Health check
- `https://echo-mcp-client.qkiu.tech/docs` - API documentation

## WebSocket Usage

### Connection
```javascript
const ws = new WebSocket('wss://echo-mcp-client.qkiu.tech/ws/agent/123');

// Send authentication
ws.send(JSON.stringify({
    type: 'authenticate',
    token: 'your-jwt-token'
}));
```

### Commands
```javascript
// Send a command
ws.send(JSON.stringify({
    type: 'command',
    content: 'pay $25 to merchant@example.com'
}));

// Send ping
ws.send(JSON.stringify({
    type: 'ping'
}));
```

### Message Types
- `welcome`: Initial connection message
- `response`: Agent response to commands
- `error`: Error messages
- `help`: Help information
- `services`: Available services list
- `status`: Agent status information
- `pong`: Ping response

## Monitoring and Logging

### CloudWatch Logs
Application logs are available in CloudWatch:
- Log Group: `/ecs/echo-mcp-client`
- Log Stream: `ecs/echo-mcp-client`

### Health Checks
- Endpoint: `https://echo-mcp-client.qkiu.tech/health`
- Returns: `{"status": "healthy"}`

### Metrics
Monitor these key metrics:
- ECS Service CPU/Memory utilization
- ALB request count and latency
- WebSocket connection count
- Error rates

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check JWT token validity
   - Verify user ID format
   - Check ALB security group rules

2. **AI Commands Not Working**
   - Verify OpenAI API key in Secrets Manager
   - Check OpenAI API quota and billing
   - Review application logs for API errors

3. **Service Unhealthy**
   - Check ECS task status
   - Review container logs
   - Verify environment variables
   - Check database connectivity (if applicable)

### Debugging Commands
```bash
# Check ECS service status
aws ecs describe-services --cluster echo-mcp-client-cluster --services echo-mcp-client-service

# View container logs
aws logs tail /ecs/echo-mcp-client --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn YOUR_TARGET_GROUP_ARN
```

## Security Considerations

1. **JWT Tokens**: Use strong secrets and short expiration times
2. **CORS**: Restrict origins to your domain only
3. **Secrets**: Store sensitive data in AWS Secrets Manager
4. **Network**: Use VPC and security groups to restrict access
5. **SSL/TLS**: Always use HTTPS/WSS in production

## Cost Optimization

1. **ECS Tasks**: Use appropriate CPU/memory allocation
2. **Auto Scaling**: Configure based on actual usage patterns
3. **Logging**: Set appropriate log retention periods
4. **Secrets**: Regularly rotate API keys and secrets

## Support

For issues or questions:
1. Check the application logs in CloudWatch
2. Review AWS service health dashboards
3. Verify configuration in AWS Console
4. Check the troubleshooting section above

---

**Deployment completed successfully! 🎉**

Your Echo MCP Client is now deployed at: `https://echo-mcp-client.qkiu.tech`
