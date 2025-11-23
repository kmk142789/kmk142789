# Deploy an NVIDIA NIM LLM on GKE

This guide captures the steps for deploying an NVIDIA NIM Large Language Model (LLM) on a GPU-enabled Google Kubernetes Engine (GKE) cluster, based on the Google Codelab workflow. Adjust chart versions and image tags as new releases are published.

## Prerequisites

- A GKE cluster with NVIDIA GPUs and `kubectl` access configured
- `helm` installed locally
- An NVIDIA NGC API key exported as `NGC_CLI_API_KEY`

## 1. Fetch the NIM LLM Helm chart

```bash
helm fetch https://helm.ngc.nvidia.com/nim/charts/nim-llm-1.3.0.tgz \
  --username='$oauthtoken' \
  --password="$NGC_CLI_API_KEY"
```

## 2. Create a namespace

```bash
kubectl create namespace nim
```

## 3. Configure secrets

Create the image-pull secret for `nvcr.io` and provide the NGC API key to the chart:

```bash
kubectl create secret docker-registry registry-secret \
  --docker-server=nvcr.io \
  --docker-username='$oauthtoken' \
  --docker-password="$NGC_CLI_API_KEY" \
  -n nim

kubectl create secret generic ngc-api \
  --from-literal=NGC_API_KEY="$NGC_CLI_API_KEY" \
  -n nim
```

## 4. Define custom values

Create `nim_custom_value.yaml` to pin the image and model configuration. Update the `tag` to the NIM release you intend to run.

```bash
cat <<'EOF_VALUES' > nim_custom_value.yaml
image:
  repository: "nvcr.io/nim/meta/llama3-8b-instruct"
  tag: 1.0.0
model:
  ngcAPISecret: ngc-api
persistence:
  enabled: true
imagePullSecrets:
  - name: registry-secret
EOF_VALUES
```

## 5. Install the chart

```bash
helm install my-nim nim-llm-1.3.0.tgz \
  -f nim_custom_value.yaml \
  --namespace nim
```

## 6. Verify the deployment

```bash
kubectl get pods -n nim
```

## 7. Port-forward for local testing

```bash
kubectl port-forward service/my-nim-nim-llm 8000:8000 -n nim
```

## 8. Send a test chat completion

Open a new terminal and invoke the NIM service:

```bash
curl -X 'POST' \
  'http://localhost:8000/v1/chat/completions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "messages": [
    {
      "content": "You are a polite and respectful chatbot helping people plan a vacation.",
      "role": "system"
    },
    {
      "content": "What should I do for a 4 day vacation in Spain?",
      "role": "user"
    }
  ],
  "model": "meta/llama3-8b-instruct",
  "max_tokens": 128,
  "top_p": 1,
  "n": 1,
  "stream": false,
  "stop": "\n",
  "frequency_penalty": 0.0
}'
```

A valid chat completion response confirms that the NIM deployment is serving traffic.
