# Observability

### Key Metrics to Monitor

| Metric | Alert When |
|--------|------------|
| `used_memory` | > 80% of maxmemory |
| `connected_clients` | Sudden spikes or drops |
| `blocked_clients` | > 0 sustained |
| `instantaneous_ops_per_sec` | Significant drops |
| `keyspace_hits/misses` | Hit ratio < 80% |
| `rejected_connections` | > 0 |

```python
info = r.info()
hit_ratio = info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100
print(f"Memory: {info['used_memory_human']}, Ops/sec: {info['instantaneous_ops_per_sec']}, Hit ratio: {hit_ratio:.1f}%")
```

### Debugging Commands

```
SLOWLOG GET 10          # Find slow commands
MEMORY USAGE mykey      # Per-key memory
MEMORY DOCTOR           # Memory diagnostics
FT.INFO idx:products    # Index stats
FT.PROFILE idx:products SEARCH QUERY "@name:laptop"  # Query profiling
CLIENT LIST             # Active connections
```

