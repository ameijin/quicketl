# Observability

QuickETL integrates with OpenTelemetry for tracing and metrics, and OpenLineage for data lineage tracking.

## Overview

| Feature | Package | Purpose |
|---------|---------|---------|
| Tracing | OpenTelemetry | Distributed tracing across pipeline steps |
| Metrics | OpenTelemetry | Rows processed, transform duration |
| Lineage | OpenLineage | Track data flow and dependencies |

## Installation

```bash
# OpenTelemetry (tracing + metrics)
pip install "quicketl[opentelemetry]"

# OpenLineage (data lineage)
pip install "quicketl[openlineage]"

# Both (enterprise bundle)
pip install "quicketl[enterprise]"
```

---

## OpenTelemetry Tracing

Trace pipeline execution with spans for each transform.

### Quick Start

```python
from quicketl.telemetry import TracingContext

# Initialize tracing
ctx = TracingContext(service_name="my-etl-pipeline")

# Create spans for operations
with ctx.span("pipeline_execution"):
    with ctx.span("read_source", attributes={"source": "s3://bucket/data"}):
        data = read_data()

    with ctx.span("transform_filter", attributes={"transform.type": "filter"}):
        filtered = apply_filter(data)

    with ctx.span("write_sink", attributes={"sink": "postgres"}):
        write_data(filtered)
```

### Configuration

Configure the OpenTelemetry SDK to export traces:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Set up the tracer provider
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Now use TracingContext
from quicketl.telemetry import TracingContext
ctx = TracingContext(service_name="quicketl")
```

### Span Attributes

Add meaningful attributes to spans:

```python
with ctx.span("transform", attributes={
    "transform.type": "filter",
    "transform.predicate": "amount > 100",
    "rows.input": 10000,
    "rows.output": 5000,
}):
    result = engine.filter(table, "amount > 100")
```

### Error Recording

Errors are automatically recorded in spans:

```python
with ctx.span("risky_operation"):
    if something_wrong:
        raise ValueError("Data validation failed")
# Exception is recorded in the span with stack trace
```

---

## OpenTelemetry Metrics

Track quantitative data about pipeline execution.

### Quick Start

```python
from quicketl.telemetry import MetricsContext

ctx = MetricsContext(service_name="my-etl-pipeline")

# Record rows processed
ctx.record_rows_processed(10000, transform_type="filter")

# Record transform duration
ctx.record_transform_duration(0.5, transform_type="aggregate")
```

### Available Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `quicketl.rows.processed` | Counter | Total rows processed |
| `quicketl.transform.duration` | Histogram | Transform execution time |

### Configuration

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Set up metrics
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://localhost:4317"),
    export_interval_millis=60000,
)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

# Now use MetricsContext
from quicketl.telemetry import MetricsContext
ctx = MetricsContext(service_name="quicketl")
```

---

## Correlation IDs

Track requests across distributed systems with correlation IDs.

```python
from quicketl.telemetry import get_correlation_id
from quicketl.telemetry.context import set_correlation_id, reset_correlation_id

# Get current correlation ID (auto-generated if not set)
correlation_id = get_correlation_id()
print(f"Processing request: {correlation_id}")

# Set a specific correlation ID (e.g., from incoming request)
set_correlation_id("request-123-abc")

# Reset for a new request
reset_correlation_id()
new_id = get_correlation_id()  # New UUID generated
```

---

## OpenLineage

Track data lineage: where data comes from, how it's transformed, and where it goes.

### Quick Start

```python
from quicketl.telemetry.openlineage import LineageContext

# Initialize lineage tracking
ctx = LineageContext(
    namespace="quicketl",
    job_name="daily-sales-pipeline",
)

# Define inputs
ctx.add_input_dataset(
    namespace="s3://data-lake",
    name="raw_sales",
    schema={"id": "string", "amount": "float", "date": "date"},
)

# Define outputs
ctx.add_output_dataset(
    namespace="postgres://warehouse",
    name="processed_sales",
    schema={"id": "string", "total": "float"},
    column_lineage={
        "total": ["amount"],  # total comes from amount
    },
)

# Emit events
ctx.emit_start()
# ... run pipeline ...
ctx.emit_complete()
```

### Event Types

| Event | Method | When |
|-------|--------|------|
| START | `emit_start()` | Pipeline begins |
| COMPLETE | `emit_complete()` | Pipeline succeeds |
| FAIL | `emit_fail(error)` | Pipeline fails |

### Column Lineage

Track which input columns flow to which output columns:

```python
ctx.add_output_dataset(
    namespace="postgres://warehouse",
    name="customer_summary",
    column_lineage={
        "full_name": ["first_name", "last_name"],  # Concatenated
        "total_spent": ["order_amount"],  # Aggregated
        "last_order": ["order_date"],  # Selected
    },
)
```

### Integration with Marquez

OpenLineage events are compatible with [Marquez](https://marquezproject.github.io/marquez/):

```python
from openlineage.client import OpenLineageClient
from openlineage.client.transport.http import HttpConfig, HttpCompression, HttpTransport

# Configure Marquez endpoint
config = HttpConfig(
    url="http://localhost:5000",
    compression=HttpCompression.GZIP,
)
client = OpenLineageClient(transport=HttpTransport(config))

# Use with LineageContext
ctx = LineageContext(
    namespace="quicketl",
    job_name="my-pipeline",
    client=client,
)
```

---

## Complete Example

Combine tracing, metrics, and lineage:

```python
import time
from quicketl.telemetry import TracingContext, MetricsContext, get_correlation_id
from quicketl.telemetry.openlineage import LineageContext

# Initialize all contexts
tracing = TracingContext(service_name="sales-pipeline")
metrics_ctx = MetricsContext(service_name="sales-pipeline")
lineage = LineageContext(namespace="quicketl", job_name="daily-sales")

# Add datasets
lineage.add_input_dataset("s3://bucket", "raw_sales")
lineage.add_output_dataset("postgres://db", "processed_sales")

# Run pipeline with observability
correlation_id = get_correlation_id()
print(f"Starting pipeline run: {correlation_id}")

lineage.emit_start()

try:
    with tracing.span("pipeline", attributes={"correlation_id": correlation_id}):

        with tracing.span("read"):
            start = time.time()
            data = read_source()
            metrics_ctx.record_rows_processed(len(data), transform_type="read")
            metrics_ctx.record_transform_duration(time.time() - start, transform_type="read")

        with tracing.span("transform"):
            start = time.time()
            result = transform_data(data)
            metrics_ctx.record_rows_processed(len(result), transform_type="transform")
            metrics_ctx.record_transform_duration(time.time() - start, transform_type="transform")

        with tracing.span("write"):
            start = time.time()
            write_sink(result)
            metrics_ctx.record_transform_duration(time.time() - start, transform_type="write")

    lineage.emit_complete()

except Exception as e:
    lineage.emit_fail(str(e))
    raise
```

---

## Backends

### Jaeger (Tracing)

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

Configure exporter:
```python
exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
```

### Prometheus (Metrics)

```python
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server

# Start Prometheus endpoint
start_http_server(8000)
reader = PrometheusMetricReader()
```

### Marquez (Lineage)

```bash
docker-compose -f docker-compose.marquez.yml up
```

Access UI at http://localhost:3000

---

## Best Practices

1. **Use meaningful span names** - `transform.filter` not just `filter`
2. **Add context attributes** - Include table names, row counts, predicates
3. **Propagate correlation IDs** - Pass through HTTP headers for distributed tracing
4. **Sample in production** - Use probabilistic sampling to reduce overhead
5. **Set up alerting** - Create alerts on error spans and high latency
6. **Track lineage continuously** - Emit events even for incremental runs
