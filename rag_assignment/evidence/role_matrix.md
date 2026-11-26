# Exercise D - role-by-role retrieval results

Top-5 chunks per identity, strategy `structure_recursive`, cosine distance (`<=>`, lower is closer).
`Authorized?` is recomputed outside the database from users.json + document ACLs.

## How does a Kubernetes Deployment manage application replicas?

Primary area: **application_engineering** - expected best document `APP-deployment`. Unfiltered (admin-only) top-5: APP-deployment, APP-deployment, APP-horizontal-pod-autoscale, APP-deployment, APP-replicaset

| Identity | Rank | Document | Chunk / heading | Cosine distance | Authorized? | Source |
|---|---|---|---|---|---|---|
| priya | 1 | `APP-deployment` | 0 / Deployments | 0.1726 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| priya | 2 | `APP-deployment` | 56 / Deployments > Writing a Deployment Spec > Replicas | 0.1764 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| priya | 3 | `APP-horizontal-pod-autoscale` | 16 / Horizontal Pod Autoscaling > Autoscaling during rolling update | 0.2038 | yes | [Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) |
| priya | 4 | `APP-deployment` | 22 / Deployments > Rolling Back a Deployment | 0.2060 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| priya | 5 | `APP-replicaset` | 21 / ReplicaSet > Alternatives to ReplicaSet > Deployment (recommended) | 0.2071 | yes | [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/) |
| arjun | 1 | `SHR-working-with-objects` | 3 / Objects In Kubernetes > Understanding Kubernetes objects > Object spec and status | 0.2164 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| arjun | 2 | `SHR-overview` | 9 / Overview > Historical context for Kubernetes | 0.2265 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 3 | `SHR-overview` | 3 / Overview > Why you need Kubernetes and what it can do | 0.2274 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2348 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 5 | `SHR-overview` | 1 / Overview > Why you need Kubernetes and what it can do | 0.2525 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 1 | `SHR-working-with-objects` | 3 / Objects In Kubernetes > Understanding Kubernetes objects > Object spec and status | 0.2164 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| meena | 2 | `SHR-overview` | 9 / Overview > Historical context for Kubernetes | 0.2265 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 3 | `SHR-overview` | 3 / Overview > Why you need Kubernetes and what it can do | 0.2274 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2348 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 5 | `SHR-overview` | 1 / Overview > Why you need Kubernetes and what it can do | 0.2525 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| divya | 1 | `APP-deployment` | 0 / Deployments | 0.1726 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| divya | 2 | `APP-deployment` | 56 / Deployments > Writing a Deployment Spec > Replicas | 0.1764 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| divya | 3 | `APP-horizontal-pod-autoscale` | 16 / Horizontal Pod Autoscaling > Autoscaling during rolling update | 0.2038 | yes | [Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) |
| divya | 4 | `APP-deployment` | 22 / Deployments > Rolling Back a Deployment | 0.2060 | yes | [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| divya | 5 | `APP-replicaset` | 21 / ReplicaSet > Alternatives to ReplicaSet > Deployment (recommended) | 0.2071 | yes | [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/) |
| mallory | - | *no authorized chunks* | - | - | n/a | - |

## What are PersistentVolumes and PersistentVolumeClaims?

Primary area: **platform_engineering** - expected best document `PLAT-persistent-volumes`. Unfiltered (admin-only) top-5: PLAT-persistent-volumes, PLAT-persistent-volumes, PLAT-persistent-volumes, PLAT-persistent-volumes, APP-statefulset

| Identity | Rank | Document | Chunk / heading | Cosine distance | Authorized? | Source |
|---|---|---|---|---|---|---|
| priya | 1 | `APP-statefulset` | 12 / StatefulSets > Pod Identity > Stable Storage | 0.1893 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| priya | 2 | `APP-statefulset` | 4 / StatefulSets > Components > Volume Claim Templates | 0.2194 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| priya | 3 | `APP-statefulset` | 29 / StatefulSets > PersistentVolumeClaim retention | 0.2297 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| priya | 4 | `APP-statefulset` | 30 / StatefulSets > PersistentVolumeClaim retention | 0.2390 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| priya | 5 | `APP-statefulset` | 32 / StatefulSets > PersistentVolumeClaim retention | 0.2734 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| arjun | 1 | `PLAT-persistent-volumes` | 2 / Persistent Volumes > Introduction | 0.1563 | yes | [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) |
| arjun | 2 | `PLAT-persistent-volumes` | 42 / Persistent Volumes > PersistentVolumeClaims | 0.1718 | yes | [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) |
| arjun | 3 | `PLAT-persistent-volumes` | 1 / Persistent Volumes > Introduction | 0.1753 | yes | [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) |
| arjun | 4 | `PLAT-persistent-volumes` | 18 / Persistent Volumes > Lifecycle of a volume and claim > Reserving a PersistentVolume | 0.1889 | yes | [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) |
| arjun | 5 | `PLAT-volume-snapshots` | 8 / Volume Snapshots > Lifecycle of a volume snapshot and volume snapshot content > Persistent Volume Claim as Snapshot Source Protection | 0.1919 | yes | [Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/) |
| meena | 1 | `SEC-rbac-good-practices` | 10 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks > Persistent volume creation | 0.2579 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| meena | 2 | `SHR-kubernetes-api` | 14 / The Kubernetes API > Persistence | 0.2846 | yes | [The Kubernetes API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/) |
| meena | 3 | `SEC-security-checklist` | 15 / Security Checklist > Secrets | 0.3547 | yes | [Security Checklist](https://kubernetes.io/docs/concepts/security/security-checklist/) |
| meena | 4 | `SEC-rbac-good-practices` | 5 / Role Based Access Control Good Practices > General good practice > Periodic review | 0.3842 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| meena | 5 | `SHR-overview` | 9 / Overview > Historical context for Kubernetes | 0.3860 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| divya | 1 | `APP-statefulset` | 12 / StatefulSets > Pod Identity > Stable Storage | 0.1893 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| divya | 2 | `APP-statefulset` | 4 / StatefulSets > Components > Volume Claim Templates | 0.2194 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| divya | 3 | `APP-statefulset` | 29 / StatefulSets > PersistentVolumeClaim retention | 0.2297 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| divya | 4 | `APP-statefulset` | 30 / StatefulSets > PersistentVolumeClaim retention | 0.2390 | yes | [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) |
| divya | 5 | `SEC-rbac-good-practices` | 10 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks > Persistent volume creation | 0.2579 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| mallory | - | *no authorized chunks* | - | - | n/a | - |

## What are recommended Kubernetes RBAC practices?

Primary area: **security_engineering** - expected best document `SEC-rbac-good-practices`. Unfiltered (admin-only) top-5: SEC-rbac-good-practices, SEC-secrets-good-practices, SEC-rbac-good-practices, SEC-rbac-good-practices, SEC-rbac-good-practices

| Identity | Rank | Document | Chunk / heading | Cosine distance | Authorized? | Source |
|---|---|---|---|---|---|---|
| priya | 1 | `SHR-overview` | 11 / Overview > What's next | 0.2540 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 2 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2622 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 3 | `SHR-overview` | 9 / Overview > Historical context for Kubernetes | 0.2736 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 4 | `SHR-overview` | 1 / Overview > Why you need Kubernetes and what it can do | 0.2768 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 5 | `SHR-overview` | 3 / Overview > Why you need Kubernetes and what it can do | 0.2774 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 1 | `SHR-overview` | 11 / Overview > What's next | 0.2540 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 2 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2622 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 3 | `SHR-overview` | 9 / Overview > Historical context for Kubernetes | 0.2736 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 4 | `SHR-overview` | 1 / Overview > Why you need Kubernetes and what it can do | 0.2768 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 5 | `SHR-overview` | 3 / Overview > Why you need Kubernetes and what it can do | 0.2774 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 1 | `SEC-rbac-good-practices` | 0 / Role Based Access Control Good Practices | 0.1772 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| meena | 2 | `SEC-secrets-good-practices` | 2 / Good practices for Kubernetes Secrets > Cluster administrators > Configure least-privilege access to Secrets | 0.2246 | yes | [Good practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) |
| meena | 3 | `SEC-rbac-good-practices` | 6 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks | 0.2354 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| meena | 4 | `SEC-rbac-good-practices` | 16 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks > Token request | 0.2371 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| meena | 5 | `SEC-rbac-good-practices` | 5 / Role Based Access Control Good Practices > General good practice > Periodic review | 0.2405 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| divya | 1 | `SEC-rbac-good-practices` | 0 / Role Based Access Control Good Practices | 0.1772 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| divya | 2 | `SEC-secrets-good-practices` | 2 / Good practices for Kubernetes Secrets > Cluster administrators > Configure least-privilege access to Secrets | 0.2246 | yes | [Good practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) |
| divya | 3 | `SEC-rbac-good-practices` | 6 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks | 0.2354 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| divya | 4 | `SEC-rbac-good-practices` | 16 / Role Based Access Control Good Practices > Kubernetes RBAC - privilege escalation risks > Token request | 0.2371 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| divya | 5 | `SEC-rbac-good-practices` | 5 / Role Based Access Control Good Practices > General good practice > Periodic review | 0.2405 | yes | [Role Based Access Control Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) |
| mallory | - | *no authorized chunks* | - | - | n/a | - |

## What are the main Kubernetes components?

Primary area: **shared** - expected best document `SHR-components`. Unfiltered (admin-only) top-5: SHR-components, SHR-overview, SHR-components, SHR-overview, SHR-working-with-objects

| Identity | Rank | Document | Chunk / heading | Cosine distance | Authorized? | Source |
|---|---|---|---|---|---|---|
| priya | 1 | `SHR-components` | 0 / Kubernetes Components > Core Components | 0.1381 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| priya | 2 | `SHR-overview` | 11 / Overview > What's next | 0.1534 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 3 | `SHR-components` | 1 / Kubernetes Components > Core Components > Control Plane Components | 0.2108 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| priya | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2114 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| priya | 5 | `SHR-working-with-objects` | 8 / Objects In Kubernetes > What's next | 0.2129 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| arjun | 1 | `SHR-components` | 0 / Kubernetes Components > Core Components | 0.1381 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| arjun | 2 | `SHR-overview` | 11 / Overview > What's next | 0.1534 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 3 | `SHR-components` | 1 / Kubernetes Components > Core Components > Control Plane Components | 0.2108 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| arjun | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2114 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| arjun | 5 | `SHR-working-with-objects` | 8 / Objects In Kubernetes > What's next | 0.2129 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| meena | 1 | `SHR-components` | 0 / Kubernetes Components > Core Components | 0.1381 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| meena | 2 | `SHR-overview` | 11 / Overview > What's next | 0.1534 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 3 | `SHR-components` | 1 / Kubernetes Components > Core Components > Control Plane Components | 0.2108 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| meena | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2114 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| meena | 5 | `SHR-working-with-objects` | 8 / Objects In Kubernetes > What's next | 0.2129 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| divya | 1 | `SHR-components` | 0 / Kubernetes Components > Core Components | 0.1381 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| divya | 2 | `SHR-overview` | 11 / Overview > What's next | 0.1534 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| divya | 3 | `SHR-components` | 1 / Kubernetes Components > Core Components > Control Plane Components | 0.2108 | yes | [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/) |
| divya | 4 | `SHR-overview` | 2 / Overview > Why you need Kubernetes and what it can do | 0.2114 | yes | [Overview](https://kubernetes.io/docs/concepts/overview/) |
| divya | 5 | `SHR-working-with-objects` | 8 / Objects In Kubernetes > What's next | 0.2129 | yes | [Objects In Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/) |
| mallory | - | *no authorized chunks* | - | - | n/a | - |

## Summary

Unauthorized chunks returned across all runs: **0**

