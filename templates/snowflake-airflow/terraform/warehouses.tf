# One warehouse per environment. Sizes come from var.warehouse_sizes.

resource "snowflake_warehouse" "this" {
  for_each = toset(local.environments)

  name                = "${local.prefix}_${each.key}_WH"
  warehouse_size      = lookup(var.warehouse_sizes, each.key, "XSMALL")
  auto_suspend        = 60
  auto_resume         = "true"
  initially_suspended = true
}
