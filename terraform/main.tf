terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
 
provider "aws" {
  region = var.aws_region
}
 
data "aws_caller_identity" "current" {}
 
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}
 
resource "aws_security_group" "app" {
  name        = "${var.project_name}-tf-sg"
  description = "CostWatch access"
 
  dynamic "ingress" {
    for_each = [22, 8000, 9090, 3000]
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    }
  }
 
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
 
resource "aws_iam_role" "ec2" {
  name = "${var.project_name}-tf-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
 
# Lets you open a browser shell with Session Manager (no SSH needed)
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
 
resource "aws_iam_role_policy" "ec2" {
  name = "${var.project_name}-tf-policy"
  role = aws_iam_role.ec2.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage", "ce:GetCostForecast", "ce:GetAnomalies",
          "cloudwatch:GetMetricStatistics", "cloudwatch:GetMetricData",
          "cloudwatch:ListMetrics", "ec2:DescribeInstances", "budgets:ViewBudget"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["ssm:GetParameter"]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_groq_param}",
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.ssm_grafana_param}"
        ]
      }
    ]
  })
}
 
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_name}-tf-profile"
  role = aws_iam_role.ec2.name
}
 
resource "aws_instance" "app" {
  ami                    = data.aws_ssm_parameter.al2023.value
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
 
  # Hop limit 2 lets containers reach the instance role credentials
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
 
  user_data = <<-EOF
    #!/bin/bash
    set -e
    # 2 GB swap: t3.micro only has 1 GB of RAM
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
 
    dnf install -y docker git
    systemctl enable --now docker
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
 
    git clone ${var.repo_url} /opt/costwatch
    cd /opt/costwatch
    GROQ=$(aws ssm get-parameter --name ${var.ssm_groq_param} --with-decryption --query Parameter.Value --output text --region ${var.aws_region})
    GRAF=$(aws ssm get-parameter --name ${var.ssm_grafana_param} --with-decryption --query Parameter.Value --output text --region ${var.aws_region})
    cat > .env <<ENV
    AWS_REGION=${var.aws_region}
    COST_SOURCE=${var.cost_source}
    GROQ_API_KEY=$GROQ
    GRAFANA_ADMIN_PASSWORD=$GRAF
    DOCKER_IMAGE=${var.docker_image}
    ENV
    docker compose up -d
  EOF
 
  tags = {
    Name    = "${var.project_name}-tf"
    Project = var.project_name
  }
}
