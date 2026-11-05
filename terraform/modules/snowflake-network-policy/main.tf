# Network policy allowing only var.allowed_ips.
#
# It is created but NOT attached. Attaching it to the account blocks every
# other address, including other teams using the same account. Attach it
# yourself once you have checked the list includes your own address:
#   ALTER ACCOUNT SET NETWORK_POLICY = <output policy_name>;

resource "snowflake_database" "admin" {
  name    = "${var.prefix}_ADMIN"
  comment = "Platform administration objects"
}

resource "snowflake_schema" "network" {
  database = snowflake_database.admin.name
  name     = "NETWORK"
}

resource "snowflake_network_rule" "allowed_ips" {
  name       = "${var.prefix}_ALLOWED_IPS"
  database   = snowflake_database.admin.name
  schema     = snowflake_schema.network.name
  type       = "IPV4"
  mode       = "INGRESS"
  value_list = var.allowed_ips
}

resource "snowflake_network_policy" "this" {
  name                      = "${var.prefix}_NETWORK_POLICY"
  allowed_network_rule_list = [snowflake_network_rule.allowed_ips.fully_qualified_name]
}
