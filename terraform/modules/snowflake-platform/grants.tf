# Privileges for access roles and warehouse use for functional roles.

locals {
  read_roles  = { for key, schema in local.schemas : key => "${key}_R" }
  write_roles = { for key, schema in local.schemas : key => "${key}_W" }

  # Every (schema, object type, all-or-future) combination for table grants.
  object_grants = {
    for triple in setproduct(keys(local.schemas), ["TABLES", "VIEWS"], ["all", "future"]) :
    "${triple[0]}_${triple[1]}_${triple[2]}" => {
      schema = triple[0]
      plural = triple[1]
      scope  = triple[2]
    }
  }
  table_grants = { for key, g in local.object_grants : key => g if g.plural == "TABLES" }
}

# --- Read: use the database and schema, select from tables and views ---

resource "snowflake_grant_privileges_to_account_role" "read_database" {
  for_each = local.read_roles

  account_role_name = snowflake_account_role.access[each.value].name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_schema.this[each.key].database
  }
}

resource "snowflake_grant_privileges_to_account_role" "read_schema" {
  for_each = local.read_roles

  account_role_name = snowflake_account_role.access[each.value].name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = snowflake_schema.this[each.key].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "read_all" {
  for_each = { for key, g in local.object_grants : key => g if g.scope == "all" }

  account_role_name = snowflake_account_role.access[local.read_roles[each.value.schema]].name
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = each.value.plural
      in_schema          = snowflake_schema.this[each.value.schema].fully_qualified_name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "read_future" {
  for_each = { for key, g in local.object_grants : key => g if g.scope == "future" }

  account_role_name = snowflake_account_role.access[local.read_roles[each.value.schema]].name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = each.value.plural
      in_schema          = snowflake_schema.this[each.value.schema].fully_qualified_name
    }
  }
}

# --- Write: create objects in the schema and change table data ---

resource "snowflake_grant_privileges_to_account_role" "write_schema" {
  for_each = local.write_roles

  account_role_name = snowflake_account_role.access[each.value].name
  privileges        = ["CREATE TABLE", "CREATE VIEW", "CREATE STAGE", "CREATE FILE FORMAT"]
  on_schema {
    schema_name = snowflake_schema.this[each.key].fully_qualified_name
  }
}

resource "snowflake_grant_privileges_to_account_role" "write_all_tables" {
  for_each = { for key, g in local.table_grants : key => g if g.scope == "all" }

  account_role_name = snowflake_account_role.access[local.write_roles[each.value.schema]].name
  privileges        = ["INSERT", "UPDATE", "DELETE", "TRUNCATE"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = snowflake_schema.this[each.value.schema].fully_qualified_name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "write_future_tables" {
  for_each = { for key, g in local.table_grants : key => g if g.scope == "future" }

  account_role_name = snowflake_account_role.access[local.write_roles[each.value.schema]].name
  privileges        = ["INSERT", "UPDATE", "DELETE", "TRUNCATE"]
  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = snowflake_schema.this[each.value.schema].fully_qualified_name
    }
  }
}

# --- Warehouse: each functional role can use its environment's warehouse ---

resource "snowflake_grant_privileges_to_account_role" "warehouse" {
  for_each = local.functional_roles

  account_role_name = snowflake_account_role.functional[each.key].name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.this[each.value.env].name
  }
}
