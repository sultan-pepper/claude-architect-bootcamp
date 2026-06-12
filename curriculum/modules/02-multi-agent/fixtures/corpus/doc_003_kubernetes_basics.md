# Kubernetes Orchestration Basics

Kubernetes is an open-source platform for automating container deployment, scaling, and operations. It abstracts the underlying infrastructure and provides a declarative API.

## Core Concepts

- **Pods**: Smallest deployable units, typically containing one container
- **Nodes**: Worker machines running pods
- **Clusters**: Sets of nodes managed by Kubernetes
- **Services**: Abstractions defining logical sets of pods and policies for access
- **Deployments**: Declarative updates for pods and replicas

## Self-Healing

Kubernetes automatically restarts failed containers, replaces and reschedules pods when nodes fail, and kills containers that don't respond to health checks.

## Declarative Configuration

Instead of imperative commands, Kubernetes uses YAML manifests to describe desired state. Controllers continuously work to match current state to desired state.
