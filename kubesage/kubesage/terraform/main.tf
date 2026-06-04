terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

# --- Networking (minimal VPC for the cluster) -------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # cheaper for a demo
}

# --- EKS cluster ------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_irsa = true # lets the KubeSage pod assume an IAM role (for Bedrock)

  eks_managed_node_groups = {
    default = {
      instance_types = ["t3.small"]
      min_size       = 1
      max_size       = 2
      desired_size   = 1
    }
  }
}

# --- ECR repository for the KubeSage image ----------------------------------
resource "aws_ecr_repository" "kubesage" {
  name                 = "kubesage"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

# --- SNS topic for alerts ---------------------------------------------------
resource "aws_sns_topic" "alerts" {
  name = "kubesage-alerts"
}

# --- IAM: allow the KubeSage pod to call Bedrock + publish to SNS -----------
# Attach this to the pod's service account via IRSA (see README).
data "aws_iam_policy_document" "kubesage" {
  statement {
    actions   = ["bedrock:InvokeModel", "bedrock:Converse"]
    resources = ["*"]
  }
  statement {
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.alerts.arn]
  }
}

resource "aws_iam_policy" "kubesage" {
  name   = "kubesage-policy"
  policy = data.aws_iam_policy_document.kubesage.json
}
