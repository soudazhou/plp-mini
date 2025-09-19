# Research: LegalAnalytics Mini Technology Decisions

## FastAPI vs Spring Boot (Backend Framework)

**Decision**: FastAPI for Python backend
**Rationale**:
- Automatic OpenAPI documentation generation (similar to Spring Boot Actuator but built-in)
- Native async/await support for better performance under load
- Type hints integration provides compile-time safety similar to Java
- Dependency injection system comparable to Spring's IoC container
- Pydantic models for automatic request/response validation (similar to Bean Validation)

**Alternatives Considered**:
- Django: Too heavyweight for MVP, includes ORM/admin that we don't need
- Flask: Requires too many additional libraries, less opinionated than Spring Boot

**Java/Go Comparison Notes**:
- FastAPI decorators (@app.get) vs Spring @RestController/@GetMapping
- Pydantic models vs Java DTOs with validation annotations
- Async request handling vs Spring WebFlux reactive streams

## SQLAlchemy vs JPA/Hibernate (ORM)

**Decision**: SQLAlchemy Core + ORM for database operations
**Rationale**:
- Declarative model definition similar to JPA @Entity classes
- Session management comparable to JPA EntityManager
- Query language (SQLAlchemy Query API) similar to JPQL/Criteria API
- Migration support (Alembic) comparable to Flyway/Liquibase
- Both lazy and eager loading strategies available

**Alternatives Considered**:
- Raw SQL with psycopg2: Too low-level for educational purposes
- Django ORM: Tied to Django framework

**Java/Go Comparison Notes**:
- SQLAlchemy Session vs JPA EntityManager lifecycle
- relationship() definitions vs @OneToMany/@ManyToOne annotations
- query() methods vs JPQL/Criteria API syntax differences

## Angular vs Traditional Java Web (Frontend Framework)

**Decision**: Angular 15+ with TypeScript
**Rationale**:
- Component-based architecture provides clear separation of concerns
- TypeScript strong typing familiar to Java developers
- Dependency injection system similar to Spring
- HTTP client service comparable to RestTemplate/WebClient usage patterns
- Reactive forms provide client-side validation similar to server-side validation

**Alternatives Considered**:
- React: Less opinionated, requires more configuration decisions
- Vue: Smaller learning curve but less enterprise-focused
- Server-side rendering (Thymeleaf-style): Not part of Pirical stack

**Java/Go Comparison Notes**:
- Angular services vs Spring @Service components
- Component lifecycle hooks vs servlet lifecycle methods
- Observable/RxJS patterns vs Java CompletableFuture/reactive streams

## PostgreSQL vs Other RDBMS (Database)

**Decision**: PostgreSQL 14+
**Rationale**:
- ACID compliance and mature ecosystem
- JSON/JSONB support for flexible data (useful for time entry metadata)
- Full-text search capabilities complement Elasticsearch
- Excellent integration with SQLAlchemy
- Industry standard for web applications

**Alternatives Considered**:
- MySQL: Less advanced features, weaker JSON support
- SQLite: Not suitable for production deployment
- Oracle: Licensing costs, not part of Pirical stack

**Java/Go Comparison Notes**:
- JDBC connection patterns vs SQLAlchemy connection pooling
- PostgreSQL-specific features vs generic SQL portability concerns

## Elasticsearch vs Lucene/Solr (Search Engine)

**Decision**: Elasticsearch 8.x with official Python client
**Rationale**:
- RESTful API simplifies integration compared to embedded Lucene
- Built-in aggregations for dashboard metrics
- Real-time indexing suitable for employee search
- JSON-based queries familiar from NoSQL background
- Horizontal scaling capabilities

**Alternatives Considered**:
- Apache Solr: More complex configuration, less modern API
- PostgreSQL full-text search: Sufficient for MVP but limited scalability
- Embedded Lucene: Requires deeper indexing knowledge

**Java/Go Comparison Notes**:
- Elasticsearch REST client vs Lucene IndexWriter/IndexSearcher
- JSON query DSL vs Lucene Query parser syntax
- Document indexing patterns vs traditional search index management

## AWS Services Integration (Cloud Infrastructure)

**Decision**: Hybrid approach - Local simulation with AWS SDK patterns
**Rationale**:
- **Local Development**: Use LocalStack/MinIO for S3, Redis for SQS/SNS simulation
- **Production Pattern**: Maintain boto3 SDK usage for easy AWS migration
- **Learning Value**: Demonstrate AWS patterns without requiring real account
- **Cost Effective**: Zero AWS costs during development and learning

**Local AWS Simulation Stack**:
- **S3 Alternative**: MinIO (S3-compatible object storage)
- **SQS Alternative**: Redis with Celery for async job processing
- **SNS Alternative**: Local SMTP server or console notifications
- **Secrets Manager**: Environment variables with python-dotenv
- **Deployment**: Docker Compose instead of EC2

**Implementation Strategy**:
```python
# AWS-like interface but local backends
class LocalAWSService:
    def __init__(self, use_local=True):
        if use_local:
            self.s3 = MinIOClient()  # Local S3-compatible storage
            self.queue = CeleryQueue()  # Redis-backed queuing
            self.notifications = ConsoleNotifier()  # Local notifications
        else:
            self.s3 = boto3.client('s3')  # Real AWS when available
            self.queue = boto3.client('sqs')
            self.notifications = boto3.client('sns')
```

**Java/Go Comparison Notes**:
- boto3 patterns vs AWS Java SDK v2 (same interface, different backends)
- Configuration switching (local vs cloud) similar to Spring profiles
- Queue processing patterns comparable to JMS with ActiveMQ/RabbitMQ
- Object storage abstraction similar to Java NIO.2 with different providers

## Development Tools & Testing (Supporting Technologies)

**Decision**: pytest (backend), Jest/Jasmine (frontend), Docker containers
**Rationale**:
- pytest fixtures provide setup/teardown similar to JUnit @Before/@After
- Jest async testing compatible with Angular's testing utilities
- Docker containers provide consistent deployment vs JAR files
- docker-compose for local development vs embedded servers

**Alternatives Considered**:
- unittest (Python): Less feature-rich than pytest
- Protractor: Deprecated in favor of Jest for Angular
- Virtual machines: Heavier than containers

**Java/Go Comparison Notes**:
- pytest parametrized tests vs JUnit @ParameterizedTest
- Docker multi-stage builds vs Maven/Gradle build plugins
- Container orchestration vs JAR deployment strategies

## Learning Documentation Strategy

**Decision**: Inline comments + README_LEARNING.md files + comparative analysis
**Rationale**:
- Header comments in every file explaining purpose and Java/Go equivalents
- Dedicated learning files for each major technology component
- Side-by-side code examples showing pattern differences
- Performance and memory usage notes where significantly different

**Key Comparison Areas**:
- Type system differences (dynamic vs static typing implications)
- Memory management patterns (GC vs manual management differences)
- Concurrency models (async/await vs threads vs goroutines)
- Package management (pip/npm vs Maven/go mod)
- Error handling strategies (exceptions vs error returns)

## Implementation Phase Strategy

**Decision**: Incremental development with working deployments at each phase
**Rationale**:
- Phase 1: Basic CRUD demonstrates core FastAPI + SQLAlchemy patterns
- Phase 2: Frontend integration shows full-stack communication patterns
- Phase 3: File processing demonstrates async operations and cloud integration
- Phase 4: Search integration shows NoSQL/search engine patterns
- Phase 5: Full AWS deployment demonstrates production readiness

Each phase produces a working, deployable application with comprehensive learning documentation.