# C++ Google Test Helper Template

This template provides reusable test helper utilities for C++ projects using Google Test and Google Mock.

## Mock Creation Helpers

```cpp
#include <gmock/gmock.h>
#include <gtest/gtest.h>
#include <memory>
#include <string>
#include <vector>

// Mock API Client
class MockApiClient {
public:
    MOCK_METHOD(std::string, GetBaseUrl, (), (const));
    MOCK_METHOD(Response, Get, (const std::string& path), ());
    MOCK_METHOD(Response, Post, (const std::string& path, const nlohmann::json& data), ());
    MOCK_METHOD(Response, Put, (const std::string& path, const nlohmann::json& data), ());
    MOCK_METHOD(Response, Delete, (const std::string& path), ());
};

// Factory function to create mock API client with default behaviors
std::unique_ptr<MockApiClient> CreateMockApiClient() {
    auto mockClient = std::make_unique<MockApiClient>();

    using ::testing::Return;
    using ::testing::_;

    ON_CALL(*mockClient, GetBaseUrl())
        .WillByDefault(Return("https://api.example.com"));
    ON_CALL(*mockClient, Get(_))
        .WillByDefault(Return(Response{200, "ok"}));
    ON_CALL(*mockClient, Post(_, _))
        .WillByDefault(Return(Response{201, "created"}));
    ON_CALL(*mockClient, Put(_, _))
        .WillByDefault(Return(Response{200, "updated"}));
    ON_CALL(*mockClient, Delete(_))
        .WillByDefault(Return(Response{204, "deleted"}));

    return mockClient;
}

// Mock Database
class MockDatabase {
public:
    MOCK_METHOD(bool, Connect, (), ());
    MOCK_METHOD(bool, Disconnect, (), ());
    MOCK_METHOD(std::vector<Row>, Query, (const std::string& sql), ());
    MOCK_METHOD(int, Execute, (const std::string& sql), ());
};

// Factory function to create mock database with default behaviors
std::unique_ptr<MockDatabase> CreateMockDatabase() {
    auto mockDb = std::make_unique<MockDatabase>();

    using ::testing::Return;
    using ::testing::_;

    ON_CALL(*mockDb, Connect())
        .WillByDefault(Return(true));
    ON_CALL(*mockDb, Disconnect())
        .WillByDefault(Return(true));
    ON_CALL(*mockDb, Query(_))
        .WillByDefault(Return(std::vector<Row>{}));
    ON_CALL(*mockDb, Execute(_))
        .WillByDefault(Return(1));

    return mockDb;
}

// Mock Logger
class MockLogger {
public:
    MOCK_METHOD(void, Info, (const std::string& msg), ());
    MOCK_METHOD(void, Warn, (const std::string& msg), ());
    MOCK_METHOD(void, Error, (const std::string& msg), ());
    MOCK_METHOD(void, Debug, (const std::string& msg), ());
};

// Factory function to create mock logger with default behaviors
std::unique_ptr<MockLogger> CreateMockLogger() {
    auto mockLogger = std::make_unique<MockLogger>();

    using ::testing::_;

    ON_CALL(*mockLogger, Info(_)).WillByDefault(::testing::Return());
    ON_CALL(*mockLogger, Warn(_)).WillByDefault(::testing::Return());
    ON_CALL(*mockLogger, Error(_)).WillByDefault(::testing::Return());
    ON_CALL(*mockLogger, Debug(_)).WillByDefault(::testing::Return());

    return mockLogger;
}
```

## Test Data Builders

```cpp
#include <string>
#include <vector>
#include <memory>

// User entity for testing
struct User {
    int id;
    std::string name;
    std::string email;
    int age;
    std::string role;
};

// Builder for creating test User objects with default values
class UserBuilder {
private:
    int id_ = 1;
    std::string name_ = "Test User";
    std::string email_ = "test@example.com";
    int age_ = 30;
    std::string role_ = "user";

public:
    UserBuilder& WithId(int id) {
        id_ = id;
        return *this;
    }

    UserBuilder& WithName(const std::string& name) {
        name_ = name;
        return *this;
    }

    UserBuilder& WithEmail(const std::string& email) {
        email_ = email;
        return *this;
    }

    UserBuilder& WithAge(int age) {
        age_ = age;
        return *this;
    }

    UserBuilder& WithRole(const std::string& role) {
        role_ = role;
        return *this;
    }

    User Build() const {
        return User{id_, name_, email_, age_, role_};
    }

    static User BuildDefault() {
        return UserBuilder().Build();
    }

    static std::vector<User> BuildList(int count) {
        std::vector<User> users;
        users.reserve(count);
        for (int i = 0; i < count; ++i) {
            users.push_back(
                UserBuilder()
                    .WithId(i + 1)
                    .WithName("User " + std::to_string(i + 1))
                    .WithEmail("user" + std::to_string(i + 1) + "@example.com")
                    .Build()
            );
        }
        return users;
    }
};

// Product entity for testing
struct Product {
    int id;
    std::string name;
    double price;
    std::string category;
    bool inStock;
};

// Builder for creating test Product objects with default values
class ProductBuilder {
private:
    int id_ = 1;
    std::string name_ = "Test Product";
    double price_ = 99.99;
    std::string category_ = "electronics";
    bool inStock_ = true;

public:
    ProductBuilder& WithId(int id) {
        id_ = id;
        return *this;
    }

    ProductBuilder& WithName(const std::string& name) {
        name_ = name;
        return *this;
    }

    ProductBuilder& WithPrice(double price) {
        price_ = price;
        return *this;
    }

    ProductBuilder& WithCategory(const std::string& category) {
        category_ = category;
        return *this;
    }

    ProductBuilder& WithInStock(bool inStock) {
        inStock_ = inStock;
        return *this;
    }

    Product Build() const {
        return Product{id_, name_, price_, category_, inStock_};
    }

    static Product BuildDefault() {
        return ProductBuilder().Build();
    }

    static std::vector<Product> BuildList(int count) {
        std::vector<Product> products;
        products.reserve(count);
        for (int i = 0; i < count; ++i) {
            products.push_back(
                ProductBuilder()
                    .WithId(i + 1)
                    .WithName("Product " + std::to_string(i + 1))
                    .Build()
            );
        }
        return products;
    }
};
```

## Setup and Teardown Utilities

```cpp
#include <gtest/gtest.h>
#include <memory>

// Base test fixture with common setup and teardown
class BaseTestFixture : public ::testing::Test {
protected:
    std::unique_ptr<MockApiClient> mockApi;
    std::unique_ptr<MockDatabase> mockDb;
    std::unique_ptr<MockLogger> mockLogger;

    void SetUp() override {
        mockApi = CreateMockApiClient();
        mockDb = CreateMockDatabase();
        mockLogger = CreateMockLogger();
    }

    void TearDown() override {
        // Cleanup is automatic with unique_ptr
        mockApi.reset();
        mockDb.reset();
        mockLogger.reset();
    }
};

// Utility for running tests with timeouts
template<typename Func>
void WithTimeout(Func&& testFunc, int timeoutMs = 5000) {
    std::atomic<bool> completed{false};
    std::thread testThread([&]() {
        testFunc();
        completed = true;
    });

    auto start = std::chrono::steady_clock::now();
    while (!completed) {
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start
        ).count();

        if (elapsed > timeoutMs) {
            testThread.detach();
            FAIL() << "Test timeout after " << timeoutMs << "ms";
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    testThread.join();
}

// Utility for database test setup and cleanup
template<typename Func>
void WithTestDatabase(Func&& testFunc) {
    auto mockDb = CreateMockDatabase();

    EXPECT_CALL(*mockDb, Connect())
        .WillOnce(::testing::Return(true));
    EXPECT_CALL(*mockDb, Disconnect())
        .WillOnce(::testing::Return(true));

    bool connected = mockDb->Connect();
    ASSERT_TRUE(connected);

    try {
        testFunc(mockDb.get());
    } catch (...) {
        mockDb->Disconnect();
        throw;
    }

    bool disconnected = mockDb->Disconnect();
    EXPECT_TRUE(disconnected);
}

// RAII helper for test resource management
template<typename T>
class TestResource {
private:
    T* resource_;
    std::function<void(T*)> cleanup_;

public:
    TestResource(T* resource, std::function<void(T*)> cleanup)
        : resource_(resource), cleanup_(cleanup) {}

    ~TestResource() {
        if (cleanup_ && resource_) {
            cleanup_(resource_);
        }
    }

    T* Get() { return resource_; }
    T* operator->() { return resource_; }

    TestResource(const TestResource&) = delete;
    TestResource& operator=(const TestResource&) = delete;
};
```

## Usage Examples

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>

using ::testing::Return;
using ::testing::_;
using ::testing::Eq;

class UserServiceTest : public BaseTestFixture {
protected:
    std::unique_ptr<UserService> service;

    void SetUp() override {
        BaseTestFixture::SetUp();
        service = std::make_unique<UserService>(
            mockApi.get(),
            mockLogger.get()
        );
    }
};

TEST_F(UserServiceTest, GetUserById_ShouldReturnUser) {
    // Arrange
    User testUser = UserBuilder()
        .WithId(123)
        .WithName("John Doe")
        .Build();

    EXPECT_CALL(*mockApi, Get("/users/123"))
        .WillOnce(Return(Response{200, testUser}));

    // Act
    auto result = service->GetUserById(123);

    // Assert
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->id, 123);
    EXPECT_EQ(result->name, "John Doe");
}

TEST_F(UserServiceTest, CreateUser_ShouldReturnCreatedUser) {
    // Arrange
    User newUser = UserBuilder()
        .WithId(0)
        .WithName("Jane Doe")
        .Build();

    User createdUser = UserBuilder()
        .WithId(456)
        .WithName("Jane Doe")
        .Build();

    EXPECT_CALL(*mockApi, Post("/users", _))
        .WillOnce(Return(Response{201, createdUser}));
    EXPECT_CALL(*mockLogger, Info(_))
        .Times(::testing::AtLeast(1));

    // Act
    auto result = service->CreateUser(newUser);

    // Assert
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result->id, 456);
}

TEST_F(UserServiceTest, GetAllUsers_ShouldReturnMultipleUsers) {
    // Arrange
    auto users = UserBuilder::BuildList(3);

    EXPECT_CALL(*mockApi, Get("/users"))
        .WillOnce(Return(Response{200, users}));

    // Act
    auto result = service->GetAllUsers();

    // Assert
    EXPECT_EQ(result.size(), 3);
}

TEST(UserServiceTimeoutTest, GetUserById_WithTimeout_ShouldNotExceed) {
    // Arrange
    auto mockApi = CreateMockApiClient();
    auto mockLogger = CreateMockLogger();
    auto testUser = UserBuilder::BuildDefault();

    EXPECT_CALL(*mockApi, Get(_))
        .WillOnce(Return(Response{200, testUser}));

    auto service = std::make_unique<UserService>(
        mockApi.get(),
        mockLogger.get()
    );

    // Act & Assert
    WithTimeout([&]() {
        auto result = service->GetUserById(1);
        EXPECT_TRUE(result.has_value());
    }, 1000);
}
```
