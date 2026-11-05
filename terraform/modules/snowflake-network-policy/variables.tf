variable "prefix" {
  description = "Prefix for object names, in upper case, such as ACME_DATA."
  type        = string
}

variable "allowed_ips" {
  description = "IPv4 addresses or CIDR ranges allowed to connect, such as [\"203.0.113.0/24\"]."
  type        = list(string)

  validation {
    condition     = length(var.allowed_ips) > 0 && alltrue([for ip in var.allowed_ips : can(cidrnetmask(strcontains(ip, "/") ? ip : "${ip}/32"))])
    error_message = "allowed_ips must be a non-empty list of IPv4 addresses or CIDR ranges."
  }
}
