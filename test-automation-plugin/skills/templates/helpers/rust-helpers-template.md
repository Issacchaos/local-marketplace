# Rust Test Helper Template

This template provides reusable test helper utilities for Rust projects using the standard test framework and mockall.

## Mock Creation Helpers

```rust
use mockall::mock;
use mockall::predicate::*;

// Mock API Client trait and implementation
pub trait ApiClient {
    fn get(&self, path: &str) -> Result<Response, Error>;
    fn post(&self, path: &str, data: &serde_json::Value) -> Result<Response, Error>;
    fn put(&self, path: &str, data: &serde_json::Value) -> Result<Response, Error>;
    fn delete(&self, path: &str) -> Result<(), Error>;
}

mock! {
    pub ApiClient {}

    impl ApiClient for ApiClient {
        fn get(&self, path: &str) -> Result<Response, Error>;
        fn post(&self, path: &str, data: &serde_json::Value) -> Result<Response, Error>;
        fn put(&self, path: &str, data: &serde_json::Value) -> Result<Response, Error>;
        fn delete(&self, path: &str) -> Result<(), Error>;
    }
}

/// Create a mock API client with common default behaviors
pub fn create_mock_api_client() -> MockApiClient {
    let mut mock = MockApiClient::new();

    mock.expect_get()
        .returning(|_| Ok(Response {
            status: 200,
            body: "ok".to_string(),
        }));

    mock.expect_post()
        .returning(|_, _| Ok(Response {
            status: 201,
            body: "created".to_string(),
        }));

    mock.expect_put()
        .returning(|_, _| Ok(Response {
            status: 200,
            body: "updated".to_string(),
        }));

    mock.expect_delete()
        .returning(|_| Ok(()));

    mock
}

// Mock Database trait and implementation
pub trait Database {
    fn connect(&mut self) -> Result<(), Error>;
    fn disconnect(&mut self) -> Result<(), Error>;
    fn query(&self, sql: &str) -> Result<Vec<Row>, Error>;
    fn execute(&self, sql: &str) -> Result<u64, Error>;
}

mock! {
    pub Database {}

    impl Database for Database {
        fn connect(&mut self) -> Result<(), Error>;
        fn disconnect(&mut self) -> Result<(), Error>;
        fn query(&self, sql: &str) -> Result<Vec<Row>, Error>;
        fn execute(&self, sql: &str) -> Result<u64, Error>;
    }
}

/// Create a mock database with common default behaviors
pub fn create_mock_database() -> MockDatabase {
    let mut mock = MockDatabase::new();

    mock.expect_connect()
        .returning(|| Ok(()));

    mock.expect_disconnect()
        .returning(|| Ok(()));

    mock.expect_query()
        .returning(|_| Ok(Vec::new()));

    mock.expect_execute()
        .returning(|_| Ok(1));

    mock
}

// Mock Logger trait and implementation
pub trait Logger {
    fn info(&self, msg: &str);
    fn warn(&self, msg: &str);
    fn error(&self, msg: &str);
    fn debug(&self, msg: &str);
}

mock! {
    pub Logger {}

    impl Logger for Logger {
        fn info(&self, msg: &str);
        fn warn(&self, msg: &str);
        fn error(&self, msg: &str);
        fn debug(&self, msg: &str);
    }
}

/// Create a mock logger with common default behaviors
pub fn create_mock_logger() -> MockLogger {
    let mut mock = MockLogger::new();

    mock.expect_info().returning(|_| ());
    mock.expect_warn().returning(|_| ());
    mock.expect_error().returning(|_| ());
    mock.expect_debug().returning(|_| ());

    mock
}
```

## Test Data Builders

```rust
/// User entity for testing
#[derive(Debug, Clone, PartialEq)]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
    pub age: i32,
    pub role: String,
}

/// Builder for creating test User objects with default values
#[derive(Default)]
pub struct UserBuilder {
    id: i32,
    name: String,
    email: String,
    age: i32,
    role: String,
}

impl UserBuilder {
    pub fn new() -> Self {
        Self {
            id: 1,
            name: "Test User".to_string(),
            email: "test@example.com".to_string(),
            age: 30,
            role: "user".to_string(),
        }
    }

    pub fn with_id(mut self, id: i32) -> Self {
        self.id = id;
        self
    }

    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.name = name.into();
        self
    }

    pub fn with_email(mut self, email: impl Into<String>) -> Self {
        self.email = email.into();
        self
    }

    pub fn with_age(mut self, age: i32) -> Self {
        self.age = age;
        self
    }

    pub fn with_role(mut self, role: impl Into<String>) -> Self {
        self.role = role.into();
        self
    }

    pub fn build(self) -> User {
        User {
            id: self.id,
            name: self.name,
            email: self.email,
            age: self.age,
            role: self.role,
        }
    }
}

/// Build a default test user
pub fn build_default_user() -> User {
    UserBuilder::new().build()
}

/// Build a list of test users with sequential IDs
pub fn build_user_list(count: usize) -> Vec<User> {
    (0..count)
        .map(|i| {
            UserBuilder::new()
                .with_id((i + 1) as i32)
                .with_name(format!("User {}", i + 1))
                .with_email(format!("user{}@example.com", i + 1))
                .build()
        })
        .collect()
}

/// Product entity for testing
#[derive(Debug, Clone, PartialEq)]
pub struct Product {
    pub id: i32,
    pub name: String,
    pub price: f64,
    pub category: String,
    pub in_stock: bool,
}

/// Builder for creating test Product objects with default values
#[derive(Default)]
pub struct ProductBuilder {
    id: i32,
    name: String,
    price: f64,
    category: String,
    in_stock: bool,
}

impl ProductBuilder {
    pub fn new() -> Self {
        Self {
            id: 1,
            name: "Test Product".to_string(),
            price: 99.99,
            category: "electronics".to_string(),
            in_stock: true,
        }
    }

    pub fn with_id(mut self, id: i32) -> Self {
        self.id = id;
        self
    }

    pub fn with_name(mut self, name: impl Into<String>) -> Self {
        self.name = name.into();
        self
    }

    pub fn with_price(mut self, price: f64) -> Self {
        self.price = price;
        self
    }

    pub fn with_category(mut self, category: impl Into<String>) -> Self {
        self.category = category.into();
        self
    }

    pub fn with_in_stock(mut self, in_stock: bool) -> Self {
        self.in_stock = in_stock;
        self
    }

    pub fn build(self) -> Product {
        Product {
            id: self.id,
            name: self.name,
            price: self.price,
            category: self.category,
            in_stock: self.in_stock,
        }
    }
}

/// Build a default test product
pub fn build_default_product() -> Product {
    ProductBuilder::new().build()
}

/// Build a list of test products with sequential IDs
pub fn build_product_list(count: usize) -> Vec<Product> {
    (0..count)
        .map(|i| {
            ProductBuilder::new()
                .with_id((i + 1) as i32)
                .with_name(format!("Product {}", i + 1))
                .build()
        })
        .collect()
}
```

## Setup and Teardown Utilities

```rust
use std::sync::{Arc, Mutex};

/// Test environment with common mocks
pub struct TestEnvironment {
    pub mock_api: MockApiClient,
    pub mock_db: MockDatabase,
    pub mock_logger: MockLogger,
}

impl TestEnvironment {
    pub fn new() -> Self {
        Self {
            mock_api: create_mock_api_client(),
            mock_db: create_mock_database(),
            mock_logger: create_mock_logger(),
        }
    }
}

/// Run test with timeout
pub async fn with_timeout<F, T>(duration: std::time::Duration, test_fn: F) -> T
where
    F: std::future::Future<Output = T>,
{
    tokio::time::timeout(duration, test_fn)
        .await
        .expect("Test timeout exceeded")
}

/// Run test with mock database connection
pub fn with_test_database<F>(test_fn: F)
where
    F: FnOnce(&MockDatabase),
{
    let mut mock_db = create_mock_database();
    mock_db.connect().expect("Failed to connect to test database");

    test_fn(&mock_db);

    mock_db.disconnect().expect("Failed to disconnect from test database");
}

/// RAII guard for test setup/teardown
pub struct TestGuard<T> {
    resource: Option<T>,
    cleanup: Box<dyn FnOnce(T)>,
}

impl<T> TestGuard<T> {
    pub fn new(resource: T, cleanup: impl FnOnce(T) + 'static) -> Self {
        Self {
            resource: Some(resource),
            cleanup: Box::new(cleanup),
        }
    }

    pub fn get(&self) -> &T {
        self.resource.as_ref().unwrap()
    }

    pub fn get_mut(&mut self) -> &mut T {
        self.resource.as_mut().unwrap()
    }
}

impl<T> Drop for TestGuard<T> {
    fn drop(&mut self) {
        if let Some(resource) = self.resource.take() {
            (self.cleanup)(resource);
        }
    }
}
```

## Usage Examples

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_user_by_id() {
        // Arrange
        let mut env = TestEnvironment::new();
        let test_user = UserBuilder::new()
            .with_id(123)
            .with_name("John Doe")
            .build();

        env.mock_api
            .expect_get()
            .with(eq("/users/123"))
            .returning(move |_| Ok(Response::from_user(&test_user)));

        let service = UserService::new(env.mock_api, env.mock_logger);

        // Act
        let result = service.get_user_by_id(123);

        // Assert
        assert!(result.is_ok());
        let user = result.unwrap();
        assert_eq!(user.id, 123);
        assert_eq!(user.name, "John Doe");
    }

    #[test]
    fn test_create_user() {
        // Arrange
        let mut env = TestEnvironment::new();
        let new_user = UserBuilder::new()
            .with_id(0)
            .with_name("Jane Doe")
            .build();

        let created_user = UserBuilder::new()
            .with_id(456)
            .with_name("Jane Doe")
            .build();

        env.mock_api
            .expect_post()
            .with(eq("/users"), always())
            .returning(move |_, _| Ok(Response::from_user(&created_user)));

        env.mock_logger
            .expect_info()
            .times(1..)
            .returning(|_| ());

        let service = UserService::new(env.mock_api, env.mock_logger);

        // Act
        let result = service.create_user(&new_user);

        // Assert
        assert!(result.is_ok());
        let user = result.unwrap();
        assert_eq!(user.id, 456);
    }

    #[test]
    fn test_get_all_users() {
        // Arrange
        let mut env = TestEnvironment::new();
        let users = build_user_list(3);

        env.mock_api
            .expect_get()
            .with(eq("/users"))
            .returning(move |_| Ok(Response::from_users(&users)));

        let service = UserService::new(env.mock_api, env.mock_logger);

        // Act
        let result = service.get_all_users();

        // Assert
        assert!(result.is_ok());
        let users = result.unwrap();
        assert_eq!(users.len(), 3);
    }

    #[tokio::test]
    async fn test_get_user_with_timeout() {
        // Arrange
        let mut env = TestEnvironment::new();
        let test_user = build_default_user();

        env.mock_api
            .expect_get()
            .returning(move |_| Ok(Response::from_user(&test_user)));

        let service = UserService::new(env.mock_api, env.mock_logger);

        // Act & Assert
        let result = with_timeout(
            std::time::Duration::from_secs(1),
            service.get_user_by_id(1)
        ).await;

        assert!(result.is_ok());
    }

    #[test]
    fn test_with_database() {
        with_test_database(|db| {
            let result = db.query("SELECT * FROM users");
            assert!(result.is_ok());
        });
    }
}
```
