resource "aws_security_group" "vulnerable_sg" {
  name = "allow_internal_ssh"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # Fixed [SEC-01]: Restricted SSH access to VPC internal subnet
  }
}

resource "aws_db_instance" "overpriced_db" {
  allocated_storage = 100
  engine            = "mysql"
  instance_class    = "db.m5.large" # Fixed [COST-01]: Downsized for staging environment based on P95 CPU utilization
}