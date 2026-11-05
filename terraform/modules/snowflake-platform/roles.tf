# Role model.
#
# Access roles hold privileges on one schema: <SCHEMA>_R can read it and
# <SCHEMA>_W can also write to it. Functional roles (from platform.yml) are
# what people and services use; they get access roles and a warehouse.
# Functional roles roll up to SYSADMIN.

locals {
  access_roles = merge([
    for key, schema in local.schemas : {
      "${key}_R" = { schema = key, level = "read", name = "${local.prefix}_${key}_R" }
      "${key}_W" = { schema = key, level = "write", name = "${local.prefix}_${key}_W" }
    }
  ]...)

  functional_roles = {
    for pair in setproduct(local.environments, keys(local.roles)) :
    "${pair[0]}_${pair[1]}" => {
      env  = pair[0]
      role = pair[1]
      name = "${local.prefix}_${pair[0]}_${pair[1]}"
    }
  }

  # Each functional role gets one access role per layer and domain it covers.
  functional_access = merge([
    for fkey, functional in local.functional_roles : merge([
      for layer, level in local.roles[functional.role].access : {
        for domain in local.roles[functional.role].domains :
        "${fkey}_${layer}_${domain}" => {
          functional = fkey
          access     = "${functional.env}_${layer}_${domain}_${level == "write" ? "W" : "R"}"
        }
      }
    ]...)
  ]...)
}

resource "snowflake_account_role" "access" {
  for_each = local.access_roles

  name    = each.value.name
  comment = "Access role: ${each.value.level} on ${each.value.schema}"
}

resource "snowflake_account_role" "functional" {
  for_each = local.functional_roles

  name    = each.value.name
  comment = "Functional role ${each.value.role} in ${each.value.env}"
}

# A write role can also do everything its read role can.
resource "snowflake_grant_account_role" "read_to_write" {
  for_each = local.schemas

  role_name        = snowflake_account_role.access["${each.key}_R"].name
  parent_role_name = snowflake_account_role.access["${each.key}_W"].name
}

resource "snowflake_grant_account_role" "access_to_functional" {
  for_each = local.functional_access

  role_name        = snowflake_account_role.access[each.value.access].name
  parent_role_name = snowflake_account_role.functional[each.value.functional].name
}

resource "snowflake_grant_account_role" "functional_to_sysadmin" {
  for_each = local.functional_roles

  role_name        = snowflake_account_role.functional[each.key].name
  parent_role_name = "SYSADMIN"
}
