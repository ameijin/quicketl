variable "prefix" {
  description = "Prefix for every object name, in upper case, such as ACME_DATA."
  type        = string

  validation {
    condition     = can(regex("^[A-Z][A-Z0-9_]*$", var.prefix))
    error_message = "prefix must be upper case letters, digits and underscores, starting with a letter."
  }
}

variable "environments" {
  description = "Environment names in upper case, such as [\"DEV\", \"PROD\"]. Each gets its own databases and warehouse."
  type        = list(string)
}

variable "layers" {
  description = "Data layers in order, in upper case, such as [\"RAW\", \"STAGING\", \"MARTS\"]. The first is the landing layer."
  type        = list(string)
}

variable "domains" {
  description = "Business domains in upper case, such as [\"SALES\"]. Each becomes a schema in every database."
  type        = list(string)
}

variable "roles" {
  description = <<-EOT
    Functional roles by name (upper case). `access` maps a layer to "read" or
    "write"; `domains` lists the domains the role covers.
    Example: { ANALYST = { access = { MARTS = "read" }, domains = ["SALES"] } }
  EOT
  type = map(object({
    access  = map(string)
    domains = list(string)
  }))
  default = {}

  validation {
    condition = alltrue(flatten([
      for role in values(var.roles) : [for level in values(role.access) : contains(["read", "write"], level)]
    ]))
    error_message = "Every access level must be \"read\" or \"write\"."
  }
}

variable "warehouse_sizes" {
  description = "Warehouse size per environment, such as { PROD = \"SMALL\" }. Missing environments use XSMALL."
  type        = map(string)
  default     = {}
}
