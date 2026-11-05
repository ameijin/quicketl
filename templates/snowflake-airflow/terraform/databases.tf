# One database per environment and layer, with one schema per domain.

locals {
  databases = {
    for pair in setproduct(local.environments, local.layers) :
    "${pair[0]}_${pair[1]}" => {
      env   = pair[0]
      layer = pair[1]
      name  = "${local.prefix}_${pair[0]}_${pair[1]}"
    }
  }

  schemas = {
    for triple in setproduct(local.environments, local.layers, local.domains) :
    "${triple[0]}_${triple[1]}_${triple[2]}" => {
      env      = triple[0]
      layer    = triple[1]
      domain   = triple[2]
      database = "${triple[0]}_${triple[1]}"
    }
  }
}

resource "snowflake_database" "this" {
  for_each = local.databases

  name    = each.value.name
  comment = "${each.value.layer} layer, ${each.value.env} environment"
}

resource "snowflake_schema" "this" {
  for_each = local.schemas

  database            = snowflake_database.this[each.value.database].name
  name                = each.value.domain
  with_managed_access = "true"
}
