# RPC Scaffold Module

## Purpose

The RPC Scaffold module is a code generation toolset that automates the creation of complete RPC endpoints across four layers:

1. **C++ Hook Registration** - Registers the RPC callback in the manager component
2. **C++ Endpoint Handler** - Implements the HTTP request handler (declaration + implementation)
3. **C# Library Wrapper** - Provides the client-side API wrapper (with optional DTO)
4. **C# Test Case** - Generates the corresponding test case class

The system uses pattern-based generation where it learns from existing RPCs by extracting structural templates, then uses LLM reasoning to adapt those patterns to new RPCs with project-specific conventions. Pattern libraries are stored as annotated Markdown to enable human review and git version control.

## Commands

| Command | Description |
|---------|-------------|
| `/rpc-generate` | Generate complete RPC endpoint code from a manual specification (name, parameters, context) |
| `/rpc-discover` | Discover and inventory existing RPC registrations across the codebase |
| `/rpc-curate` | Extract and curate pattern libraries from existing RPC implementations |
| `/rpc-scenario` | Analyze test scenarios to suggest RPC operations for generation (Phase 1.5) |

## Directory Structure

- `commands/` - Slash command definitions registered in plugin.json
- `agents/` - Specialized agent definitions (RPC Generator, Pattern Extractor, Code Analyzer, Conflict Resolver)
- `services/` - Core service definitions (Pattern Library Manager, File Discovery, Code Insertion, RPC Discovery Scanner)
- `skills/` - Reusable skill modules (type mappings, naming conventions)
- `default-patterns/` - Shipped starter patterns for bootstrapping new projects
- `test_fixtures/` - Test data for validation (manager, library, scan fixtures)

## Validation

See the technical plan at `.sdd/plans/2026-02-18-rpc-scaffold-plan.md` for detailed acceptance tests and success criteria.
