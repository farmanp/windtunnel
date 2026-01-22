# AI-Ready Story Template (Spike)

## 1. Intent (Required)
**Research Question:**
How should Turbulence evolve to support non-HTTP workloads including streaming pipelines, binary protocols, and job orchestrators while maintaining a cohesive action abstraction?

**Why This Matters:**
Modern distributed systems use diverse communication patterns beyond REST APIs. Teams testing microservices need to validate Kafka message flows, gRPC service meshes, Spark job outputs, and Airflow DAG executions. Without multi-protocol support, Turbulence is limited to HTTP-only systems.

**Success Looks Like:**
A concrete architecture proposal with:
- Plugin interface design for custom action types
- Generalized Observation model that works across protocols
- Prototype implementation of at least one non-HTTP transport
- Clear roadmap for priority protocol support

## 2. Research Scope (Required)

### 2.1 Protocol Categories to Investigate

#### Category A: Message Brokers & Streaming Platforms
| System | Pattern | Key Challenges |
|--------|---------|----------------|
| Apache Kafka | Produce/Consume | Consumer groups, offsets, partitions, serialization (Avro, Protobuf, JSON) |
| AWS Kinesis | Put/Get Records | Shard management, sequence numbers |
| Google Pub/Sub | Publish/Subscribe | Ack deadlines, ordering keys |
| RabbitMQ | Produce/Consume | Exchanges, routing keys, queues |
| Redis Streams | XADD/XREAD | Stream IDs, consumer groups |

**Research Questions:**
- How to express "send message, then assert another message arrives" in YAML?
- How to handle schema registries (Confluent, AWS Glue)?
- How to manage consumer offsets across test instances?
- What's the Observation model for a consumed message?

#### Category B: RPC & Binary Protocols
| Protocol | Pattern | Key Challenges |
|----------|---------|----------------|
| gRPC | Unary, Server/Client/Bidi Streaming | Proto compilation, reflection, metadata, deadlines |
| Apache Thrift | RPC | IDL compilation, multiple transports |
| GraphQL | Query/Mutation/Subscription | Schema introspection, variables, subscriptions |
| WebSocket | Bidirectional | Connection lifecycle, message framing, heartbeats |
| WebRTC | P2P Data/Media | Signaling, ICE, DTLS, SRTP (likely out of scope) |

**Research Questions:**
- How to reference .proto files in scenarios?
- How to handle gRPC streaming (multiple responses)?
- How to express WebSocket conversation sequences?
- What's the Observation model for streaming responses?

#### Category C: Job Orchestrators
| System | Pattern | Key Challenges |
|--------|---------|----------------|
| Apache Airflow | Trigger DAG → Poll → Verify | REST API available, task instance states |
| Apache Spark | Submit Job → Poll → Verify Output | Multiple submission modes (REST, spark-submit, Livy) |
| Dagster | Launch Run → Poll → Verify | GraphQL API, asset materialization |
| Prefect | Create Flow Run → Poll | REST API, flow run states |
| AWS Step Functions | Start Execution → Poll | Execution ARN, state machine history |
| Temporal | Start Workflow → Query/Signal → Poll | Workflow IDs, query handlers |

**Research Questions:**
- Is the current `wait` action sufficient, or is a dedicated `job` action cleaner?
- How to verify job outputs (S3, databases, etc.)?
- How to handle job-specific metadata (Spark application ID, Airflow run ID)?

#### Category D: Data Verification
| Target | Pattern | Key Challenges |
|--------|---------|----------------|
| SQL Databases | Query → Assert | Connection pooling, dialect differences |
| S3/GCS/Azure Blob | List/Head/Get | Credentials, eventual consistency |
| Elasticsearch | Search → Assert | Query DSL |
| MongoDB | Find → Assert | Query syntax |

**Research Questions:**
- Should data verification be separate actions or part of `assert`?
- How to handle connection credentials securely?
- How to express complex queries in YAML?

### 2.2 Architecture Questions

#### Action Plugin Interface
```python
# Current interface
class BaseAction(ABC):
    @abstractmethod
    async def execute(self, context: Context) -> Observation:
        pass

# Questions:
# 1. Is this sufficient for all protocols?
# 2. How to handle connection lifecycle (connect/disconnect)?
# 3. How to handle streaming (multiple observations)?
# 4. How to register plugins dynamically?
```

**Options to Evaluate:**
| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A. Built-in actions | All protocols in core package | Simple, consistent | Bloated dependencies |
| B. Plugin packages | `turbulence-kafka`, `turbulence-grpc` | Lean core, optional deps | Discovery, versioning |
| C. Custom action YAML | User defines actions via config | Maximum flexibility | Complex, error-prone |
| D. Hybrid | Core protocols built-in, plugin interface for custom | Balance | More complexity |

#### Observation Model Evolution
```python
# Current (HTTP-centric)
class Observation(BaseModel):
    ok: bool
    status_code: int | None  # HTTP-specific
    headers: dict | None      # HTTP-specific
    body: Any
    latency_ms: float
    errors: list[str]

# Proposed (Protocol-agnostic)
class Observation(BaseModel):
    ok: bool
    latency_ms: float
    errors: list[str]

    # Protocol-specific metadata
    transport: str  # "http", "grpc", "kafka", etc.
    metadata: dict  # Flexible per-protocol

    # Payload (unified)
    payload: Any

    # For streaming: multiple payloads?
    payloads: list[Any] | None
```

**Questions:**
- How to maintain backward compatibility?
- How to handle streaming (unbounded responses)?
- How to express protocol-specific assertions?

#### Async/Job Pattern
```yaml
# Option A: Extended wait action
- type: http
  name: trigger_spark_job
  path: /batches
  method: POST
  extract:
    batch_id: "$.id"

- type: wait
  name: poll_job
  poll:
    type: http
    path: "/batches/{{batch_id}}"
  until:
    jsonpath: "$.state"
    in: ["success", "dead"]
  timeout: 600s

# Option B: First-class job action
- type: job
  name: run_spark_job
  submit:
    type: http
    path: /batches
    method: POST
  poll:
    path: "/batches/{{batch_id}}"
    interval: 5s
  success_states: ["success"]
  failure_states: ["dead", "killed"]
  timeout: 600s
  extract:
    output_path: "$.appInfo.outputPath"
```

**Questions:**
- Is `job` action abstraction worth the complexity?
- How to handle job-specific failure modes?
- How to integrate output verification?

### 2.3 Prototype Candidates

Implement one prototype to validate the architecture:

| Candidate | Why | Complexity |
|-----------|-----|------------|
| gRPC Unary | Common in microservices, well-defined semantics | Medium |
| Kafka Produce/Consume | Very common in event-driven systems | Medium-High |
| SQL Query/Assert | Broadly useful for verification | Low-Medium |
| WebSocket | Tests bidirectional patterns | Medium |

**Recommendation:** Start with gRPC unary calls - structured request/response maps well to current model, validates proto handling.

## 3. Deliverables (Required)

### Phase 1: Discovery (Research)
- [ ] Survey 3-5 real-world use cases from potential users
- [ ] Document protocol requirements matrix
- [ ] Evaluate existing tools (Gatling, k6, Locust) for protocol support patterns
- [ ] Identify Python libraries for each protocol category

### Phase 2: Design (Architecture)
- [ ] RFC: Action Plugin Interface specification
- [ ] RFC: Generalized Observation Model
- [ ] RFC: Async Job Pattern
- [ ] Decision: Which protocols to support in core vs. plugins
- [ ] Decision: Backward compatibility strategy

### Phase 3: Prototype (Validation)
- [ ] Implement prototype action (recommend: gRPC unary)
- [ ] Write sample scenario using new action
- [ ] Validate Observation model works
- [ ] Document learnings and adjustments needed

### Phase 4: Roadmap (Planning)
- [ ] Priority-ordered protocol support roadmap
- [ ] Effort estimates for each protocol
- [ ] Create feature tickets for top 3 protocols

## 4. Constraints (Required)

**Time-box:** This spike should be time-boxed to avoid scope creep. Recommend 2-3 focused sessions.

**Must NOT:**
- Implement full protocol support (that's feature work)
- Break existing HTTP action functionality
- Add heavy dependencies to core package
- Over-engineer plugin system before validating need

**Out of Scope:**
- WebRTC (too complex, niche use case)
- Custom binary protocols (infinite scope)
- Performance optimization (premature)
- UI changes for protocol configuration

## 5. Research Resources

### Existing Tools to Study
| Tool | Multi-Protocol Support | Notes |
|------|----------------------|-------|
| [Gatling](https://gatling.io/) | HTTP, WebSocket, JMS, gRPC (paid) | Scala DSL, mature |
| [k6](https://k6.io/) | HTTP, WebSocket, gRPC, Redis, Kafka (extensions) | JS, extension model |
| [Locust](https://locust.io/) | HTTP (others via custom clients) | Python, user classes |
| [Karate](https://karatelabs.io/) | HTTP, gRPC, Kafka, WebSocket | BDD-style, JVM |
| [Artillery](https://artillery.io/) | HTTP, WebSocket, Socket.io | YAML config |

### Python Libraries
| Protocol | Library | Notes |
|----------|---------|-------|
| gRPC | `grpcio`, `grpcio-tools` | Official, well-maintained |
| Kafka | `aiokafka`, `confluent-kafka` | Async support varies |
| WebSocket | `websockets`, `aiohttp` | Both mature |
| SQL | `sqlalchemy`, `asyncpg`, `aiomysql` | Async ecosystem good |
| S3 | `aiobotocore` | Async AWS |
| GraphQL | `gql`, `httpx` | Client libraries |

### Reference Architectures
- [k6 Extensions Architecture](https://k6.io/docs/extensions/)
- [Gatling Protocol Support](https://gatling.io/docs/gatling/reference/current/protocols/)
- [Locust Custom Clients](https://docs.locust.io/en/stable/testing-other-systems.html)

## 6. Success Criteria

This spike is successful if we can answer:

1. **Architecture:** What's the right abstraction for multi-protocol actions?
2. **Model:** How should Observation evolve to be protocol-agnostic?
3. **Feasibility:** Can we implement gRPC/Kafka without major refactoring?
4. **Roadmap:** Which protocols should we prioritize and why?
5. **Scope:** What's core vs. plugin vs. out-of-scope?

## 7. Planned Outputs

- [ ] `docs/rfcs/RFC-001-action-plugin-interface.md`
- [ ] `docs/rfcs/RFC-002-observation-model-v2.md`
- [ ] `src/turbulence/actions/grpc.py` (prototype)
- [ ] `tickets/FEAT-030-grpc-action.md` (or similar, based on findings)
- [ ] Updated `TICKET-GRAPH.md` with protocol roadmap

## 8. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| FEAT-007 (Context Templating) | DONE | Needed for variable substitution |
| FEAT-008 (Artifact Storage) | DONE | Observations must be storable |
| FEAT-014 (Expression Evaluator) | DONE | For complex assertions |

No blocking dependencies - this spike can start immediately.
