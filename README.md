# Real-Time Machine Data Ingestion Service

## Overview

This project implements a microservice responsible for receiving, storing, and serving real-time sensor data from hundreds of industrial machines. Conceptual clarity, efficient design, and best practices (modularity, validation, error handling) are prioritized.

## Question 1.1: Database Design (Data Modeling)

### Machine Metadata (PostgreSQL)
We use PostgreSQL as a relational database to store machine metadata. It is well-suited for structured data that changes infrequently and requires ACID compliance.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE machine_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    sensor_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for frequent lookups and filtering
CREATE INDEX idx_machine_location ON machine_metadata(location);
CREATE INDEX idx_machine_status ON machine_metadata(status);
```

### Sensor Data (InfluxDB)
InfluxDB is utilized for the high-frequency time-series sensor data because of its high write throughput and optimized time-window aggregations.

*   **Measurement**: `sensor_data` (This is akin to an SQL table, containing all metrics).
*   **Tags** (Indexed, strings, used for filtering/grouping operations):
    *   `machine_id` (UUID string matching PostgreSQL)
    *   `location` (String, optional redundancy for faster geographical queries without joining Postgres)
    *   `sensor_type` (String)
*   **Fields** (Not indexed, containing the actual telemetry values):
    *   `temperature` (Float)
    *   `pressure` (Float)
    *   `speed` (Float)
*   **Timestamp**: The primary index, stored with nanosecond precision.

### Optimization Strategy for Analytics
To ensure rapid query execution for weekly/monthly historical analytics across hundreds of machines, we implement the following:

1.  **Downsampling (Continuous Queries / Tasks)**:
    Raw sensor data is typically needed only for immediate real-time monitoring. For historical analytics, querying millions of raw data points directly is slow. We create InfluxDB background Tasks to periodically roll up data (e.g., executing `mean()`, `max()`, `min()` over 5-minute, 1-hour, or 1-day windows) and store the results in separate, aggregated buckets. Weekly/monthly queries are directed to these downsampled buckets, parsing drastically less data.
2.  **Data Retention Policies (RPs)**:
    *   **Raw Bucket**: Keep high-resolution data for a short period (e.g., 7 or 14 days).
    *   **Downsampled Buckets**: Keep aggregated data (like hourly averages) for a much longer term (e.g., 2 years). This saves storage and maintains query speed over time.
3.  **Shard Group Optimization**:
    InfluxDB stores data in shards grouped by a specific time range. Aligning the Shard Group Duration with the Retention Policy eliminates overhead. A 7-day RP should use a 1-day shard group duration. For multi-year RP (downsampled bucket), we configure longer shard group durations (e.g., 1 month or 6 months) to avoid having too many small shards, maximizing memory and disk I/O efficiency.

---

## Question 1.2: RESTful API Design

### Ingestion Endpoint (`POST /api/v1/data/ingest`)

We assume ingestion happens via industrial gateways pushing batched sensor payloads, which is more network-efficient than single-point requests.

**JSON Request Body design:**
```json
{
  "gateway_id": "gw-001-factoryA",
  "payloads": [
    {
      "machine_id": "123e4567-e89b-12d3-a456-426614174000",
      "timestamp": "2023-10-27T10:00:00Z",
      "metrics": {
         "temperature": 45.5,
         "pressure": 1.2,
         "speed": 1500.0
      }
    },
    {
      "machine_id": "123e4567-e89b-12d3-a456-426614174000",
      "timestamp": "2023-10-27T10:00:05Z",
      "metrics": {
         "temperature": 45.8,
         "pressure": 1.3
         // speed may be missing depending on the sensor configurations, validation handles this
      }
    }
  ]
}
```

### Retrieval Endpoint (`GET /api/v1/data/machine/{machine_id}`)

Retrieves bounded historical data for a given machine target.

**Query Parameters:**
*   `start_time` (string, required): Standard ISO 8601 datetime defining the beginning of the retrieval window (e.g., `2023-10-20T00:00:00Z`).
*   `end_time` (string, required): Standard ISO 8601 datetime defining the end of the retrieval window. Must be chronological after `start_time`.
*   `interval` (string, optional): Defines the aggregation frequency for the time range (e.g., `1m`, `1h`, `1d`). If absent, raw telemetry is returned, otherwise the downsampled buckets fall under query scope to construct aggregated points.

### Brief Implementation Snippet

The ingestion endpoint code in FastAPI is available in `main.py`, showcasing robust Pydantic data validation logic over input formats, allowable boundaries, and timestamp checking before returning a `202 Accepted` response for decoupled batch-ingestion architectures.