{#
    Put a model in models/<layer>/<domain>/... into schema <DOMAIN>.

    <domain> must be one of var('platform_domains'). An explicit +schema
    config is used as-is (dbt's default would prefix it with the target
    schema). Other models use the target schema.
#}
{% macro generate_schema_name(custom_schema_name=none, node=none) -%}
    {%- if custom_schema_name is not none -%}
        {{ custom_schema_name | trim | upper }}
    {%- elif node is not none and node.fqn | length > 3 and (node.fqn[2] | upper) in var('platform_domains') -%}
        {{ node.fqn[2] | upper }}
    {%- else -%}
        {{ target.schema }}
    {%- endif -%}
{%- endmacro %}
