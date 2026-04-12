# Naming Convention Skill

## Purpose

This skill documents the naming convention rules used by the RPC Scaffold System to derive all identifiers from a canonical RPC name. It covers the DeriveIdentifiers algorithm, default naming formulas, optional parameter syntax, and HTTP verb inference rules. All agents and services reference this document when generating identifiers for any RPC layer.

## DeriveIdentifiers Algorithm

The DeriveIdentifiers function is the central naming derivation used throughout the system. It takes a raw RPC name and a set of naming conventions, and produces all required identifiers for the four code layers.

### Step 1: Normalize the RPC Name (REQ-F-17)

Strip known prefixes and suffixes that are part of the naming convention, not the canonical name.

```
Input: rawRpcName (string)
Output: canonicalName (string)

1. canonicalName = rawRpcName

2. If canonicalName starts with "Http":
     canonicalName = canonicalName.removePrefix("Http")
     Emit warning: "Stripped 'Http' prefix from RPC name"

3. If canonicalName ends with "Command":
     canonicalName = canonicalName.removeSuffix("Command")
     Emit warning: "Stripped 'Command' suffix from RPC name"

Example transformations:
  "HttpLoginUserCommand" -> "LoginUser"
  "HttpGetPlayerStatus"  -> "GetPlayerStatus"
  "ValidateSession"      -> "ValidateSession" (no change)
  "LoginUserCommand"     -> "LoginUser"
```

### Step 2: Apply Naming Rules

Using the canonicalName and the project's naming conventions, derive all identifiers.

```
Input: canonicalName (string), conventions (NamingConventions)
Output: identifiers (IdentifierMap)

identifiers = {
  cpp_handler:    conventions.cpp_handler_prefix + canonicalName + conventions.cpp_handler_suffix,
  http_path:      "/" + lowercase(canonicalName),
  csharp_wrapper: canonicalName,
  csharp_dto:     canonicalName + conventions.csharp_dto_suffix,
  test_case:      conventions.csharp_test_prefix + canonicalName + conventions.csharp_test_suffix,
}
```

### Step 3: Apply Project-Specific Overrides

If the project configuration defines naming overrides, apply them after the default rules.

```
Input: identifiers (IdentifierMap), conventions (NamingConventions), canonicalName (string)
Output: identifiers (IdentifierMap) with overrides applied

For each override in conventions.overrides:
  If override.applies_to matches canonicalName (glob pattern):
    identifiers[override.target] = override.transform(canonicalName)

Return identifiers
```

## Default Naming Formulas (REQ-F-16)

These are the default naming conventions. Projects can override any of these via config.yaml.

### C++ Handler Name

```
Formula: "Http" + PascalCase(RpcName) + "Command"
Example: RpcName = "ValidateSession"
Result:  "HttpValidateSessionCommand"
```

The handler name is used for:
- Method declaration in the `.h` file
- Method implementation in the `.cpp` file
- Lambda delegation in the registration block

### HTTP Path

```
Formula: "/" + lowercase(RpcName)
Example: RpcName = "ValidateSession"
Result:  "/validatesession"
```

The HTTP path is used in the `FHttpPath()` parameter of `RegisterHttpCallback()`.

### C# Wrapper Method Name

```
Formula: PascalCase(RpcName)
Example: RpcName = "ValidateSession"
Result:  "ValidateSession"
```

The wrapper method name is used for the `public static` method in the RPC library class.

### C# Response DTO Class Name

```
Formula: RpcName + "Response"
Example: RpcName = "ValidateSession"
Result:  "ValidateSessionResponse"
```

The response DTO name is used only when `response_type` is `structured`. It defines the C# class that deserializes the custom JSON response from the C++ handler.

### C# Test Case Class Name

```
Formula: "Test" + RpcName + "TestCase"
Example: RpcName = "ValidateSession"
Result:  "TestValidateSessionTestCase"
```

The test case class name is used for the Gauntlet test case file and the class definition.

## Complete Example

Given RPC name `"HttpGetPlayerStatusCommand"` with default conventions:

| Step | Operation | Result |
|------|-----------|--------|
| Normalize | Strip `Http` prefix | `GetPlayerStatusCommand` |
| Normalize | Strip `Command` suffix | `GetPlayerStatus` |
| cpp_handler | `Http` + `GetPlayerStatus` + `Command` | `HttpGetPlayerStatusCommand` |
| http_path | `/` + `getplayerstatus` | `/getplayerstatus` |
| csharp_wrapper | `GetPlayerStatus` | `GetPlayerStatus` |
| csharp_dto | `GetPlayerStatus` + `Response` | `GetPlayerStatusResponse` |
| test_case | `Test` + `GetPlayerStatus` + `TestCase` | `TestGetPlayerStatusTestCase` |

## Optional Parameter Syntax (REQ-F-1)

Parameters in the RPC specification use the format `name:type` for required parameters and `name:type=default` for optional parameters.

### Syntax Format

```
required_parameter := name ":" type
optional_parameter := name ":" type "=" default_value

name          := identifier (camelCase, no spaces)
type          := "string" | "int" | "float" | "bool" | "string[]" | "int[]" | "float[]" | "bool[]" | "object[]" | "object"
default_value := literal value appropriate for the type
```

### Parsing Rules

```
Input: parameterSpec (string, e.g., "retryCount:int=3")
Output: Parameter object

1. Split on ":" to get [name, typeAndDefault]
2. If typeAndDefault contains "=":
     Split on first "=" to get [type, defaultValue]
     Parameter.optional = true
     Parameter.default_value = defaultValue
3. Else:
     Parameter.type = typeAndDefault
     Parameter.optional = false
     Parameter.default_value = null

4. Return Parameter { name, type, optional, default_value }
```

### Examples

| Input | Name | Type | Optional | Default |
|-------|------|------|----------|---------|
| `sessionId:string` | sessionId | string | false | - |
| `retryCount:int=3` | retryCount | int | true | 3 |
| `verbose:bool=false` | verbose | bool | true | false |
| `tags:string[]` | tags | string[] | false | - |
| `timeout:float=30.0` | timeout | float | true | 30.0 |

### Code Generation for Optional Parameters

**C++ (optional parameter with default):**

```cpp
// Required parameter - extract directly
FString SessionId = JsonRequest->GetStringField(TEXT("sessionId"));

// Optional parameter with default - check existence first
int32 RetryCount = 3; // default value
if (JsonRequest->HasField(TEXT("retryCount")))
{
    RetryCount = JsonRequest->GetIntegerField(TEXT("retryCount"));
}
```

**C# (optional parameter with default):**

```csharp
public static bool ValidateSession(RpcTarget InTarget, string SessionId, int RetryCount = 3)
{
    var RequestArgs = new Dictionary<string, object>()
    {
        { "sessionId", SessionId },
    };

    // Only include optional parameter if non-default
    if (RetryCount != 3)
    {
        RequestArgs.Add("retryCount", RetryCount);
    }

    // ... rest of method
}
```

## HTTP Verb Inference Rules (REQ-F-22a)

The system infers the HTTP verb per RPC using REST semantics. The user can override the inferred verb during confirmation.

### Decision Tree

```
Function: InferHttpVerb(rpcName, parameters)

1. Check for body requirement:
   - If any parameter has type "object" or "object[]":
       Cannot use GET (body required)
       Skip to step 3 for POST/PUT decision

2. Check for GET eligibility (read-only, no body):
   - If rpcName starts with "Get", "List", "Query", or "Fetch":
     AND all parameters are primitive types (no object/object[]):
       Return GET

3. Check for PUT eligibility (idempotent update):
   - If rpcName starts with "Set", "Update", or "Replace":
       Return PUT

4. Default:
   - Return POST
```

### Inference Table

| RPC Name Prefix | Has Object Params | Inferred Verb |
|-----------------|-------------------|---------------|
| `Get*` | No | GET |
| `Get*` | Yes | POST (body overrides) |
| `List*` | No | GET |
| `Query*` | No | GET |
| `Fetch*` | No | GET |
| `Set*` | Any | PUT |
| `Update*` | Any | PUT |
| `Replace*` | Any | PUT |
| (anything else) | Any | POST |

### Examples

| RPC Name | Parameters | Inferred Verb | Reason |
|----------|-----------|---------------|--------|
| `GetPlayerStatus` | (none) | GET | Starts with Get, no params |
| `GetPlayerStatus` | `playerId:string` | GET | Starts with Get, primitive param |
| `GetPlayerConfig` | `filter:object` | POST | Starts with Get, but has object param |
| `SetPlayerName` | `name:string` | PUT | Starts with Set |
| `UpdatePreferences` | `prefs:object` | PUT | Starts with Update |
| `ValidateSession` | `sessionId:string` | POST | Default (no matching prefix) |
| `SpawnBot` | `botType:string` | POST | Default |
| `ListFriends` | (none) | GET | Starts with List, no params |

### Verb to C++ Enum Mapping

| HTTP Verb | C++ Enum |
|-----------|----------|
| GET | `EHttpServerRequestVerbs::VERB_GET` |
| PUT | `EHttpServerRequestVerbs::VERB_PUT` |
| POST | `EHttpServerRequestVerbs::VERB_POST` |

## References

- **Spec**: REQ-F-16 (default naming rules), REQ-F-17 (Http/Command stripping), REQ-F-18 (project-specific overrides), REQ-F-22a (HTTP verb inference)
- **Plan**: "Naming Convention Application" section for DeriveIdentifiers pseudocode, "HTTP verb inference" in Data Models section
