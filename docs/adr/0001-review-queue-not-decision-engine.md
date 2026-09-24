# ADR 0001: Emit review signals, not automated decisions

## Context

Municipality-year indicators can contain reporting changes, contextual variation, and incomplete coverage. An anomaly score cannot establish fraud, policy quality, or causality.

## Decision

The model emits evidence-bearing review signals and drift checks. It does not rank people, allocate resources, or determine compliance.

## Consequences

The project demonstrates lineage and monitoring without overstating model authority. Users need domain review before any operational conclusion.

## Alternatives considered

An automated classification workflow would create stronger product-like output but would not be defensible with the public fixture and stated analytical boundary.
