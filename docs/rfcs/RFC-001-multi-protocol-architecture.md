# RFC-001: Multi-Protocol Transport Architecture

## 1. Objective
Evolve Turbulence from an HTTP-centric tool into a generalized distributed systems testing framework capable of handling gRPC, Kafka, SQL, and other protocols through a unified plugin architecture.

## 2. Proposed Design

### 2.1 Action Plugin Interface
We will move away from hardcoded action types in the engine and introduce an `ActionRegistry`.

```python
class BaseAction(BaseModel, ABC):
    name: str
    type: str  # Action type identifier (e.g., "http", "grpc", "kafka")
    
    @abstractmethod
    async def execute(self, context: dict, sut: SUTConfig) -> tuple[Observation, dict]:
        """Execute the action and return the result."""
```

### 2.2 Action Registry
A central registry will allow dynamic discovery of action runners.

```python
class ActionRegistry:
    _actions = {}

    @classmethod
    def register(cls, type_name: str, action_class: Type[BaseAction]):
        cls._actions[type_name] = action_class

    @classmethod
    def get_action_class(cls, type_name: str) -> Type[BaseAction]:
        return cls._actions.get(type_name)
```

### 2.3 Protocol-Agnostic Observation Model
The `Observation` model will be refactored to prioritize protocol-specific metadata while keeping a common core.

```python
class Observation(BaseModel):
    ok: bool
    latency_ms: float
    errors: list[str] = []
    
    # Metadata for the specific protocol
    protocol: str  # "http", "grpc", etc.
    meta: dict[str, Any] = {} 
    
    # Unified payload access
    body: Any = None
    
    # For streaming support
    events: list[Any] = []
```

## 3. Supported Categories

### Category A: Streaming (Kafka, Pub/Sub)
- **Action:** `kafka_produce`, `kafka_consume`
- **Metadata:** topic, partition, offset, key
- **Success Criteria:** Message published OR message received matching filter.

### Category B: RPC (gRPC)
- **Action:** `grpc_call`
- **Metadata:** service, method, status_code, trailers
- **Challenge:** Requires `.proto` file management or reflection.

### Category C: Data (SQL, S3)
- **Action:** `sql_query`, `s3_put`
- **Metadata:** rows_affected, query_time
- **Success Criteria:** Result set matches expectation.

## 4. Implementation Strategy

1.  **Phase 1: Registry:** Implement `ActionRegistry` and refactor `ScenarioRunner` to use it instead of explicit `if/elif` blocks.
2.  **Phase 2: Generic Observation:** Update `Observation` model to include `protocol` and `meta` fields (backward compatible).
3.  **Phase 3: gRPC Prototype:** Implement a gRPC unary action as a proof-of-concept plugin.

## 5. Backward Compatibility
- Existing `HttpAction`, `WaitAction`, and `AssertAction` will be the first "plugins" registered in the system.
- The `Observation` model will keep `status_code` and `headers` as property helpers that map to the new `meta` dictionary if the protocol is HTTP.

## 6. Security Considerations
Dynamic loading of plugins (if supported via filesystem) requires careful validation to prevent arbitrary code execution. Initially, plugins will be restricted to those explicitly imported in the Turbulence package.
