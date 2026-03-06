
# GONSTERS Technical Skill Assessment Answers

## Question 1.1: Database Design (Data Modeling)

### 1. Machine Metadata (PostgreSQL)

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

---

### 2. Sensor Data (InfluxDB)

InfluxDB is utilized for the high-frequency time-series sensor data because of its high write throughput and optimized time-window aggregations.

* **Measurement**: `sensor_data` (This is akin to an SQL table, containing all metrics).
* **Tags** (Indexed, strings, used for filtering/grouping operations):
  * `machine_id` (UUID string matching PostgreSQL)
  * `location` (String, optional redundancy for faster geographical queries without joining Postgres)
  * `sensor_type` (String)
* **Fields** (Not indexed, containing the actual telemetry values):
  * `temperature` (Float)
  * `pressure` (Float)
  * `speed` (Float)
* **Timestamp**: The primary index, stored with nanosecond precision.

---

### 3. Optimization Strategy for Analytics

To ensure rapid query execution for weekly/monthly historical analytics across hundreds of machines, we implement the following:

1. **Downsampling (Continuous Queries / Tasks)**:
    Raw sensor data is typically needed only for immediate real-time monitoring. For historical analytics, querying millions of raw data points directly is slow. We create InfluxDB background Tasks to periodically roll up data (e.g., executing `mean()`, `max()`, `min()` over 5-minute, 1-hour, or 1-day windows) and store the results in separate, aggregated buckets. Weekly/monthly queries are directed to these downsampled buckets, parsing drastically less data.
2. **Data Retention Policies (RPs)**:
    * **Raw Bucket**: Keep high-resolution data for a short period (e.g., 7 or 14 days).
    * **Downsampled Buckets**: Keep aggregated data (like hourly averages) for a much longer term (e.g., 2 years). This saves storage and maintains query speed over time.
3. **Shard Group Optimization**:
    InfluxDB stores data in shards grouped by a specific time range. Aligning the Shard Group Duration with the Retention Policy eliminates overhead. A 7-day RP should use a 1-day shard group duration. For multi-year RP (downsampled bucket), we configure longer shard group durations (e.g., 1 month or 6 months) to avoid having too many small shards, maximizing memory and disk I/O efficiency.

---

## Question 1.2: RESTful API Design

### 1. Ingestion Endpoint (`POST /api/v1/data/ingest`)

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

---

### 2. Retrieval Endpoint (`GET /api/v1/data/machine/{machine_id}`)

Retrieves bounded historical data for a given machine target.

**Query Parameters:**

* `start_time` (string, required): Standard ISO 8601 datetime defining the beginning of the retrieval window (e.g., `2023-10-20T00:00:00Z`).
* `end_time` (string, required): Standard ISO 8601 datetime defining the end of the retrieval window. Must be chronological after `start_time`.
* `interval` (string, optional): Defines the aggregation frequency for the time range (e.g., `1m`, `1h`, `1d`). If absent, raw telemetry is returned, otherwise the downsampled buckets fall under query scope to construct aggregated points.

---

### 3. Brief Implementation Snippet

The ingestion endpoint code is available in `app/api/v1/endpoints/ingest.py`, showcasing robust Pydantic data validation logic over input formats, allowable boundaries, and timestamp checking before returning a `202 Accepted` response for decoupled batch-ingestion architectures.

#### Ingestion Pseudocode

```text
# POST /api/v1/data/ingest

FUNCTION ingest_sensor_data(request_body: BatchIngestRequest):

    # ── 1. Validate that all requested machines exist in PostgreSQL ────────────────
    machine_ids = EXTRACT_MACHINE_IDS(request_body.payloads)
    invalid_ids = AWAIT machine_service.validate_machines_exist(machine_repo, machine_ids)
    
    IF invalid_ids IS NOT EMPTY:
        THROW HTTP_400_BAD_REQUEST("Machine(s) not found: " + invalid_ids)
        
    # ── 2. Structural & Semantic Validation (via Pydantic Schemas) ─────────────────
    # Validates input automatically before executing the function logic:
    # - gateway_id constraints
    # - Validates UUID correct format for machine_id
    # - Validates parameters boundaries (temperature, pressure, speed)
    # - Checks timestamps
    
    # ── 3. Process Batch ───────────────────────────────────────────────────────────
    # Send validated data batch to the service layer for writing into InfluxDB
    AWAIT process_sensor_data_batch(sensor_repo, batch=request_body)
    
    # ── 4. Acknowledgment ──────────────────────────────────────────────────────────
    RETURN HTTP_202_ACCEPTED("Sensor data ingestion queued successfully")
```

---

## Question 2.1: MQTT Code Flow Pseudocode

### 1. Code Flow

#### 1.1. Topic Subscribed

```text
factory/A/machine/+/telemetry
```

The `+` is a single-level MQTT wildcard that matches any machine identifier.

---

#### 1.2. MQQT Pseudocode

```text
FUNCTION mqtt_subscriber_main():

    # ── 1. CONNECT ──────────────────────────────────────────────────────────
    WHILE not stop_event is set:
        TRY:
            client = MQTT_CLIENT(
                host     = MQTT_BROKER_HOST,
                port     = MQTT_BROKER_PORT,
                clientId = MQTT_CLIENT_ID,
            )

            CONNECT client TO broker
            LOG "Connected to broker at {host}:{port}"

            # ── 2. SUBSCRIBE ─────────────────────────────────────────────────
            SUBSCRIBE client TO topic "factory/A/machine/+/telemetry"
            LOG "Subscribed to topic filter"

            # ── 3. MESSAGE LOOP ──────────────────────────────────────────────
            FOR EACH message IN client.messages:
                IF stop_event is set:
                    BREAK

                CALL on_message(topic=message.topic, payload=message.payload)

        CATCH MqttConnectionError AS err:
            LOG warning "Connection lost: {err}. Retry in 5 s…"
            SLEEP 5 seconds   # back-off before reconnecting


FUNCTION on_message(topic: string, payload: bytes):

    # ── 3.1  Extract machine_id from topic ───────────────────────────────────
    parts = topic.SPLIT("/")
    # Expected: ["factory", "<factory_id>", "machine", "<machine_id>", "telemetry"]
    IF len(parts) != 5 OR parts[2] != "machine" OR parts[4] != "telemetry":
        LOG warning "Unexpected topic structure – skipping"
        RETURN

    machine_id = UUID(parts[3])
    IF machine_id is invalid:
        LOG warning "Non-UUID machine segment – skipping"
        RETURN

    # ── 3.2  Decode + JSON-parse payload ─────────────────────────────────────
    data = JSON_PARSE(payload.DECODE("utf-8"))
    IF data is None:
        LOG error "Malformed payload – skipping"
        RETURN

    # ── 3.3  Validate via schema ─────────────────────────────────────────────
    # Use internal helper to build and validate the payload
    sensor_payload = _build_sensor_payload(machine_id, data)
    
    IF sensor_payload is None:
        LOG error "Schema validation failed – skipping"
        RETURN

    # ── 3.4  Verify machine exists in PostgreSQL ─────────────────────────────
    machine = AWAIT machine_repo.get_by_id(machine_id)
    IF machine IS None:
        LOG warning "Unknown machine {machine_id} – discarding"
        RETURN

    # ── 3.5  Persist to InfluxDB ─────────────────────────────────────────────
    batch = BatchIngestRequest(
        gateway_id = "mqtt-subscriber",
        payloads   = [sensor_payload]
    )
    TRY:
        AWAIT sensor_repo.write_batch(batch)
        LOG info "Data for machine {machine_id} written to InfluxDB"
    CATCH WriteError AS err:
        LOG error "InfluxDB write failed: {err}"
```

---

#### 1.3. Flow Summary

```text
MQTT Broker
    │  publish  factory/A/machine/<id>/telemetry  { … }
    ▼
MQTTSubscriberService.start()
    │  aiomqtt async message loop
    ▼
handle_mqtt_message(topic, payload)
    ├─ extract machine_id from topic
    ├─ JSON-parse payload
    ├─ Pydantic validation (SensorDataPayload)
    ├─ machine_repo.get_by_id(machine_id)   → PostgreSQL check
    └─ sensor_repo.write_batch(batch)       → InfluxDB write
```

---

### 2. WebSocket vs MQTT: Fundamental Differences & Decision Guide

#### 2.1 Fundamental Differences

| Dimension | MQTT | WebSocket |
| ----------- | ------ | ----------- |
| **Protocol model** | Publish-Subscribe (broker in the middle) | Client-Server (direct, full-duplex TCP) |
| **Connection owner** | Broker manages all connections; clients are decoupled | Each pair of endpoints maintains its own connection |
| **Message routing** | Topic-based routing by the broker (`factory/A/machine/+/telemetry`) | Application-level routing; client must address server directly |
| **Footprint** | Extremely lightweight (2-byte fixed header); designed for constrained devices | Heavier framing; general-purpose binary/text framing |
| **QoS** | Built-in QoS levels 0 / 1 / 2 (at-most-once → exactly-once guarantee) | No built-in delivery guarantee; must be implemented in application layer |
| **Persistent sessions** | Optional persistent session survives client reconnection; broker queues missed messages (QoS 1/2) | Stateless from the protocol's point of view; reconnect = new session |
| **Retained messages** | Broker can retain the last message on a topic and deliver it to new subscribers immediately | No equivalent; latest state must be fetched via separate request |
| **Connection initiation** | Device → Broker (device is always the initiator; broker is always reachable) | Typically Client → Server; either side can send once connected |
| **Fan-out** | Broker delivers one published message to *N* subscribers automatically | Server must loop over all connected clients and send individually |
| **Firewall / NAT friendliness** | Single outbound TCP/TLS to broker from every device | Same; but server push through a reverse proxy is common |

---

#### 2.2. When to Choose MQTT over WebSocket for a Real-Time Dashboard

Choose **MQTT as the data source** when **any** of the following conditions apply:

##### 1. Data originates from industrial / IoT devices

Sensors, PLCs, and microcontrollers natively speak MQTT. Translating their
output to WebSocket adds a conversion layer with no benefit.

##### 2. Hundreds or thousands of data streams

MQTT's topic tree and the broker's built-in fan-out mean the backend service
subscribes to one wildcard topic and receives data from every machine without
maintaining a per-machine WebSocket connection.

##### 3. Intermittent connectivity must be tolerated

With **QoS 1 or 2** and a **persistent session**, the broker queues messages
published while the subscriber was offline and replays them on reconnect.
A WebSocket connection drops all in-flight data when it closes.

##### 4. Last-known state must be available to late joiners

MQTT **retained messages** let a new dashboard subscriber instantly receive
the most recent reading for every machine, without waiting for the device to
publish again. WebSocket has no such primitive.

##### 5. Decoupling producers from consumers is critical

MQTT's publish-subscribe pattern means a new consumer (e.g. an alert service,
a secondary dashboard) can subscribe to the same topic with *zero changes* to
the device or the ingestion backend. With WebSocket the server must explicitly
know about and manage every consumer.

---

#### 2.3. When WebSocket is preferable

| Scenario | Prefer |
| ---------- | -------- |
| End-user browser dashboard consuming pre-aggregated data | **WebSocket** – browsers speak it natively; no broker needed |
| Bidirectional control (user sends commands, server sends state) | **WebSocket** – natural for interactive UIs |
| Simple single-server, few clients | **WebSocket** – less infrastructure overhead |
| Sub-50 ms latency requirement with bespoke protocol | **WebSocket** – full control over framing |

---

#### 2.4. Architecture of This Service

This service uses **MQTT as the primary ingestion channel** (device → broker →
`MQTTSubscriberService` → InfluxDB) and exposes the stored data over **REST / WebSocket** to dashboard clients—combining both protocols at the layer where
each is strongest.

```text
[Machine/Sensor]  →  [MQTT Broker]  →  [MQTTSubscriberService]  →  [InfluxDB]
                                                                         │
[Browser Dashboard]  ←  ──────── REST / WebSocket ─────────────  [FastAPI API]
```

---

## Question 2.2: Security and Authentication (RBAC)

### 1. JWT Design

To effectively support Role-Based Access Control (RBAC) without requiring a database lookup for every API request, the JWT payload must encapsulate the user's identity and their authorization privileges.

**Required Payload Claims:**

* **`sub` (Subject):** The unique User ID (usually a UUID). This identifies who is making the request, essential for auditing, logging, and performing user-specific actions.
* **`role` (Custom Claim):** The user's assigned role (e.g., `Operator`, `Supervisor`, `Management`). This is the core piece of information used for RBAC decisions.
* **`exp` (Expiration Time):** The timestamp when the token expires. Critical for security to limit the window of opportunity if a token is compromised.
* **`iat` (Issued At):** The timestamp when the token was created.
* **`jti` (JWT ID):** A unique identifier for the token. Useful if we need to implement token revocation (blacklisting) before expiration.

**Example Payload:**

```json
{
  "sub": "b2f618a3-9c8d-4e5a-8b1e-2f3a4c5d6e7f",
  "role": "Management",
  "name": "Jane Doe",
  "exp": 1700000000,
  "iat": 1699996400,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### 2. Authorization Flow

Below is the step-by-step workflow when a user with the `MANAGEMENT` role attempts to access a sensitive endpoint like `POST /api/v1/config/update`:

1. **Login & Authentication:**
    * The user sends their credentials (e.g., email/password) to the login endpoint (`POST /api/v1/auth/login`).
    * The backend validates the credentials against the database.
    * If valid, the system retrieves the user's profile and their assigned role (`Management`).
2. **JWT Generation:**
    * The backend generates a JWT. It signs the token using a secure, private secret key.
    * The payload is populated with the user's ID (`sub`) and role (`role: "Management"`).
    * The token is returned to the client in the response.
3. **API Request:**
    * The user tries to update the configuration by making a request to `POST /api/v1/config/update`.
    * The client attaches the JWT to the request, typically in the `Authorization` header as a Bearer token (`Authorization: Bearer <token>`).
4. **Token Validation (Authentication Middleware):**
    * The API intercepts the request. The authentication dependency reads the header and extracts the JWT.
    * The backend verifies the token's cryptographic signature using the server's secret key to ensure it hasn't been altered.
    * The backend checks the `exp` claim to ensure the token isn't expired. If invalid or expired, a `401 Unauthorized` is returned.
5. **Role Verification (Authorization Middleware):**
    * After successful token validation, the authorization dependency extracts the `role` claim from the payload.
    * The endpoint `POST /api/v1/config/update` is configured to require the `Management` role.
    * The system compares the extracted role (`Management`) against the required role restrictions.
    * Since the user possesses the correct role, authorization is granted. (Had the role been `Operator` or `Supervisor`, a `403 Forbidden` would be returned).
6. **Request Execution & Response:**
    * The request proceeds to the endpoint's core logic.
    * The configuration is updated, and the server returns a success response (e.g., `200 OK`) to the client.
