---
name: llt-web-tests
description: Specialized guidance for working with WebTests (LLTs for web runtime environments)
user-invocable: false
---

# LLT: WebTests Framework

**Purpose:** Specialized guidance for working with WebTests (LLTs for web runtime environments).

## Framework Overview

WebTests are LowLevelTests that execute in a web runtime environment using a webrunner. They test web-specific functionality and browser integrations.

### Key Differences from Standard LLTs

- **Runtime**: Webrunner instead of native executable
- **Startup**: Special initialization for web environment
- **Platforms**: Web-specific targets (WebAssembly, WebGL)

### Startup Sequence

WebTests require webrunner initialization before test execution:

```bash
# Start webrunner
webrunner --port 8080 --test-mode

# Run WebTests through webrunner
python3 llt_run.py \
  --test-target WebTests \
  --platform Web \
  --webrunner-url http://localhost:8080
```

### Integration with llt-find

WebTests are discovered like standard LLTs but have web-specific metadata:

```json
{
  "test_target": "WebTests",
  "platforms": ["Web"],
  "requires_webrunner": true,
  "webrunner_config": {
    "port": 8080,
    "mode": "test"
  }
}
```

### References

- **Source**: `Engine/Source/Programs/LowLevelTests/WebTests/`
- **Webrunner**: `Engine/Binaries/WebRunner/`
