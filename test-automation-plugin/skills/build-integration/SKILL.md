---
name: build-integration
description: Integrate with project build systems to configure test dependencies and execution. Use when setting up testing frameworks in Maven, CMake, .NET, and Go projects, including adding test dependencies, configuring build targets, and ensuring test discovery.
user-invocable: false
---

# Build Integration Skill

**Version**: 1.0.0
**Category**: Infrastructure
**Languages**: Java (Maven/Gradle), C++ (CMake), C# (.NET), Go, Unreal Engine (UBT)
**Purpose**: Integrate with project build systems to configure test dependencies and execution

## Overview

The Build Integration Skill provides build system configuration capabilities for automated testing workflows. It enables correct setup of test dependencies, build targets, and test discovery across Java (Maven/Gradle), C++ (CMake), C# (.NET), Go, and Unreal Engine (UnrealBuildTool) build systems.

## Components

- `java-build-systems.md` - Maven and Gradle test dependency configuration
- `cmake-build-system.md` - CMake test target and Google Test/Catch2 integration
- `dotnet-build-systems.md` - .NET test project creation and xUnit/NUnit/MSTest setup
- `go-build-system.md` - Go module test configuration and build tags
- `ue-build-system.md` - UnrealBuildTool (UBT) test module build and execution for UE Low Level Tests
