---
layout: ../../layouts/Layout.astro
title: System Design Basics
---

# System Design Basics

> Backend / full-stack interview prompts. Walk through scope, scale, storage, and bottlenecks.

## The 4 S's framework

| | What you discuss |
|---|---|
| **Scenario** | features, MAU/DAU, QPS, read/write ratio |
| **Service** | break system into services / modules |
| **Storage** | pick DB/cache; design schema; sharding strategy |
| **Scale** | bottlenecks, replication, async, CDN |

Always start by clarifying **scenario** before drawing boxes.

## QPS by storage type — rule of thumb

| System | Single-machine QPS |
|---|---|
| MySQL / PostgreSQL (SQL) | ~1,000 |
| MongoDB / Cassandra (disk NoSQL) | ~10,000 |
| Redis / Memcached (in-memory) | ~100,000 – 1,000,000 |

These are *order-of-magnitude* numbers — picks depend on consistency requirements, not just QPS.

## DB selection — quick decision tree

- Need **transactions / joins** → SQL (MySQL, Postgres)
- Need **horizontal scale** + flexible schema → wide-column NoSQL (Cassandra, Bigtable)
- Need **document model** → MongoDB
- Need **lookup speed** + ephemeral data → Redis / Memcached (cache, not source of truth)
- Need **search** → Elasticsearch / Solr
- Need **analytics** → columnar (BigQuery, Redshift, ClickHouse)

Hybrid is normal: MySQL for source of truth + Memcached for read cache + Elasticsearch for full-text.

## Cache patterns

### Cache-aside (look-aside) — the default

![](/notes/system-design/media/image1.png)

```
read(key):
    val = cache.get(key)
    if val is None:                          # cache miss
        val = db.read(key)
        cache.set(key, val, ttl=...)
    return val

write(key, val):
    db.write(key, val)
    cache.delete(key)                        # OR cache.set; see below
```

### Cache write strategy

| Strategy | Behavior | Tradeoff |
|---|---|---|
| **Write-through** | write to cache + DB synchronously | reads always fresh; slow writes |
| **Write-back** | write cache, flush to DB later | fast writes; risk losing data on crash |
| **Write-around** | write only to DB; invalidate cache | safe; first read pays a miss penalty |
| **Cache invalidation on write** | DB write + delete cache key | simple; brief stale window during eviction |

> Why "delete cache" instead of "set cache" on write? If two writes interleave with a slow `set`, the cache can end up with the older value. **Delete-on-write + repopulate-on-read** avoids that race.

### Cache hit rate — typical

User-table cache hit rate is usually **>95%**: most users are read-heavy and a small set is hot.

`hit_rate = cache_hits / (cache_hits + cache_misses)`

If your hit rate is < 80%, your TTL is wrong, your cache is too small, or your access pattern is wrong for caching.

## Sharding (write-heavy systems)

When write QPS exceeds a single DB, split data across machines.

![](/notes/system-design/media/image3.png)

| Strategy | How |
|---|---|
| **Range sharding** | shard by `user_id` ranges (`A-G`, `H-N`, …) |
| **Hash sharding** | `shard = hash(key) % N` |
| **Consistent hashing** | hash key + shards onto a ring; each key maps to next shard clockwise. Adds/removes shards move only `~1/N` keys. |

Consistent hashing is the standard for caches and sharded stores precisely because resharding is cheap.

## Replication — read-heavy systems

| Pattern | Use case |
|---|---|
| **Master + replica** | write to master; reads from replicas (eventually consistent) |
| **Multi-master** | writes anywhere; needs conflict resolution (CRDTs, last-write-wins) |
| **Quorum** (Cassandra/Dynamo) | tunable: write to W replicas, read from R, with `R + W > N` for strong reads |

## Common patterns by problem type

| Prompt | Key concepts |
|---|---|
| **News Feed** (Facebook, Twitter) | push (fan-out on write) vs pull (fan-out on read); hybrid by user popularity; Redis sorted set for the feed; CDN for media |
| **URL Shortener** (TinyURL, bit.ly) | base62 encode of incrementing ID, or hash-of-url; KV store; cache hot URLs |
| **Chat** (WhatsApp, Slack) | WebSocket for live; message queue (Kafka) per channel; long-poll fallback; outbox pattern for reliable delivery |
| **Rate Limiter** | token bucket per user in Redis with `INCR` + `EXPIRE`; sliding window log for stricter limits |
| **Top K** | reservoir sampling, count-min sketch, hyperloglog for distinct counts |
| **Pastebin** | object store (S3) for content; KV (Redis) for metadata; signed URLs for access |
| **Search Autocomplete** | trie in memory + log of queries; rebuild trie offline; rank by frequency |
| **Web Crawler** | URL frontier (priority queue), bloom filter for "seen", per-host rate limit, distributed via Kafka |

## CAP — pick 2 of 3 (during partition)

- **C**onsistency — every read returns the latest write
- **A**vailability — every request gets a response (even if stale)
- **P**artition tolerance — system works despite network splits

In practice, P is non-negotiable in distributed systems → choose **CP** (banks, locks) or **AP** (DNS, social feeds).

## Latency anchors (memorize, ish)

| Op | Time |
|---|---|
| L1 cache | 1 ns |
| L2 cache | 4 ns |
| Main memory | 100 ns |
| SSD random read | 16 µs |
| Round-trip same datacenter | 0.5 ms |
| Disk seek | 4 ms |
| HDD sequential read 1 MB | 10 ms |
| Round-trip cross-Atlantic | 150 ms |

Use these to **back-of-envelope** capacity: "1M users * 10 reads/sec * 0.5 ms cache latency = 5,000 cache QPS — fine for one Redis instance."

## Interview cheat-sheet behavior

- **Always** ask scope/scale before designing — what features, how many users, read/write ratio.
- **Estimate** first (Fermi-style), then size storage and machines.
- **Draw** boxes + arrows; label each arrow with protocol + direction (HTTP, gRPC, async queue).
- **Identify the bottleneck** before optimizing — almost always the DB, then network, then CPU.
- **Talk tradeoffs** out loud — "We could go strong consistency here, but it'd cost 3x latency."

## Practice prompts

- **Design a URL shortener** (TinyURL) — high read, append-only writes; consistent hashing for cache; encode collision strategy.
- **Design a news feed** (Facebook) — fan-out write vs read tradeoffs; per-user feed in Redis; pull on top users.
- **Design a chat system** (WhatsApp) — WebSocket connection routing; message persistence; group messaging fan-out.
- **Design a rate limiter** — token bucket vs leaky bucket vs sliding window; Redis Lua for atomicity.
- **Design a key-value store** (Dynamo-style) — consistent hashing, replication factor, vector clocks for conflicts.
- **Design Twitter** — timeline assembly; trending topics (count-min sketch); search index.
- **Design Uber** — driver location updates (geohash quad-tree); matching algorithm; surge pricing.
- **Design a search autocomplete** — trie + frequency rank; cache top suggestions.
