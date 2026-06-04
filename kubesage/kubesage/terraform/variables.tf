variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "kubesage-demo"
}

variable "kubernetes_version" {
  type    = string
  default = "1.30"
}
