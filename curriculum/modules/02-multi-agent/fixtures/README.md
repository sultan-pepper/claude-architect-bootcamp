# M2 Fixtures Documentation

## Research Corpus

A collection of ~12 markdown documents covering one broad topic ("Containerization and Orchestration") spanning 6 distinct sub-domains.

### Structure

```
corpus/
├── doc_001_containers_basics.md
├── doc_002_docker_images.md
├── doc_003_kubernetes_basics.md
├── doc_004_k8s_deployments.md
├── doc_005_container_networking.md
├── doc_006_k8s_ingress.md
├── doc_007_container_storage.md
├── doc_008_container_security.md
├── doc_009_container_monitoring.md
├── doc_010_k8s_config_management.md
├── doc_011_k8s_resource_management.md
├── doc_012_multi_container_patterns.md
└── corpus_index.json
```

### corpus_index.json

Maps each document to its sub-domain for breadth validation.

**Schema:**
```json
{
  "topic": "Containerization and Orchestration",
  "documents": [
    {
      "id": "doc_001",
      "filename": "...",
      "title": "...",
      "subdomain": "..."
    }
  ],
  "subdomains": ["Containers", "Orchestration", "Networking", "Storage", "Security", "Operations"]
}
```

### Document Coverage

**Sub-domains:** 6 distinct areas
1. **Containers** (Docker basics, images, registries) — docs 001, 002
2. **Orchestration** (Kubernetes, deployments, scaling) — docs 003, 004, 012
3. **Networking** (container networking, ingress, services) — docs 005, 006
4. **Storage** (persistent volumes, storage classes) — doc 007
5. **Security** (image scanning, runtime security, access control) — doc 008
6. **Operations** (monitoring, logging, config management, resource limits) — docs 009, 010, 011

Each document is ~300-500 words covering specific technical aspects.

---

## Testing Notes

- Documents are plain markdown with no special formatting requirements.
- Breadth check: corpus must cover ≥4 sub-domains (this corpus has 6).
- Index provides ground truth for sub-domain classification.
