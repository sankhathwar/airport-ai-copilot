# Airport Policy Knowledge Base

This directory contains synthetic airport operations policies used by the Airport Operations AI Copilot.

## Airports Covered

| Airport | Code |
|---|---|
| San Francisco International Airport | SFO |
| Los Angeles International Airport | LAX |
| John F. Kennedy International Airport | JFK |

## Policy Documents

- sfo_operations.md — Operations, pickup, drop-off, queue
- sfo_pricing.md — Pricing, surge, approval
- sfo_driver_policy.md — Queue, incentives, cancellations, conduct
- lax_operations.md — Operations, pickup, drop-off, queue
- lax_pricing.md — Pricing, surge, approval
- jfk_operations.md — Operations, pickup, drop-off, queue
- jfk_pricing.md — Pricing, surge, approval

## Important Policy Values

| Airport | Maximum Surge |
|---|---:|
| SFO | 1.5x |
| LAX | 1.4x |
| JFK | 1.6x |

## RAG Usage

These documents will be loaded, cleaned, chunked, embedded, stored in a vector database, retrieved using semantic search, and passed to an LLM as context.
