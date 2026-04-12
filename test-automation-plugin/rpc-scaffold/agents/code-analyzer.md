---
name: code-analyzer
description: Extracts parameters, naming patterns, and formatting conventions from existing RPC implementations
tools:
  - Read
  - Grep
---

# Code Analyzer Agent

## Purpose

Analyzes RPC handler implementations to extract detailed metadata that the RPC Discovery Scanner cannot obtain from registration blocks alone. The agent reads actual function bodies and method signatures to infer parameter types (from C++ JSON getter patterns), detect sync vs async patterns (from C# method signatures), detect simple vs structured response types (from C# return types), and extract formatting conventions (indentation, spacing, comment style) from source files.

This agent is spawned by the RPC Discovery Scanner during Pass 2 (Step 6) for each RPC that has a found handler implementation. It is also used by the Pattern Extractor Agent during pattern curation.

---

## Operations

### ExtractParameters

Extracts parameter names and inferred types from a C++ handler function body by matching JSON getter patterns.

**Signature**: `ExtractParameters(handlerFile, handlerName)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `handlerFile` | string | Absolute path to the .cpp file containing the handler implementation |
| `handlerName` | string | The handler method name (e.g., `HttpBotAttackTargetCommand`) |

**Returns**:
```yaml
parameters:
  - name: "targetId"        # camelCase JSON field name
    type: "string"          # Inferred type from getter pattern
    getter: "GetStringField" # The actual getter method used
  - name: "damage"
    type: "int"
    getter: "GetIntegerField"
  - name: "weaponIds"
    type: "string[]"
    getter: "TryGetArrayField"
    element_type: "string"  # Only present for array types
  - name: "isCritical"
    type: "bool"
    getter: "GetBoolField"
```

**Algorithm**:

#### Step 1: Locate the Handler Function Body

Read the handler file and find the function implementation:

```
Grep(
  pattern="bool\s+\w+::{handlerName}\s*\(",
  path=handlerFile,
  output_mode="content",
  -n=true
)
```

This gives the starting line of the function. Then read from that line through the function body. The function ends at the matching closing brace `}` at the same indentation level as the `bool` keyword.

To extract the body, use the Read tool with an appropriate line range:
- Start: the line number from the Grep match
- End: scan forward until finding a line that is just `}` at column 0 (or the same indent as the function signature)

A practical approach: read a generous range (e.g., 100 lines from the function start) and then trim to the function boundary.

#### Step 2: Match JSON Getter Patterns

Within the function body, search for all JSON getter invocations. These patterns indicate parameter extraction from the request JSON:

**Primary getter patterns** (direct field access):

| Pattern | Inferred Type | Regex |
|---------|---------------|-------|
| `GetStringField(TEXT("paramName"))` | `string` | `->GetStringField\(TEXT\("(\w+)"\)\)` |
| `GetIntegerField(TEXT("paramName"))` | `int` | `->GetIntegerField\(TEXT\("(\w+)"\)\)` |
| `GetNumberField(TEXT("paramName"))` | `float` | `->GetNumberField\(TEXT\("(\w+)"\)\)` |
| `GetBoolField(TEXT("paramName"))` | `bool` | `->GetBoolField\(TEXT\("(\w+)"\)\)` |
| `GetObjectField(TEXT("paramName"))` | `object` | `->GetObjectField\(TEXT\("(\w+)"\)\)` |
| `GetArrayField(TEXT("paramName"))` | `array` (see element detection) | `->GetArrayField\(TEXT\("(\w+)"\)\)` |

**Alternative getter patterns** (Try-prefixed, used for optional parameters or arrays):

| Pattern | Inferred Type | Regex |
|---------|---------------|-------|
| `TryGetStringField(TEXT("paramName"), ...)` | `string` | `->TryGetStringField\(TEXT\("(\w+)"\)` |
| `TryGetNumberField(TEXT("paramName"), ...)` | `float` | `->TryGetNumberField\(TEXT\("(\w+)"\)` |
| `TryGetBoolField(TEXT("paramName"), ...)` | `bool` | `->TryGetBoolField\(TEXT\("(\w+)"\)` |
| `TryGetArrayField(TEXT("paramName"), ...)` | `array` (see element detection) | `->TryGetArrayField\(TEXT\("(\w+)"\)` |
| `TryGetObjectField(TEXT("paramName"), ...)` | `object` | `->TryGetObjectField\(TEXT\("(\w+)"\)` |

For each match:
1. Extract the parameter name from Group 1 of the regex.
2. Map the getter method to the inferred type using the table above.
3. Record the getter name for reference.

#### Step 3: Detect Array Element Types

When `GetArrayField` or `TryGetArrayField` is matched for a parameter, perform additional analysis to determine the array element type. Look at the code following the array extraction to find element access patterns:

**String array detection**:
```cpp
// Pattern: iterating over array and calling TryGetString or GetString
for (const TSharedPtr<FJsonValue>& Value : *ArrayName)
{
    FString ElementVar;
    if (Value->TryGetString(ElementVar))
```
- If `TryGetString` or `AsString()` is found in the loop body -> type = `string[]`

**Number array detection**:
```cpp
Value->TryGetNumber(ElementVar)
// or
Value->AsNumber()
```
- If `TryGetNumber` or `AsNumber()` is found -> type = `float[]`
- If the variable type is `int32` or an explicit cast to int is present -> type = `int[]`

**Bool array detection**:
```cpp
Value->TryGetBool(ElementVar)
// or
Value->AsBool()
```
- If `TryGetBool` or `AsBool()` is found -> type = `bool[]`

**Object array detection**:
```cpp
Value->TryGetObject(ElementVar)
// or
Value->AsObject()
```
- If `TryGetObject` or `AsObject()` is found -> type = `object[]`

**Fallback**: If the element type cannot be determined, default to `string[]` and add a note:
```yaml
- name: "myArray"
  type: "string[]"
  getter: "TryGetArrayField"
  element_type: "string"
  note: "Element type inferred as string (default). Verify manually."
```

**Example**: In the `HttpBotAttackTargetCommand` handler from the test fixture:
```cpp
TArray<FString> WeaponIds;
const TArray<TSharedPtr<FJsonValue>>* WeaponIdsJsonArray;
if (JsonRequest->TryGetArrayField(TEXT("weaponIds"), WeaponIdsJsonArray))
{
    for (const TSharedPtr<FJsonValue>& Value : *WeaponIdsJsonArray)
    {
        FString WeaponId;
        if (Value->TryGetString(WeaponId))
        {
            WeaponIds.Add(WeaponId);
        }
    }
}
```

Analysis:
- `TryGetArrayField(TEXT("weaponIds"), ...)` -> array parameter named `weaponIds`
- `Value->TryGetString(...)` inside the loop -> element type is `string`
- Result: `{name: "weaponIds", type: "string[]", getter: "TryGetArrayField", element_type: "string"}`

#### Step 4: Deduplicate and Order

If the same parameter name appears multiple times (e.g., accessed in different code paths), keep only the first occurrence. Order parameters by their order of appearance in the function body (top to bottom).

#### Step 5: Return Results

Return the parameter list with inferred types.

**Example output for `HttpBotAttackTargetCommand`**:
```yaml
parameters:
  - name: "targetId"
    type: "string"
    getter: "GetStringField"
  - name: "damage"
    type: "int"
    getter: "GetIntegerField"
  - name: "isCritical"
    type: "bool"
    getter: "GetBoolField"
  - name: "weaponIds"
    type: "string[]"
    getter: "TryGetArrayField"
    element_type: "string"
```

Note: The order may differ from the registration descriptor order. The `isCritical` param is extracted before `weaponIds` because `GetBoolField` appears before `TryGetArrayField` in the handler body. The scanner merges these results with the descriptor order from Pass 2 Step 2, using the descriptor order as authoritative.

**Example output for `HttpLoginUserCommand`**:
```yaml
parameters:
  - name: "username"
    type: "string"
    getter: "GetStringField"
  - name: "password"
    type: "string"
    getter: "GetStringField"
```

**Example output for `HttpDebugDumpStateCommand`**:
```yaml
parameters:
  - name: "category"
    type: "string"
    getter: "GetStringField"
  - name: "verbose"
    type: "bool"
    getter: "GetBoolField"
```

---

### DetectAsyncPattern

Detects whether a C# library method uses synchronous or asynchronous invocation.

**Signature**: `DetectAsyncPattern(libraryFile, methodName)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `libraryFile` | string | Absolute path to the C# library .cs file |
| `methodName` | string | The base RPC method name (e.g., `GetPlayerStatus`). The agent checks for both `{methodName}` and `{methodName}Async`. |

**Returns**:
```yaml
async: true|false
method_name_found: "GetPlayerStatusAsync"  # Actual method name found
evidence: "Method signature contains 'async Task<GetPlayerStatusResponse>'"
```

**Algorithm**:

#### Step 1: Search for the Method

Search the library file for the method by name. Check both sync and async variants:

```
Grep(
  pattern="public\s+static\s+\S+\s+({methodName}|{methodName}Async)\s*\(",
  path=libraryFile,
  output_mode="content",
  -n=true,
  -A=5
)
```

If no match is found, return:
```yaml
async: false
method_name_found: null
evidence: "Method not found in library file"
```

#### Step 2: Analyze the Method Signature

Examine the matched method signature for async indicators:

**Async indicators** (any one is sufficient):

| Indicator | Pattern | Confidence |
|-----------|---------|------------|
| Method name ends with `Async` | `{methodName}Async` | High |
| Return type is `Task<T>` or `Task` | `async\s+Task` | High |
| `async` keyword in signature | `public\s+static\s+async\s+` | High |
| `CancellationToken` parameter | `CancellationToken` in parameter list | High |

**Sync indicators**:

| Indicator | Pattern | Confidence |
|-----------|---------|------------|
| Return type is `bool` | `public\s+static\s+bool\s+` | High |
| Return type is `void` | `public\s+static\s+void\s+` | High |
| No `async` keyword | absence of `async` in signature | Medium |
| No `CancellationToken` parameter | absence of `CancellationToken` | Medium |

#### Step 3: Check Method Body (Supplementary)

If the signature analysis is inconclusive (e.g., return type is a custom class but no `async` keyword), read the method body and look for:

- `await` keyword -> async = true
- `CallRpcAsync` invocation -> async = true
- `CallRpc` invocation (without Async) -> async = false

#### Step 4: Return Result

**Example for `GetPlayerStatus`** (from test fixture SampleRpcLibrary.cs):

The method `GetPlayerStatusAsync` at line 181:
```csharp
public static async Task<GetPlayerStatusResponse> GetPlayerStatusAsync(RpcTarget InTarget, string PlayerId, CancellationToken InCancellationToken)
```

Result:
```yaml
async: true
method_name_found: "GetPlayerStatusAsync"
evidence: "Method signature: 'async Task<GetPlayerStatusResponse>', name has 'Async' suffix, has CancellationToken parameter"
```

**Example for `LoginUser`** (from test fixture SampleRpcLibrary.cs):

The method `LoginUser` at line 115:
```csharp
public static bool LoginUser(RpcTarget InTarget, string Username, string Password)
```

Result:
```yaml
async: false
method_name_found: "LoginUser"
evidence: "Method signature: 'public static bool', no async keyword, no CancellationToken parameter"
```

---

### DetectResponseType

Detects whether a C# library method returns a simple success/failure result or a structured response object.

**Signature**: `DetectResponseType(libraryFile, methodName)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `libraryFile` | string | Absolute path to the C# library .cs file |
| `methodName` | string | The base RPC method name (e.g., `GetPlayerStatus`). The agent checks for both `{methodName}` and `{methodName}Async`. |

**Returns**:
```yaml
response_type: "simple"|"structured"
return_type: "bool"              # The actual C# return type
dto_class: "GetPlayerStatusResponse"  # Only present if structured
evidence: "Return type is 'GetPlayerStatusResponse' (custom DTO class)"
```

**Algorithm**:

#### Step 1: Find the Method Signature

Use the same Grep as DetectAsyncPattern to locate the method signature.

#### Step 2: Extract the Return Type

From the method signature, extract the return type:

- For sync methods: `public\s+static\s+(\S+)\s+{methodName}\(`
  - Group 1 is the return type (e.g., `bool`, `string`, `void`, `CustomResponse`)
- For async methods: `public\s+static\s+async\s+Task<(\S+)>\s+{methodName}Async\(`
  - Group 1 is the inner type of `Task<T>` (e.g., `GetPlayerStatusResponse`)
  - If `Task` without a type parameter: `public\s+static\s+async\s+Task\s+`
    - Return type is effectively `void` (simple)

#### Step 3: Classify the Return Type

**Simple response types** (return type indicates success/failure or void):
- `bool` -> simple
- `void` -> simple
- `string` -> simple
- `int` -> simple
- `Task` (without type parameter) -> simple
- `SimpleResponse` or similar framework-provided result type -> simple

**Structured response types** (return type is a custom DTO class):
- Any PascalCase class name that is NOT a primitive type -> structured
  - Examples: `GetPlayerStatusResponse`, `LoginResult`, `MatchData`
- Detection heuristic: if the return type ends with `Response`, `Result`, `Data`, `Info`, or `DTO`, it is likely structured
- If the return type does not match any known simple type, default to structured

#### Step 4: Locate the DTO Class (if structured)

If the response type is classified as structured, search the file for the DTO class definition:

```
Grep(
  pattern="public\s+class\s+{returnType}",
  path=libraryFile,
  output_mode="content",
  -n=true,
  -A=10
)
```

If found, extract the DTO's public properties:
```
Grep(
  pattern="public\s+(\S+)\s+(\w+)\s*\{\s*get;\s*set;\s*\}",
  path=libraryFile,
  output_mode="content",
  -n=true
)
```

This yields the response fields:
```yaml
dto_fields:
  - name: "PlayerName"
    type: "string"
  - name: "Level"
    type: "int"
  - name: "bIsOnline"
    type: "bool"
```

#### Step 5: Return Result

**Example for `GetPlayerStatus`** (structured response):

```yaml
response_type: "structured"
return_type: "GetPlayerStatusResponse"
dto_class: "GetPlayerStatusResponse"
dto_fields:
  - name: "PlayerName"
    type: "string"
  - name: "Level"
    type: "int"
  - name: "bIsOnline"
    type: "bool"
evidence: "Return type 'GetPlayerStatusResponse' is a custom DTO class with 3 properties"
```

**Example for `LoginUser`** (simple response):

```yaml
response_type: "simple"
return_type: "bool"
dto_class: null
evidence: "Return type 'bool' is a primitive type indicating success/failure"
```

**Example for `BotAttackTarget`** (simple response):

```yaml
response_type: "simple"
return_type: "bool"
dto_class: null
evidence: "Return type 'bool' is a primitive type indicating success/failure"
```

---

### ExtractFormattingConventions

Extracts indentation style, spacing patterns, and comment conventions from a source file. Used by the Pattern Extractor Agent and the RPC Generator Agent to ensure generated code matches existing file formatting.

**Signature**: `ExtractFormattingConventions(file)`

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | string | Absolute path to the source file to analyze |

**Returns**:
```yaml
formatting:
  indentation:
    style: "tabs"|"spaces"
    size: 4                     # Number of spaces per indent level (only for spaces)
  line_endings: "crlf"|"lf"    # Detected from file content
  blank_lines_between_methods: 1|2  # Number of blank lines separating method implementations
  brace_style: "next_line"|"same_line"|"mixed"
  trailing_newline: true|false  # Whether file ends with a newline
  max_line_length: 120          # Observed maximum line length (approximate)
  comment_style:
    section_headers: true|false     # Whether section headers (e.g., "// ---") are used
    section_header_pattern: "// ---"  # The specific pattern observed
    xml_doc_comments: true|false    # Whether C# XML doc comments (/// <summary>) are used
    inline_comments: true|false     # Whether inline comments are present
```

**Algorithm**:

#### Step 1: Read the File

Use the Read tool to load the entire file content.

#### Step 2: Detect Indentation Style

Examine the first 50 non-empty, non-comment lines:

1. Count lines starting with tab characters vs lines starting with spaces.
2. If >80% use tabs: `style = "tabs"`
3. If >80% use spaces: `style = "spaces"`, count the most common leading-space count to determine `size`
4. If mixed: `style = "tabs"` (default to tabs for C++ files, spaces for C# files based on extension)

#### Step 3: Detect Blank Line Spacing

Find consecutive method implementations (for C++) or method definitions (for C#):

1. Locate pairs of adjacent methods.
2. Count the blank lines between the closing brace of one method and the opening line (or doc comment) of the next.
3. Report the most common count.

#### Step 4: Detect Brace Style

For C++ files, check if opening braces appear on the same line as control structures or on the next line:

- `if (condition) {` -> same_line
- `if (condition)\n{` -> next_line

For C# files, the convention is typically next_line (Allman style).

Report the dominant pattern.

#### Step 5: Detect Comment Style

Search for:
- Section header comments: `^// [-=]{3,}` (e.g., `// ---------------------------------------------------------------------------`)
- XML doc comments: `/// <summary>` (C# files)
- Inline comments: `//` at end of code lines

#### Step 6: Return Results

**Example for `EOSDemoRpcManager_Core.cpp`**:
```yaml
formatting:
  indentation:
    style: "tabs"
    size: null
  blank_lines_between_methods: 2
  brace_style: "next_line"
  trailing_newline: true
  comment_style:
    section_headers: true
    section_header_pattern: "// ---------------------------------------------------------------------------"
    xml_doc_comments: false
    inline_comments: true
```

**Example for `SampleRpcLibrary.cs`**:
```yaml
formatting:
  indentation:
    style: "spaces"
    size: 4
  blank_lines_between_methods: 1
  brace_style: "next_line"
  trailing_newline: true
  comment_style:
    section_headers: true
    section_header_pattern: "// ==================================================================="
    xml_doc_comments: true
    inline_comments: false
```

---

## Cross-Reference Validation

When the RPC Discovery Scanner passes both descriptor-declared parameters (from registration `FRpcParameterDescriptor` entries) and handler-inferred parameters (from this agent's `ExtractParameters`) for the same RPC, the scanner should merge them as follows:

### Merge Strategy

1. **Descriptor parameters are authoritative for ordering**: The order of parameters from `FRpcParameterDescriptor` entries is the canonical order.

2. **Handler parameters are authoritative for type inference**: When the descriptor uses a generic type like `ERpcParamType::StringArray`, the handler analysis provides the specific element type (e.g., `string[]` confirmed by `TryGetString` in the loop).

3. **Handler may reveal additional parameters**: If the handler accesses JSON fields not listed in the descriptors, these are "undeclared parameters". Flag them in the report:
   ```yaml
   - name: "extraField"
     type: "string"
     note: "Found in handler but not in registration descriptors"
   ```

4. **Descriptor may list unused parameters**: If a parameter is in the descriptors but not accessed in the handler, flag it:
   ```yaml
   - name: "unusedParam"
     type: "string"
     note: "Declared in descriptors but not accessed in handler"
   ```

### Example: BotAttackTarget Cross-Reference

**From descriptors** (Pass 2 Step 2):
```
targetId: String, damage: Int, weaponIds: StringArray, isCritical: Bool
```

**From handler** (ExtractParameters):
```
targetId: string (GetStringField), damage: int (GetIntegerField), isCritical: bool (GetBoolField), weaponIds: string[] (TryGetArrayField + TryGetString)
```

**Merged result** (descriptor order, handler types):
```yaml
parameters:
  - name: "targetId"
    type: "string"
  - name: "damage"
    type: "int"
  - name: "weaponIds"
    type: "string[]"    # Handler confirms element type is string
  - name: "isCritical"
    type: "bool"
```

All 4 parameters match between descriptors and handler. No discrepancies. The `weaponIds` type is refined from the generic `StringArray` descriptor to the specific `string[]` confirmed by the handler's `TryGetString` usage.

---

## Error Handling

### Handler Function Not Found

If the specified `handlerName` cannot be found in `handlerFile`:

```yaml
error: "Handler not found"
handlerName: "{handlerName}"
file: "{handlerFile}"
note: "The handler method was not found in the specified file. It may be in a different file or the method name may differ."
```

Return empty parameters and let the scanner fall back to descriptor-only types.

### No Getter Patterns Found

If the handler function body contains no recognizable JSON getter patterns:

```yaml
parameters: []
note: "No JSON getter patterns found in handler body. The handler may use a non-standard parsing approach."
```

This can happen if the handler:
- Uses a custom deserialization framework
- Accepts no parameters (but has a JSON parse guard for validation)
- Delegates parsing to another function

### Library File Not Found

If the library file path does not exist:

```yaml
async: false
response_type: "simple"
note: "Library file not found. Defaulting to sync/simple."
```

### Method Not Found in Library

If neither `{methodName}` nor `{methodName}Async` is found in the library file:

```yaml
async: false
method_name_found: null
note: "Method not found in library. May use a different naming convention."
```

The scanner marks the library layer as `missing`.

---

## Spec Traceability

| Requirement | How Addressed |
|---|---|
| AT-8 | ExtractParameters matches `GetStringField`, `GetIntegerField`, `GetBoolField` etc. to infer types |
| REQ-F-7 | DetectAsyncPattern distinguishes sync vs async; DetectResponseType distinguishes simple vs structured |
| REQ-F-19 | Type inference table maps C++ getter patterns to the same type system used in REQ-F-19 |
| REQ-NF-4 | ExtractFormattingConventions captures indentation, spacing, and comment conventions |
| REQ-F-2 | All operations contribute to the complete RPC metadata for the discovery report |
