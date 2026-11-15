variable "aws_region" {
  type    = string
  default = "us-east-1"
}
 
variable "project_name" {
  type    = string
  default = "costwatch"
}
 
variable "instance_type" {
  type    = string
  default = "t3.micro"
}
 
variable "key_name" {
  type = string
}
 
variable "allowed_cidr" {
  type        = string
  description = "128.185.168.199/32"
}
 
variable "repo_url" {
  type = string
}
 
variable "docker_image" {
  type = string
}
 
variable "ssm_groq_param" {
  type    = string
  default = "/costwatch/groq_api_key"
}
 
variable "ssm_grafana_param" {
  type    = string
  default = "/costwatch/grafana_password"
}

variable "cost_source" {
  type        = string
  default     = "mock"
  description = "mock = sample data, aws = real Cost Explorer data"
}
