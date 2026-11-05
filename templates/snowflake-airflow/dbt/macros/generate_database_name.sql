{#
    Put a model in models/<layer>/... into database <PREFIX>_<TARGET>_<LAYER>.

    <layer> must be one of var('platform_layers'). Models elsewhere, and
    models with an explicit +database config, keep dbt's default behavior.
#}
{% macro generate_database_name(custom_database_name=none, node=none) -%}
    {%- if custom_database_name is not none -%}
        {{ custom_database_name | trim }}
    {%- elif node is not none and node.fqn | length > 2 and (node.fqn[1] | upper) in var('platform_layers') -%}
        {{ var('platform_prefix') }}_{{ target.name | upper }}_{{ node.fqn[1] | upper }}
    {%- else -%}
        {{ target.database }}
    {%- endif -%}
{%- endmacro %}
