output "ecr_repository_url" {
  value = aws_ecr_repository.kubesage.repository_url
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the new cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
