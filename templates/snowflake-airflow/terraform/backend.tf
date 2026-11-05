# Terraform state lives in S3, so CI/CD and every engineer share one copy.
# The bucket, key and region are passed at `terraform init` time: from
# backend.hcl on your machine, and from repository variables in CI. See the
# README, "Run Terraform" and "CI/CD". Both set `use_lockfile = true`, so
# Terraform holds a lock file in S3 and two runs never write the state at once.
terraform {
  backend "s3" {}
}
