---
name: llt-online-tests
description: Specialized guidance for working with Epic's Online Tests framework (OSSv2 testing)
user-invocable: false
---

# LLT: Online Tests Framework

**Purpose:** Specialized guidance for working with Epic's Online Tests framework (OSSv2 testing).

## Framework Overview

Online Tests is a production LowLevelTest variant built on Catch2 for testing OnlineSubsystem interfaces (OSSv2). It uses a **builder pattern** for async operation orchestration.

### Key Components

- **OnlineTestsCore** (Public): Core builder pattern infrastructure, step definitions
- **OnlineTests** (Internal): Epic-internal test implementations
- **Builder Pattern**: Chain async steps with `.EmplaceStep<T>()` and execute with `.RunToCompletion()`

### Test Macros

```cpp
ONLINE_TEST_CASE("Login to EOS", "[Login][EOS]")
{
    GetLoginPipeline(FOnlineAccountIdRegistryRegistry::Get(EOnlineServices::Epic))
        .EmplaceStep<FOnlineAutoLogin>()
        .EmplaceStep<FOnlineAutoLogout>()
        .RunToCompletion();
}

RESONANCE_TEST_CASE("Join Audio Channel", "[Resonance][Audio]")
{
    GetLoginPipeline()
        .EmplaceStep<FSetupResonanceChannel>()
        .EmplaceStep<FJoinResonanceChannel>()
        .EmplaceStep<FVerifyAudioPackets>()
        .RunToCompletion();
}
```

### Common Pipelines

| Pipeline | Purpose | Common Steps |
|----------|---------|--------------|
| Login Pipeline | User authentication | FOnlineAutoLogin, FOnlineAutoLogout |
| Session Pipeline | Matchmaking/sessions | FCreateSession, FJoinSession, FLeaveSession |
| Resonance Pipeline | Voice chat | FSetupResonanceChannel, FJoinResonanceChannel |

### Step Pattern

Steps inherit from `FOnlineStep` and implement async operations:

```cpp
class FOnlineAutoLogin : public FOnlineStep
{
    virtual void Run(FOnlineStepContext& Context) override
    {
        // Async login operation
        Context.OnlineServices->GetAuthInterface()->Login(...)
            .OnComplete([this, &Context](const TOnlineResult<FAuthLogin>& Result)
            {
                Context.CompleteStep(Result.IsOk());
            });
    }
};
```

### Integration with llt-find

Online Tests are discovered like standard LLTs:
- Module: `OnlineTests` (internal), `OnlineServicesMcpTests` (per-service)
- Test macros: `ONLINE_TEST_CASE`, `RESONANCE_TEST_CASE`
- BuildGraph: Registered in `FortniteGame/Build/LowLevelTests.xml`

### References

- **Documentation**: Online Tests Internal Documentation.pdf
- **Source**: `FortniteGame/Plugins/ForEngine/Online/OnlineTestsCore/`
- **Examples**: `FortniteGame/Plugins/ForEngine/Online/OnlineServicesMcp/Tests/`
