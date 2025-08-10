FastAPI automatically generates an OpenAPI document for your app. Quick summary and examples to get, customize and export it.

1) Where it’s served
-  /openapi.json — the OpenAPI document (JSON)
-  /docs — Swagger UI
-  /redoc — ReDoc

Run your app (example):
```bash
uvicorn main:app --reload
# then open http: //127.0.0.1:8000/openapi.json or /docs
```

2) Minimal FastAPI app (auto OpenAPI)
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="My API", version="1.0.0")

class Item(BaseModel):
    id: int
    name: str

@app.get("/items", response_model=list[Item
])
async def list_items():
    return [
    {
        "id": 1,
        "name": "Apple"
    }
]
```
Open http: //127.0.0.1:8000/openapi.json to fetch the spec.
3) Programmatically get and save the OpenAPI JSON
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import json

app = FastAPI()

# ... define routes ...

def save_openapi(path: str = "openapi.json"):
    spec = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    with open(path,
"w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

# call save_openapi() after app is defined (e.g., in a build/CI step)
```

4) Customize the generated OpenAPI (add servers, security, extra info)
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.2.0",
        description="My API description",
        routes=app.routes,
    )
    # add servers or securitySchemes
    openapi_schema[
    "servers"
] = [
    {
        "url": "https://api.example.com/v1"
    }
]
    openapi_schema[
    "components"
][
    "securitySchemes"
] = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}
    openapi_schema[
    "security"
] = [
    {
        "bearerAuth": []
    }
]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```
After this, /openapi.json will reflect your customizations.

5) Fetch the OpenAPI over HTTP (example)
```bash
curl -s http: //127.0.0.1:8000/openapi.json -o openapi.json
```

6) Validate / lint in CI
-  Validate JSON: pip install openapi-spec-validator
```bash
python -c "from openapi_spec_validator import validate_spec; import json; print(validate_spec(json.load(open('openapi.json'))))"
```
-  Lint with Spectral (recommended): npm i -g @stoplight/spectral
```bash
spectral lint openapi.json
```

7) CI snippet (example, GitHub Actions step)
```yaml
-  name: Install deps
  run: pip install -r requirements.txt openapi-spec-validator
-  name: Generate OpenAPI
  run: python -c "from main import save_openapi; save_openapi('openapi.json')"
-  name: Validate OpenAPI
  run: python -c "from openapi_spec_validator import validate_spec; import json; validate_spec(json.load(open('openapi.json')))"
```

Notes
-  FastAPI uses your route signatures and Pydantic models to build the spec (include response_model, status_code, descriptions, examples).
-  If you want a YAML file, convert JSON with tools like `yq` or Python (PyYAML).
-  For design-first workflows, you can still use Connexion or generate FastAPI routes from an existing OpenAPI, but FastAPI is optimized for code-first.

If you want, tell me whether you want:
-  a ready-to-run example that saves openapi.json at build time, or
-  a customized OpenAPI (examples, tags, multiple servers, OAuth2 flows) — I’ll provide the exact code.