# Expanded Program Specification

*(with design rationale and concrete examples)*

---

## 1. High-level objective

Create a **single codebase + one build pipeline** that lets any small Python “component” (function `predict(payload)`) be deployed **unchanged** to multiple Azure runtimes:

| Runtime                                            | Examples of use-case             |
| -------------------------------------------------- | -------------------------------- |
| **Azure ML Managed Online Endpoint**               | real-time inference, autoscaling |
| **Azure ML Managed Batch Endpoint / Parallel job** | asynchronous bulk scoring        |
| **Azure Functions**                                | serverless HTTP trigger          |
| **Azure Container Apps / App Service / AKS**       | REST micro-service               |
| **MCP action server**                              | agent orchestration              |

…and let a **single YAML manifest** decide *which* component goes to *which* runtime, in *which* subscription / resource-group, with optional per-deployment overrides. One `make deploy` (or GitHub-Actions job) should build once, then fan-out deployments.

---

## 2. Design principles & why each decision was taken

| Principle                       | What we did                                                                                   | Why                                                                        |
| ------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **DRY (Don’t Repeat Yourself)** | 1 copy of adapters, 1 Dockerfile, 1 template per service                                      | avoids version drift, reduces bugs, slashes code reviews                   |
| **Single source of truth**      | `deploy/manifest.yaml` holds *all* environment mappings                                       | deployments are reproducible; auditors & SREs look in one place            |
| **Stateless containers**        | each component is pure function; selection via `$HANDLER`                                     | every Azure host can autoscale horizontally without extra code             |
| **Code vs. Infra separation**   | *Logic* stays with the component; *infra* is generated from templates                         | component can be unit-tested/registered once; infra flexes per environment |
| **Image immutability**          | one container tag per commit (e.g. Git SHA)                                                   | the *identical* bits run in dev, test, prod; easy rollback                 |
| **Simple local dev**            | `docker run -e HANDLER="components.wordcount:predict"`                                        | no need to mimic each Azure runtime; on-board new dev in minutes           |
| **CLI-driven overrides**        | Use `az ml … --set` and env-vars for last-mile config                                         | lets the script patch only the fields that differ ([Microsoft Learn][1])   |
| **Extensibility**               | new runtime = add one adapter & template; new component = add one file & one line in manifest | scaling the platform team’s workload stays O(1)                            |

---

## 3. Repository layout (with justification)

```
repo/
│
├─ components/                   #   OWN THE “WHAT”
│   ├─ wordcount/
│   │   ├─ wordcount.py          # domain logic
│   │   └─ component.yml         # (opt) AML command spec—lives with code
│   └─ …
│
├─ runtime/                      #   OWN THE “HOW”
│   ├─ dispatcher.py             # picks component via $HANDLER (rationale § 4)
│   ├─ azureml_adapter.py        # ONE file handles both AML-online & batch
│   ├─ function_app/__init__.py  # Functions adapter
│   └─ rest.py                   # FastAPI entrypoint
│
├─ Dockerfile                    # immutable artefact, identical everywhere
├─ requirements.txt
│
├─ deploy/                       #   OWN THE “WHERE”
│   ├─ templates/                # infra snippets with token placeholders
│   │   ├─ aml-online.yml
│   │   ├─ aml-batch.yml
│   │   ├─ pipeline.yml
│   │   └─ containerapp.bicep
│   ├─ manifest.yaml             # ← ONLY FILE ops team touches per release
│   └─ run.py                    # 100-line Python orchestrator
│
└─ Makefile                      # 1-click entry point (CI calls same)
```

### Why split this way?

*Everything that changes rarely (adapters, Dockerfile) lives once.
Everything that changes often (which component goes where) lives in the manifest.*
Thus day-2 operations = editing one YAML file rather than copying folders.

---

## 4. Runtime / dispatcher pattern

```python
# runtime/dispatcher.py
import importlib, os, typing as T

_target = os.getenv("HANDLER", "components.wordcount:predict")
_mod, _fn = _target.split(":")
predict_fn = getattr(importlib.import_module(_mod), _fn)

def predict(payload: T.Union[str, dict, list]) -> T.Union[dict, list]:
    if isinstance(payload, list):
        return [predict_fn(p) for p in payload]
    return predict_fn(payload)
```

**Why?**

* **Env-var indirection** lets *one* container image host unlimited components; runtime selection costs 1 string lookup.
* Works uniformly in AML (`environment_variables`), Functions (`az functionapp config appsettings set`) ([Microsoft Learn][2]), Container Apps (`--env-vars`) ([Microsoft Learn][3]).
* Keeps adapters 5-10 lines each:

```python
# runtime/azureml_adapter.py  (online & batch)
from runtime.dispatcher import predict
def init(): pass
def run(data):                 # online → dict/bytes ;  batch → list
    return predict(data)
```

---

## 5. Templates and CLI overrides

### Example `deploy/templates/aml-online.yml`

```yaml
$schema: https://azuremlschemas.azureedge.net/latest/managedOnlineDeployment.schema.json
name: ${{DEPLOY_NAME}}
endpoint_name: ${{ENDPOINT}}
model: { image: ${{IMAGE_URI}} }
environment_variables:
  HANDLER: "${{HANDLER}}"
instance_type: ${{INSTANCE_TYPE}}
instance_count: ${{INSTANCE_COUNT}}
```

*Tokens* (`${{…}}`) get **patched at deploy time** with `az ml online-deployment create … --set field=value`.
The Azure ML CLI explicitly supports per-property overrides ([Microsoft Learn][1]).
This avoids N × Y copies of YAML for N components × Y environments.

---

## 6. The manifest (single source of truth)

```yaml
acr: myacr.azurecr.io
imageName: ml-components

groups:
  dev-euw:
    subscription: sub-GUID-01
    resourceGroup: rg-ml-dev
    region: westeurope
    deployments:
      - component: wordcount
        services: [aml_online, function]
        overrides: { instance_type: Standard_DS3_v2 }
      - component: sentiment
        services: [containerapp]

  prod-uk:
    subscription: sub-GUID-02
    resourceGroup: rg-ml-prod
    region: uksouth
    deployments:
      - component: wordcount
        services: [aml_online, aml_batch]
      - component: sentiment
        services: [aml_online, containerapp, function]
```

**Why manifest?**

* Non-dev stakeholders (SRE, ops) edit deployments without touching code.
* Acts as change log / audit-trail in Git.
* Script can `az account set` per group and iterate.
* Overrides (SKU, replica count, schedule) live next to the entry that needs them—no hunting.

---

## 7. Orchestrator (`deploy/run.py`)

Key responsibilities (≈ 100 LOC):

1. **Load manifest** and build a matrix of *(group, component, service)*.
2. **Switch subscription** → `az account set --subscription …`.
3. **Register component** (if using AML *component.yml*) once per workspace.
4. **Render template** → simple `str.replace`; write temp file.
5. **Execute CLI** for each runtime:

   * `az ml online-endpoint / online-deployment …` (online)
   * `az ml batch-deployment …` (batch)
   * `az functionapp config appsettings set … HANDLER=…` (Functions) ([Microsoft Learn][2])
   * `az containerapp update --image … --env-vars HANDLER=…` (Container Apps) ([Microsoft Learn][3])

Because the container is stateless, redeploying is safe and idempotent.

---

## 8. Build pipeline & local workflow

### Makefile (excerpt)

```make
ACR  := $(shell yq '.acr' deploy/manifest.yaml)
IMG  := $(shell yq '.imageName' deploy/manifest.yaml)
TAG  := $(shell git rev-parse --short HEAD)
FULL := $(ACR)/$(IMG):$(TAG)

deploy: build push
	python deploy/run.py --manifest deploy/manifest.yaml --image $(FULL)

build:
	docker build -t $(FULL) .
push:
	docker push $(FULL)
```

* **CI/CD** (GitHub Actions, Azure DevOps) invokes `make deploy`; same command works on a laptop.
* **Single Docker build** → cached once, pushed once, used everywhere.

---

## 9. Component defaults vs. environment overrides

If a component needs sensible defaults:

```yaml
# components/wordcount/defaults.yml
instance_type: Standard_DS3_v2
instance_count: 1
```

`deploy/run.py` reads the file, then layers manifest `overrides:` on top—manifest always wins. This prevents bloating the manifest while keeping non-prod deploys simple.

---

## 10. Operational & scaling considerations

* **Autoscaling** handled natively:

  * AML endpoints scale by concurrency or CPU/Memory signals ([Microsoft Learn][4])
  * Container Apps uses KEDA for scale-to-zero.
  * Functions uses consumption plan or Premium burst.
    No code change needed because containers are stateless.

* **Observability** – all runtimes expose stdout/stderr; keep unified logging format (e.g. JSON lines).

* **Security** – secrets use each service’s env-var mechanism (Key Vault references in Container Apps, App Settings for Functions, AML key vault-backed secrets). No secret appears in git.

* **Rollback** – tag images by commit; redeploy previous tag by editing manifest, running `make deploy`.

---

## 11. Trade-offs & mitigations

| Trade-off                                               | Impact                             | Mitigation                                                                                        |
| ------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------- |
| One image may carry unused dependencies                 | Slightly larger image              | Prune requirements; use multi-stage build if size critical                                        |
| Push to many RGs from one script increases blast-radius | Wrong manifest edit can touch prod | Protect prod groups via `az role assignment` or separate pipeline that reads only selected groups |
| Orchestrator is home-grown                              | Needs tests                        | Script is <150 LOC; add unit tests & dry-run flag                                                 |

---

## 12. End-to-end example (wordcount)

### Component code

```python
# components/wordcount/wordcount.py
def predict(payload):
    txt = payload["text"] if isinstance(payload, dict) else str(payload)
    return {"word_count": len(txt.split())}
```

### Manifest excerpt

```yaml
deployments:
  - component: wordcount
    services: [aml_online, function]
```

### Deploy

```bash
make deploy          # builds img acr.io/ml-components:<gitSHA>; deploys
```

Result:

* AML Endpoint **wordcount-ep** with handler `components.wordcount:predict` is live.
* Azure Function **fx-wordcount** container pulls the *same* image; `HANDLER` app-setting injected.

---

## 13. Reference docs

* Azure ML managed online-deployment YAML schema & CLI `--set` examples ([Microsoft Learn][1])
* Online endpoint concepts & autoscaling ([Microsoft Learn][4])
* CLI for Function App app-settings (`az functionapp config appsettings set`) ([Microsoft Learn][2])
* Env-vars in Container Apps (`--env-vars` or YAML) ([Microsoft Learn][3])
* Pipeline job YAML schema (token-friendly) ([Microsoft Learn][5])

---

### Summary

*The architecture maximises reuse (one image, one adapter copy), puts every environment decision into a **single manifest**, and leverages Azure CLI token overrides so no YAML is duplicated. Development stays simple; operations change just one file; scaling and hosting nuances are absorbed by each Azure service—without touching component code.*

[1]: https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-deployment-managed-online?view=azureml-api-2&utm_source=chatgpt.com "CLI (v2) managed online deployment YAML schema - Learn Microsoft"
[2]: https://learn.microsoft.com/en-us/cli/azure/functionapp/config/appsettings?view=azure-cli-latest&utm_source=chatgpt.com "az functionapp config appsettings - Learn Microsoft"
[3]: https://learn.microsoft.com/en-us/azure/container-apps/environment-variables?utm_source=chatgpt.com "Manage environment variables on Azure Container Apps"
[4]: https://learn.microsoft.com/en-us/azure/machine-learning/how-to-deploy-online-endpoints?view=azureml-api-2&utm_source=chatgpt.com "Deploy Machine Learning Models to Online Endpoints - Azure ..."
[5]: https://learn.microsoft.com/en-us/azure/machine-learning/reference-yaml-job-pipeline?view=azureml-api-2&utm_source=chatgpt.com "CLI (v2) pipeline job YAML schema - Azure Machine Learning"
