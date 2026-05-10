# Level 4 — Multi-Tenant Namespacing

## What you're implementing

Extend `FileCache` to support multiple tenants. Each tenant has its own file namespace and a per-tenant file quota.

```python
def register_tenant(self, tenant_id: str, file_quota: int) -> bool: ...
def tenant_store(self, tenant_id: str, filename: str, content: str) -> bool: ...
def tenant_fetch(self, tenant_id: str, filename: str) -> str: ...
def tenant_remove(self, tenant_id: str, filename: str) -> bool: ...
def tenant_update(self, tenant_id: str, filename: str, content: str) -> bool: ...
def tenant_fetch_by_prefix(self, tenant_id: str, prefix: str) -> list[str]: ...
def tenant_size(self, tenant_id: str) -> int: ...
```

**All Level 1–3 methods remain intact** and operate on a hidden "global" tenant with no quota.

## Mental model

Imagine a shared cloud storage service (like S3 with IAM boundaries). Multiple customers ("tenants") use the same physical cache. Each tenant has their own file namespace — `alice`'s `notes.txt` and `bob`'s `notes.txt` are different files. Each tenant also has a file count quota they cannot exceed.

The cache-wide LRU eviction (`set_capacity`) still works across all tenants — it evicts the globally least-recently-used file, regardless of which tenant owns it. Evicting a tenant's file frees their quota slot.

## The new methods

### A. `register_tenant(tenant_id: str, file_quota: int) -> bool`

Register a new tenant with a per-tenant file quota.

| Situation | Return |
|-----------|--------|
| New tenant | `True` — registered |
| Already registered | `False` — no-op |

### B. `tenant_store(tenant_id, filename, content) -> bool`

Store a file for tenant. Returns `False` if:
- `tenant_id` not registered
- `filename` already exists for this tenant
- Tenant is at or over their quota

### C–G. `tenant_fetch`, `tenant_remove`, `tenant_update`, `tenant_fetch_by_prefix`, `tenant_size`

Same semantics as L1/L2 counterparts, but scoped to `tenant_id`. Return `""` / `False` / `[]` / `0` for unregistered tenants.

## Worked example

```python
cache = FileCache()
cache.register_tenant("alice", 2)  # True
cache.register_tenant("bob",   3)  # True
cache.register_tenant("alice", 5)  # False — already registered

# alice stores 2 files (at quota)
cache.tenant_store("alice", "notes.txt", "my notes")   # True
cache.tenant_store("alice", "todo.txt",  "buy milk")   # True
cache.tenant_store("alice", "overflow.txt", "oops")    # False — at quota

# bob can still store
cache.tenant_store("bob", "report.txt", "data")        # True

# Isolation: same filename, different namespaces
cache.tenant_fetch("alice", "report.txt")  # "" — alice doesn't have this file
cache.tenant_fetch("bob",   "report.txt")  # "data"

# Quota freed on remove
cache.tenant_remove("alice", "todo.txt")              # True
cache.tenant_store("alice",  "new.txt", "allowed!")   # True — quota freed

# L1 global methods still work
cache.store("global.txt", "G")  # True — global tenant, no quota
cache.fetch("global.txt")       # "G"
cache.tenant_fetch("alice", "global.txt")  # "" — not in alice's namespace

# set_capacity evicts across all tenants by LRU
cache.set_capacity(2)  # evicts until ≤ 2 total files across all tenants
```

## Constraints

- Tenant IDs are non-empty strings. `"alice"`, `"tenant-001"` are valid.
- Quota enforcement is per-tenant. One tenant filling up does NOT affect others.
- Global tenant (`store`/`fetch`/etc.) has no quota.
- `tenant_fetch_by_prefix` does NOT update LRU (same rule as `fetch_by_prefix`).
- Cache-wide `set_capacity` evicts the globally LRU file, which may belong to any tenant.

## Common gotchas

1. **Namespacing key:** a file is identified by `(tenant_id, filename)` — not just `filename`. Store with a composite key.
2. **Unregistered tenant operations return safe defaults** — `False`, `""`, `0`, `[]` — don't raise exceptions.
3. **`register_tenant` is idempotent on failure** — second call for same tenant returns `False` and doesn't change the quota.
4. **Global methods are backward-compatible** — `store("f.txt", "x")` and `tenant_store("alice", "f.txt", "x")` are independent. Don't route one through the other in a way that conflates the namespaces.
5. **Evicting a tenant's file decrements their quota count** — otherwise quota becomes permanently "stuck" lower than the actual file count.

## When you're done

```
python3 test_level4.py
```

All tests must pass before moving to Level 5.
