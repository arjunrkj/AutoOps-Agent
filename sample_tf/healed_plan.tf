# Flawed Infrastructure Plan Baseline
resource "aws_security_group" "vulnerable_sg" {
  name = "allow_all_ssh"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Violation: Open SSH
  }
}

resource "aws_db_instance" "overpriced_db" {
  allocated_storage = 1000
  engine            = "mysql"
  instance_class    = "db.m5.24xlarge" # Violation: Over-budget database
}
