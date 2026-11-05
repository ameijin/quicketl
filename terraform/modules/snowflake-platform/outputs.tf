output "databases" {
  description = "Database names by \"<ENV>_<LAYER>\"."
  value       = { for key, db in snowflake_database.this : key => db.name }
}

output "schemas" {
  description = "Fully qualified schema names by \"<ENV>_<LAYER>_<DOMAIN>\"."
  value       = { for key, schema in snowflake_schema.this : key => schema.fully_qualified_name }
}

output "warehouses" {
  description = "Warehouse names by environment."
  value       = { for key, wh in snowflake_warehouse.this : key => wh.name }
}

output "access_roles" {
  description = "Access role names by \"<ENV>_<LAYER>_<DOMAIN>_R\" or \"..._W\"."
  value       = { for key, role in snowflake_account_role.access : key => role.name }
}

output "functional_roles" {
  description = "Functional role names by \"<ENV>_<ROLE>\"."
  value       = { for key, role in snowflake_account_role.functional : key => role.name }
}

output "landing_writer_roles" {
  description = "Functional role names that can write the landing layer (the first layer)."
  value = [
    for key, functional in local.functional_roles : snowflake_account_role.functional[key].name
    if lookup(local.roles[functional.role].access, local.layers[0], "") == "write"
  ]
}
