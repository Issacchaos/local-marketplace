# Type Mapping Skill

## Purpose

This skill provides the complete type mapping table for the RPC Scaffold System. It maps the 10 supported parameter types across C++, C#, and JSON representations. All agents and services reference this table when generating code for any of the four RPC layers.

## Supported Types

The system supports 10 parameter types as defined in REQ-F-19.

## Complete Type Mapping Table

| Inferred Type | C++ Type | C# Type | JSON Getter (C++) | JSON Field Type | cpp_variable_prefix | element_type | todo_comment |
|---------------|----------|---------|-------------------|-----------------|---------------------|--------------|--------------|
| `string` | `FString` | `string` | `GetStringField()` | string | | | |
| `int` | `int32` | `int` | `GetIntegerField()` | number | | | |
| `float` | `double` | `double` | `GetNumberField()` | number | | | |
| `bool` | `bool` | `bool` | `GetBoolField()` | boolean | `b` | | |
| `string[]` | `TArray<FString>` | `List<string>` | `GetArrayField()` | array | | `string` | |
| `int[]` | `TArray<int32>` | `List<int>` | `GetArrayField()` | array | | `int` | |
| `float[]` | `TArray<double>` | `List<double>` | `GetArrayField()` | array | | `float` | |
| `bool[]` | `TArray<bool>` | `List<bool>` | `GetArrayField()` | array | | `bool` | |
| `object[]` | `TArray<TSharedPtr<FJsonObject>>` | `List<object>` | `GetArrayField()` | array | | `object` | `// TODO: specify element type` |
| `object` | `TSharedPtr<FJsonObject>` | `object` | `GetObjectField()` | object | | | `// TODO: specify type` |

## Structured YAML Representation

```yaml
type_mappings:
  string:
    cpp_type: "FString"
    cpp_getter: "GetStringField"
    csharp_type: "string"
    json_field_type: "string"

  int:
    cpp_type: "int32"
    cpp_getter: "GetIntegerField"
    csharp_type: "int"
    json_field_type: "number"

  float:
    cpp_type: "double"
    cpp_getter: "GetNumberField"
    csharp_type: "double"
    json_field_type: "number"

  bool:
    cpp_type: "bool"
    cpp_getter: "GetBoolField"
    cpp_variable_prefix: "b"
    csharp_type: "bool"
    json_field_type: "boolean"

  string[]:
    cpp_type: "TArray<FString>"
    cpp_getter: "GetArrayField"
    csharp_type: "List<string>"
    json_field_type: "array"
    element_type: "string"

  int[]:
    cpp_type: "TArray<int32>"
    cpp_getter: "GetArrayField"
    csharp_type: "List<int>"
    json_field_type: "array"
    element_type: "int"

  float[]:
    cpp_type: "TArray<double>"
    cpp_getter: "GetArrayField"
    csharp_type: "List<double>"
    json_field_type: "array"
    element_type: "float"

  bool[]:
    cpp_type: "TArray<bool>"
    cpp_getter: "GetArrayField"
    csharp_type: "List<bool>"
    json_field_type: "array"
    element_type: "bool"

  object[]:
    cpp_type: "TArray<TSharedPtr<FJsonObject>>"
    cpp_getter: "GetArrayField"
    csharp_type: "List<object>"
    json_field_type: "array"
    element_type: "object"
    todo_comment: "// TODO: specify element type"

  object:
    cpp_type: "TSharedPtr<FJsonObject>"
    cpp_getter: "GetObjectField"
    csharp_type: "object"
    json_field_type: "object"
    todo_comment: "// TODO: specify type"
```

## Usage Instructions

### Applying Mappings During C++ Code Generation

For each parameter in the RPC specification, look up its type in the mapping table and generate the appropriate extraction code.

**Standard parameter extraction pattern:**

```cpp
// For a parameter: sessionId:string
FString SessionId = JsonRequest->GetStringField(TEXT("sessionId"));

// For a parameter: retryCount:int
int32 RetryCount = JsonRequest->GetIntegerField(TEXT("retryCount"));

// For a parameter: isEnabled:bool (note: 'b' prefix per Unreal convention)
bool bIsEnabled = JsonRequest->GetBoolField(TEXT("isEnabled"));

// For a parameter: damage:float
double Damage = JsonRequest->GetNumberField(TEXT("damage"));
```

**Array parameter extraction pattern:**

```cpp
// For a parameter: tags:string[]
TArray<TSharedPtr<FJsonValue>> TagsArray = JsonRequest->GetArrayField(TEXT("tags"));
TArray<FString> Tags;
for (const auto& Element : TagsArray)
{
    Tags.Add(Element->AsString());
}
```

**Object parameter extraction pattern (includes TODO comment per REQ-F-20):**

```cpp
// TODO: specify type
TSharedPtr<FJsonObject> Config = JsonRequest->GetObjectField(TEXT("config"));
```

### Applying Mappings During C# Code Generation

**Building request arguments dictionary:**

```csharp
// For string, int, float, bool parameters:
var RequestArgs = new Dictionary<string, object>()
{
    { "sessionId", SessionId },       // string
    { "retryCount", RetryCount },     // int
    { "isEnabled", IsEnabled },       // bool
    { "damage", Damage },             // double
};

// For object parameters (includes TODO comment per REQ-F-20):
// TODO: specify type
RequestArgs.Add("config", Config);
```

**Response DTO property types:**

```csharp
public class MyRpcResponse
{
    public string Name { get; set; }       // string
    public int Count { get; set; }         // int
    public double Score { get; set; }      // float
    public bool IsActive { get; set; }     // bool
    public List<string> Tags { get; set; } // string[]
}
```

### Bool Variable Prefix Rule

Per Unreal Engine coding standards, boolean variables in C++ must use the `b` prefix:

- Parameter name `isEnabled` becomes C++ variable `bIsEnabled`
- Parameter name `active` becomes C++ variable `bActive`
- The `cpp_variable_prefix: "b"` field in the mapping table signals this rule

The prefix is applied by capitalizing the first letter of the parameter name and prepending `b`:
```
boolVarName = "b" + capitalize(parameterName)
```

### TODO Comments for Unresolved Types

When a parameter type is `object` or `object[]`, the system cannot infer the concrete type. Per REQ-F-20, a `// TODO: specify type` comment is inserted at each usage site in the generated code. This alerts the developer to replace the generic type with a project-specific concrete type.

## References

- **Spec**: REQ-F-19 (type mapping table), REQ-F-20 (TODO comments for object types)
- **Plan**: "Type Mapping System" section for structured YAML and usage in generation
