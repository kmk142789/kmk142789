# Deploy NVIDIA NIM on GKE with GPUs

This runbook captures the Cloud Shell commands needed to provision a GPU-enabled
Google Kubernetes Engine (GKE) cluster and node pool for NVIDIA NIM workloads.

## Prerequisites

- Google Cloud project with billing enabled.
- IAM permissions to create GKE clusters and manage node pools.
- `gcloud` CLI configured (`gcloud auth login` and `gcloud config set project`).
- Quota for the chosen GPU and machine types in the target region/zone.

## Set deployment parameters

Export the following variables, substituting values for your environment:

```bash
export PROJECT_ID=<YOUR PROJECT ID>
export REGION=<YOUR REGION>
export ZONE=<YOUR ZONE>
export CLUSTER_NAME=nim-demo
export NODE_POOL_MACHINE_TYPE=g2-standard-16
export CLUSTER_MACHINE_TYPE=e2-standard-4
export GPU_TYPE=nvidia-l4
export GPU_COUNT=1
```

> ℹ️ Adjust `NODE_POOL_MACHINE_TYPE`, `CLUSTER_MACHINE_TYPE`, and `GPU_TYPE` to
> align with the GPU family and capacity available in your project.

## Create the control-plane node pool

Provision the base cluster (control-plane and default node pool) with the
non-GPU machine type:

```bash
gcloud container clusters create "${CLUSTER_NAME}" \
  --project="${PROJECT_ID}" \
  --location="${ZONE}" \
  --release-channel=rapid \
  --machine-type="${CLUSTER_MACHINE_TYPE}" \
  --num-nodes=1
```

## Add the GPU node pool

Create a dedicated GPU pool for NVIDIA NIM workloads:

```bash
gcloud container node-pools create gpupool \
  --accelerator type="${GPU_TYPE}",count="${GPU_COUNT}",gpu-driver-version=latest \
  --project="${PROJECT_ID}" \
  --location="${ZONE}" \
  --cluster="${CLUSTER_NAME}" \
  --machine-type="${NODE_POOL_MACHINE_TYPE}" \
  --num-nodes=1
```

After the node pool is ready, deploy the NVIDIA NIM assets for your target model
and run validation tests per the product documentation. When finished, clean up
by deleting the cluster to avoid ongoing charges:

```bash
gcloud container clusters delete "${CLUSTER_NAME}" --project="${PROJECT_ID}" --location="${ZONE}"
```
