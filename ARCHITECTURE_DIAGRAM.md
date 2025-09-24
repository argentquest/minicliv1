# WhisperCode Architecture Diagram

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Tier"
        A[React Frontend<br/>web1/]
        B[React Components<br/>TypeScript + Vite]
        C[API Client<br/>web1/src/api.ts]
    end

    subgraph "API Tier"
        D[FastAPI Server<br/>fastapi_server.py]
        E[REST API Endpoints<br/>web_backend/api.py]
        F[Pydantic Models<br/>web_backend/schemas.py]
        G[CORS Middleware]
    end

    subgraph "Business Logic Tier"
        H[Conversation Service<br/>web_backend/services/conversation_service.py]
        I[File Service<br/>web_backend/services/file_service.py]
        J[Settings Service<br/>web_backend/services/settings_service.py]
        K[System Message Service<br/>web_backend/services/system_service.py]
    end

    subgraph "Core Processing"
        L[AI Processing<br/>common/ai.py]
        M[File Scanners<br/>common/file_scanner.py<br/>common/lazy_file_scanner.py]
        N[App State<br/>common/models.py]
        O[Environment Manager<br/>common/env_manager.py]
    end

    subgraph "AI Providers"
        P[OpenRouter Provider<br/>providers/openrouter_provider.py]
        Q[Custom Providers<br/>providers/*.py]
    end

    subgraph "Data Layer"
        R[JSON Files<br/>Persistence<br/>file_lock.py]
        S[Environment Variables<br/>.env files]
    end

    subgraph "Utilities"
        T[Logger<br/>common/logger.py]
        U[Security Utilities<br/>security_utils.py]
        V[Pattern Matcher<br/>pattern_matcher.py]
    end

    A --> C
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    E --> I
    E --> J
    E --> K
    H --> L
    H --> M
    H --> N
    H --> O
    I --> M
    J --> O
    K --> O
    L --> P
    L --> Q
    H --> R
    J --> S
    L --> T
    L --> U
    L --> V
    I --> T
    J --> T
    K --> T

    style A fill:#4CAF50,stroke:#388E3C,color:white
    style D fill:#2196F3,stroke:#0D47A1,color:white
    style L fill:#FF9800,stroke:#EF6C00,color:white
    style P fill:#9C27B0,stroke:#4A148C,color:white
```

## React Frontend Architecture

```mermaid
graph TD
    subgraph "React Application"
        A[App.tsx<br/>Main Component]
        B[ThemeProvider<br/>theme management]
        C[Router<br/>navigation]
    end

    subgraph "UI Components"
        D[Header Component]
        E[Chat Interface<br/>Conversation UI]
        F[File Tree<br/>Directory browsing]
        G[Settings Panel<br/>Configuration]
        H[Code Preview<br/>File content display]
    end

    subgraph "State Management"
        I[React State Hooks]
        J[Context API]
        K[Conversation State]
    end

    subgraph "API Integration"
        L[API Client<br/>api.ts]
        M[HTTP Requests<br/>axios/fetch]
        N[Response Handling]
    end

    subgraph "UI Libraries"
        O[React-Bootstrap<br/>UI Components]
        P[React-Markdown<br/>Markdown rendering]
        Q[Prism.js<br/>Code syntax highlighting]
    end

    A --> B
    A --> C
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H

    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    I --> J
    J --> K

    E --> L
    F --> L
    G --> L
    L --> M
    M --> N

    D --> O
    E --> O
    F --> O
    G --> O
    H --> O
    E --> P
    H --> Q

    style A fill:#4CAF50,stroke:#388E3C,color:white
    style D fill:#8BC34A,stroke:#558B2F,color:white
    style L fill:#00BCD4,stroke:#006064,color:white
    style O fill:#FFC107,stroke:#FF8F00,color:white
```

## FastAPI Backend Architecture

```mermaid
graph TB
    subgraph "FastAPI Application"
        A[FastAPI App<br/>fastapi_server.py]
        B[Router Mounting<br/>web_backend/api.py]
        C[CORS Middleware]
        D[Pydantic Validation]
    end

    subgraph "API Endpoints"
        E[Conversation Endpoints<br/>/conversations/*]
        F[File Management<br/>/files/*]
        G[Settings Endpoints<br/>/settings/*]
        H[System Messages<br/>/system-messages/*]
        I[Metadata Endpoints<br/>/meta/*]
    end

    subgraph "Service Layer"
        J[Conversation Service<br/>Conversation management]
        K[File Service<br/>File scanning & reading]
        L[Settings Service<br/>Configuration management]
        M[System Message Service<br/>Expert mode management]
    end

    subgraph "Business Logic"
        N[Conversation Manager<br/>Session handling]
        O[File Scanner<br/>Codebase analysis]
        P[Environment Handler<br/>Config management]
        Q[Model Manager<br/>State management]
    end

    subgraph "Core Modules"
        R[AI Processor<br/>common/ai.py]
        S[File Utilities<br/>common/file_scanner.py]
        T[Models<br/>common/models.py]
        U[Environment<br/>common/env_manager.py]
    end

    A --> B
    A --> C
    A --> D
    B --> E
    B --> F
    B --> G
    B --> H
    B --> I
    E --> J
    F --> K
    G --> L
    H --> M
    J --> N
    J --> R
    K --> O
    L --> P
    M --> P
    N --> T
    O --> S
    P --> U
    Q --> T

    style A fill:#2196F3,stroke:#0D47A1,color:white
    style E fill:#64B5F6,stroke:#1565C0,color:white
    style J fill:#1E88E5,stroke:#0D47A1,color:white
    style R fill:#FF9800,stroke:#EF6C00,color:white
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User (React UI)
    participant A as API Client
    participant F as FastAPI Server
    participant S as Services
    participant C as Core Components
    participant AI as AI Provider
    participant FS as File Scanner
    participant DB as Data Storage

    U->>A: Request (e.g., analyze codebase)
    A->>F: HTTP Request to API
    F->>S: Process request via services
    S->>C: Core processing
    C->>FS: Scan files
    FS-->>C: File content
    C->>AI: Send to AI provider
    AI-->>C: AI response
    C-->>S: Processed response
    S-->>F: API response
    F-->>A: HTTP response
    A-->>U: Display results
```

## Component Interaction Overview

The WhisperCode application follows a modern three-tier architecture:

1. **Presentation Layer** (React):
   - Provides intuitive user interface for code analysis
   - Handles user interactions and displays results
   - Manages client-side state and UI components

2. **Application Layer** (FastAPI):
   - Exposes REST API endpoints for all functionality
   - Handles request/response validation and routing
   - Orchestrates business logic through services
   - Manages security and authentication

3. **Data Layer** (Core & Providers):
   - Processes codebases and manages file operations
   - Integrates with multiple AI providers
   - Handles data persistence and configuration
   - Manages conversation history and context