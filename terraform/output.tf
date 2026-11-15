output "public_ip" {
  value = aws_instance.app.public_ip
}
 
output "urls" {
  value = {
    agent      = "http://${aws_instance.app.public_ip}:8000"
    prometheus = "http://${aws_instance.app.public_ip}:9090"
    grafana    = "http://${aws_instance.app.public_ip}:3000"
  }
}
