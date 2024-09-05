import ast
import json
import time
from pprint import pprint

from agents.tester.graph import TestCoderGraph
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI

from models.models import Status, Task

load_dotenv()

if __name__=="__main__":
    #  Example using in you main graph.

    llm = ChatOpenAI(model="gpt-4o-2024-05-13", temperature=0, max_retries=5, streaming=True, seed=4000)
    Coder= TestCoderGraph(llm)
    init_task = Task(task_id='1721664384819-0692c177-61a5-44d2-8cac-b83f51a827df',description='''"work_package_name": "Implement GET Title Endpoint",
    "description": "Implement a GET Title Endpoint in .NET for a Title Requests Microservice adhering to MISMO v3.6 standards.",
    "name": "Title Requests Microservice",
    "language": "C#",
    "restConfig": {
        "server": {
            "sqlDB": "SQL Server",
            "port": "80",
            "resources": [
                {
                    "name": "Title",
                    "allowedMethods": [
                        "GET"
                    ],
                    "fields": {
                        "requestId": {
                            "datatype": "string"
                        },
                        "borrowerDetails": {
                            "datatype": "object",
                            "fields": {
                                "name": {
                                    "datatype": "string"
                                },
                                "ssn": {
                                    "datatype": "string"
                                }
                            }
                        },
                        "propertyDetails": {
                            "datatype": "object",
                            "fields": {
                                "address": {
                                    "datatype": "string"
                                },
                                "city": {
                                    "datatype": "string"
                                },
                                "state": {
                                    "datatype": "string"
                                },
                                "zipCode": {
                                    "datatype": "string"
                                }
                            }
                        },
                        "loanDetails": {
                            "datatype": "object",
                            "fields": {
                                "loanId": {
                                    "datatype": "string"
                                },
                                "amount": {
                                    "datatype": "number"
                                }
                            }
                        },
                        "responseId": {
                            "datatype": "string"
                        },
                        "status": {
                            "datatype": "string"
                        },
                        "titleDetails": {
                            "datatype": "object",
                            "fields": {
                                "titleId": {
                                    "datatype": "string"
                                },
                                "owner": {
                                    "datatype": "string"
                                }
                            }
                        },
                        "errorMessages": {
                            "datatype": "array",
                            "items": {
                                "datatype": "object",
                                "fields": {
                                    "errorCode": {
                                        "datatype": "string"
                                    },
                                    "errorMessage": {
                                        "datatype": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        },
        "framework": "ASP.NET Core"
    },
    "LICENSE_URL": "https://opensource.org/licenses/MIT",
    "LICENSE_TEXT": "MIT License"''',
      task_status=Status.NEW.value, additional_info='', question='', remarks='')

    requirements_doc="""
# Project Requirements Document

## Project Overview

### 1. Project Purpose and Goals
The purpose of this project is to develop a Title Requests Micro-service that adheres to MISMO v3.6 standards. The primary goal is to create a GET REST API service (`get_title`) in .NET that can handle title requests efficiently and accurately. This service will be part of a larger system aimed at streamlining title processing and ensuring compliance with industry standards.

### 2. Main Features or Functionalities
- **GET Title Service**: Implement a RESTful GET API endpoint to handle title requests.
- **MISMO v3.6 Compliance**: Ensure that the service adheres to the MISMO v3.6 standards for data exchange.
- **Data Validation**: Validate incoming requests to ensure they meet the required schema and standards.
- **Error Handling**: Implement robust error handling to manage invalid requests and system errors gracefully.
- **Logging and Monitoring**: Include logging and monitoring features to track the performance and usage of the service.

### 3. Schema Definition Models
To implement this service, the following schema definition models are needed:
- **TitleRequest**: This model will define the structure of the incoming title request, including fields such as `requestId`, `borrowerDetails`, `propertyDetails`, and `loanDetails`.
- **TitleResponse**: This model will define the structure of the response returned by the service, including fields such as `responseId`, `status`, `titleDetails`, and `errorMessages`.
- **ErrorModel**: This model will define the structure for error messages, including fields such as `errorCode` and `errorMessage`.

These models will be defined according to the MISMO v3.6 standards to ensure compliance and interoperability with other systems.

## Architecture

### 1. High-Level Architecture Diagram

```plaintext
+--------------------+        +--------------------+        +--------------------+
|                    |        |                    |        |                    |
|  Client Application| <----> |  API Gateway       | <----> |  Title Requests    |
|                    |        |                    |        |  Microservice      |
+--------------------+        +--------------------+        +--------------------+
                                                      |
                                                      |
                                                      v
                                            +--------------------+
                                            |                    |
                                            |  Database          |
                                            |  (MISMO v3.6)      |
                                            +--------------------+
```

### 2. Key Components, Data Models, and Their Interactions

- **Client Application**: The front-end or other services that will consume the `get_title` API.
- **API Gateway**: Acts as an entry point for all client requests, routing them to the appropriate microservice.
- **Title Requests Microservice**: The core service that handles title requests. It includes the following components:
  - **Controller**: Handles incoming HTTP GET requests for title information.
  - **Service Layer**: Contains the business logic for processing title requests.
  - **Data Access Layer**: Interacts with the database to fetch and store title information.
- **Database**: Stores title request and response data, adhering to MISMO v3.6 standards.

#### Data Models
- **TitleRequest**: Defines the structure of the incoming title request.
  ```json
  {
    "requestId": "string",
    "borrowerDetails": {
      "name": "string",
      "ssn": "string"
    },
    "propertyDetails": {
      "address": "string",
      "city": "string",
      "state": "string",
      "zipCode": "string"
    },
    "loanDetails": {
      "loanId": "string",
      "amount": "number"
    }
  }
  ```
- **TitleResponse**: Defines the structure of the response returned by the service.
  ```json
  {
    "responseId": "string",
    "status": "string",
    "titleDetails": {
      "titleId": "string",
      "owner": "string"
    },
    "errorMessages": [
      {
        "errorCode": "string",
        "errorMessage": "string"
      }
    ]
  }
  ```
- **ErrorModel**: Defines the structure for error messages.
  ```json
  {
    "errorCode": "string",
    "errorMessage": "string"
  }
  ```

### 3. Data Flow Between Services

1. **Client Application** sends a GET request to the **API Gateway**.
2. **API Gateway** routes the request to the **Title Requests Microservice**.
3. **Title Requests Microservice** processes the request:
   - Validates the request against the **TitleRequest** model.
   - Fetches the necessary data from the **Database**.
   - Constructs a **TitleResponse** or **ErrorModel** based on the outcome.
4. **Title Requests Microservice** sends the response back to the **API Gateway**.
5. **API Gateway** forwards the response to the **Client Application**.

### 4. External Integrations or APIs

- **MISMO v3.6 Database**: The microservice will interact with a database that adheres to MISMO v3.6 standards for storing and retrieving title information.
- **Logging and Monitoring Services**: External services for logging and monitoring the performance and usage of the microservice.

### 5. Scalability and Reliability Considerations

- **Scalability**:
  - Use of containerization (e.g., Docker) to deploy the microservice, allowing for easy scaling.
  - Implement auto-scaling policies based on CPU and memory usage.
  - Use a load balancer to distribute incoming requests evenly across multiple instances of the microservice.

- **Reliability**:
  - Implement health checks to monitor the status of the microservice.
  - Use circuit breakers to handle failures gracefully and prevent cascading failures.
  - Ensure data redundancy and backups for the database to prevent data loss.
  - Implement robust error handling and logging to quickly identify and resolve issues.

## Folder Structure

```plaintext
TitleRequestsMicroservice/
├── src/
│   ├── TitleRequests.Api/
│   │   ├── Controllers/
│   │   │   └── TitleController.cs
│   │   ├── Models/
│   │   │   ├── TitleRequest.cs
│   │   │   ├── TitleResponse.cs
│   │   │   └── ErrorModel.cs
│   │   ├── Services/
│   │   │   └── TitleService.cs
│   │   ├── Data/
│   │   │   └── TitleRepository.cs
│   │   ├── Mappings/
│   │   │   └── TitleMappings.cs
│   │   ├── Program.cs
│   │   ├── Startup.cs
│   │   └── appsettings.json
│   ├── TitleRequests.Tests/
│   │   ├── Controllers/
│   │   │   └── TitleControllerTests.cs
│   │   ├── Services/
│   │   │   └── TitleServiceTests.cs
│   │   ├── Data/
│   │   │   └── TitleRepositoryTests.cs
│   │   └── TestHelpers/
│   │       └── MockData.cs
├── logs/
│   └── .gitkeep
├── docker/
│   └── Dockerfile
├── .gitignore
├── README.md
└── LICENSE
```

### Explanation of the Purpose for Each Major Directory

- **src/**: Contains all the source code for the microservice.
  - **TitleRequests.Api/**: The main project directory for the API.
    - **Controllers/**: Contains the controller classes that handle HTTP requests.
    - **Models/**: Contains the data models used in the application, such as `TitleRequest`, `TitleResponse`, and `ErrorModel`.
    - **Services/**: Contains the service classes that implement the business logic.
    - **Data/**: Contains the repository classes that interact with the database.
    - **Mappings/**: Contains mapping configurations for data transformations.
    - **Program.cs**: The entry point of the application.
    - **Startup.cs**: Configures the application services and middleware.
    - **appsettings.json**: Configuration file for application settings.
  - **TitleRequests.Tests/**: Contains all the test code for the microservice.
    - **Controllers/**: Contains unit tests for the controller classes.
    - **Services/**: Contains unit tests for the service classes.
    - **Data/**: Contains unit tests for the repository classes.
    - **TestHelpers/**: Contains helper classes and mock data for testing.
- **logs/**: Directory for storing log files.
- **docker/**: Contains Docker-related files, such as the Dockerfile for containerization.
- **.gitignore**: Specifies files and directories to be ignored by Git.
- **README.md**: Provides an overview and documentation for the project.
- **LICENSE**: Contains the license information for the project.

## Microservice Design

### Title Requests Microservice

1. **Service Name and Primary Responsibility**
   - **Service Name**: Title Requests Microservice
   - **Primary Responsibility**: Handle title requests by providing a GET REST API service that adheres to MISMO v3.6 standards.

2. **Key Endpoints or Functions**
   - **GET /get_title**: Endpoint to handle incoming title requests and return the corresponding title information.

3. **Data Models or Schemas**
   - **TitleRequest**: Defines the structure of the incoming title request.
     ```json
     {
       "requestId": "string",
       "borrowerDetails": {
         "name": "string",
         "ssn": "string"
       },
       "propertyDetails": {
         "address": "string",
         "city": "string",
         "state": "string",
         "zipCode": "string"
       },
       "loanDetails": {
         "loanId": "string",
         "amount": "number"
       }
     }
     ```
   - **TitleResponse**: Defines the structure of the response returned by the service.
     ```json
     {
       "responseId": "string",
       "status": "string",
       "titleDetails": {
         "titleId": "string",
         "owner": "string"
       },
       "errorMessages": [
         {
           "errorCode": "string",
           "errorMessage": "string"
         }
       ]
     }
     ```
   - **ErrorModel**: Defines the structure for error messages.
     ```json
     {
       "errorCode": "string",
       "errorMessage": "string"
     }
     ```

4. **Internal Components or Modules**
   - **Controller**: Handles incoming HTTP GET requests for title information.
   - **Service Layer**: Contains the business logic for processing title requests.
   - **Data Access Layer**: Interacts with the database to fetch and store title information.

5. **Dependencies on Other Services or External Systems**
   - **API Gateway**: Acts as an entry point for all client requests, routing them to the Title Requests Microservice.
   - **Database (MISMO v3.6)**: Stores title request and response data, adhering to MISMO v3.6 standards.
   - **Logging and Monitoring Services**: External services for logging and monitoring the performance and usage of the microservice.

## Tasks

### 1. Define Schema Models

#### Deliverable Name
Define Schema Models

#### Description
Create the schema definition models for TitleRequest, TitleResponse, and ErrorModel according to MISMO v3.6 standards.

#### Technical Requirements
- **TitleRequest Model**: Must include fields such as `requestId`, `borrowerDetails`, `propertyDetails`, and `loanDetails`.
- **TitleResponse Model**: Must include fields such as `responseId`, `status`, `titleDetails`, and `errorMessages`.
- **ErrorModel**: Must include fields such as `errorCode` and `errorMessage`.

### 2. Implement GET Title Endpoint

#### Deliverable Name
Implement GET Title Endpoint

#### Description
Develop the GET /get_title endpoint to handle incoming title requests and return the corresponding title information.

#### Technical Requirements
- **Controller**: Create a controller to handle HTTP GET requests.
- **Service Layer**: Implement business logic for processing title requests.
- **Data Access Layer**: Interact with the database to fetch and store title information.
- **Validation**: Validate incoming requests against the TitleRequest model.
- **Response Construction**: Construct a TitleResponse or ErrorModel based on the outcome.

### 3. Database Integration

#### Deliverable Name
Database Integration

#### Description
Integrate the microservice with a database that adheres to MISMO v3.6 standards for storing and retrieving title information.

#### Technical Requirements
- **Database Schema**: Define the database schema according to MISMO v3.6 standards.
- **Data Access Layer**: Implement methods to interact with the database.
- **Data Validation**: Ensure data integrity and compliance with MISMO v3.6.

### 4. Error Handling

#### Deliverable Name
Error Handling

#### Description
Implement robust error handling to manage invalid requests and system errors gracefully.

#### Technical Requirements
- **ErrorModel**: Use the ErrorModel to structure error messages.
- **Exception Handling**: Implement exception handling in the service layer.
- **Error Logging**: Log errors for monitoring and debugging purposes.

### 5. Logging and Monitoring

#### Deliverable Name
Logging and Monitoring

#### Description
Include logging and monitoring features to track the performance and usage of the service.

#### Technical Requirements
- **Logging**: Implement logging for incoming requests, responses, and errors.
- **Monitoring**: Integrate with external monitoring services to track performance metrics.
- **Health Checks**: Implement health checks to monitor the status of the microservice.

### 6. API Gateway Integration

#### Deliverable Name
API Gateway Integration

#### Description
Integrate the microservice with the API Gateway to route client requests to the appropriate service.

#### Technical Requirements
- **Routing**: Configure the API Gateway to route GET /get_title requests to the Title Requests Microservice.
- **Security**: Implement security measures such as authentication and rate limiting.

### 7. Scalability and Reliability

#### Deliverable Name
Scalability and Reliability

#### Description
Implement scalability and reliability features to ensure the microservice can handle varying loads and remain operational.

#### Technical Requirements
- **Containerization**: Use Docker to containerize the microservice.
- **Auto-Scaling**: Implement auto-scaling policies based on CPU and memory usage.
- **Load Balancing**: Use a load balancer to distribute incoming requests evenly.
- **Circuit Breakers**: Implement circuit breakers to handle failures gracefully.
- **Data Redundancy**: Ensure data redundancy and backups for the database.

## Standards

### 1. 12-Factor Application Standards

1. **Codebase**: Maintain a single codebase tracked in version control (e.g., Git) with multiple deploys.
2. **Dependencies**: Explicitly declare and isolate dependencies using a package manager (e.g., NuGet for .NET).
3. **Config**: Store configuration in the environment. Use environment variables for configuration settings.
4. **Backing Services**: Treat backing services (e.g., databases, message queues) as attached resources.
5. **Build, Release, Run**: Strictly separate build and run stages. Use CI/CD pipelines for automated builds and deployments.
6. **Processes**: Execute the app as one or more stateless processes. Store state in a backing service.
7. **Port Binding**: Export services via port binding. The microservice should listen on a port for HTTP requests.
8. **Concurrency**: Scale out via the process model. Use container orchestration tools (e.g., Kubernetes) for scaling.
9. **Disposability**: Maximize robustness with fast startup and graceful shutdown. Implement health checks and readiness probes.
10. **Dev/Prod Parity**: Keep development, staging, and production as similar as possible.
11. **Logs**: Treat logs as event streams. Use centralized logging solutions (e.g., ELK stack).
12. **Admin Processes**: Run admin/management tasks as one-off processes.

### 2. Clean Code Standards

- **Meaningful Names**: Use descriptive and meaningful names for variables, methods, and classes.
- **Single Responsibility Principle**: Each class and method should have a single responsibility.
- **DRY (Don't Repeat Yourself)**: Avoid code duplication by reusing code where possible.
- **KISS (Keep It Simple, Stupid)**: Write simple and straightforward code.
- **YAGNI (You Aren't Gonna Need It)**: Don't add functionality until it is necessary.
- **SOLID Principles**: Follow SOLID principles for object-oriented design.
- **Code Reviews**: Conduct regular code reviews to maintain code quality.

### 3. Code Commenting Standards

- **Method Comments**: Provide comments for each method explaining its purpose, parameters, and return values.
- **Inline Comments**: Use inline comments to explain complex logic or calculations.
- **TODO Comments**: Use TODO comments to indicate areas of the code that need further work or improvement.
- **Consistent Style**: Follow a consistent commenting style throughout the codebase.

### 4. Programming Language Specific Standards

- **.NET Naming Conventions**: Follow .NET naming conventions for classes, methods, and variables.
- **Exception Handling**: Use try-catch blocks for exception handling and provide meaningful error messages.
- **Async/Await**: Use async/await for asynchronous programming to improve performance.
- **LINQ**: Use LINQ for querying collections in a readable and efficient manner.
- **Unit Testing**: Write unit tests using a testing framework like xUnit or NUnit.

### 5. User Requested Standards

- **MISMO v3.6 Compliance**: Ensure all schema models and database schemas adhere to MISMO v3.6 standards.
- **RESTful API Design**: Follow RESTful principles for designing the GET /get_title endpoint.
- **Security**: Implement security measures such as authentication, authorization, and data encryption.
- **Scalability**: Ensure the microservice can scale horizontally to handle varying loads.
- **Monitoring and Logging**: Implement robust logging and monitoring to track the performance and usage of the service.

## Implementation Details

### 1. List of Required Source Files

```plaintext
TitleRequestsMicroservice/
├── src/
│   ├── TitleRequests.Api/
│   │   ├── Controllers/
│   │   │   └── TitleController.cs
│   │   ├── Models/
│   │   │   ├── TitleRequest.cs
│   │   │   ├── TitleResponse.cs
│   │   │   └── ErrorModel.cs
│   │   ├── Services/
│   │   │   └── TitleService.cs
│   │   ├── Data/
│   │   │   └── TitleRepository.cs
│   │   ├── Mappings/
│   │   │   └── TitleMappings.cs
│   │   ├── Program.cs
│   │   ├── Startup.cs
│   │   └── appsettings.json
│   ├── TitleRequests.Tests/
│   │   ├── Controllers/
│   │   │   └── TitleControllerTests.cs
│   │   ├── Services/
│   │   │   └── TitleServiceTests.cs
│   │   ├── Data/
│   │   │   └── TitleRepositoryTests.cs
│   │   └── TestHelpers/
│   │       └── MockData.cs
├── logs/
│   └── .gitkeep
├── docker/
│   └── Dockerfile
├── .gitignore
├── README.md
└── LICENSE
```

### 2. List of Configuration Files

- **appsettings.json**: Configuration file for application settings.
- **Dockerfile**: Configuration file for Docker containerization.
- **.gitignore**: Specifies files and directories to be ignored by Git.
- **.dockerignore**: Specifies files and directories to be ignored by Docker.

### 3. List of Unit Test Approach and Files

#### Unit Test Approach

- **Controllers**: Test the endpoints to ensure they handle requests and responses correctly.
- **Services**: Test the business logic to ensure it processes data correctly.
- **Data**: Test the repository classes to ensure they interact with the database correctly.
- **TestHelpers**: Provide mock data and helper functions for testing.

#### Unit Test Files

```plaintext
TitleRequestsMicroservice/
├── src/
│   ├── TitleRequests.Tests/
│   │   ├── Controllers/
│   │   │   └── TitleControllerTests.cs
│   │   ├── Services/
│   │   │   └── TitleServiceTests.cs
│   │   ├── Data/
│   │   │   └── TitleRepositoryTests.cs
│   │   └── TestHelpers/
│   │       └── MockData.cs
```

### 4. OpenAPI Specification (Sample Structure in YAML)

```yaml
openapi: 3.0.0
info:
  title: Title Requests API
  version: 1.0.0
paths:
  /get_title:
    get:
      summary: Get title information
      parameters:
        - in: query
          name: requestId
          schema:
            type: string
          required: true
          description: The ID of the title request
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TitleResponse'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorModel'
components:
  schemas:
    TitleRequest:
      type: object
      properties:
        requestId:
          type: string
        borrowerDetails:
          type: object
          properties:
            name:
              type: string
            ssn:
              type: string
        propertyDetails:
          type: object
          properties:
            address:
              type: string
            city:
              type: string
            state:
              type: string
            zipCode:
              type: string
        loanDetails:
          type: object
          properties:
            loanId:
              type: string
            amount:
              type: number
    TitleResponse:
      type: object
      properties:
        responseId:
          type: string
        status:
          type: string
        titleDetails:
          type: object
          properties:
            titleId:
              type: string
            owner:
              type: string
        errorMessages:
          type: array
          items:
            $ref: '#/components/schemas/ErrorModel'
    ErrorModel:
      type: object
      properties:
        errorCode:
          type: string
        errorMessage:
          type: string
```

### 5. Dependency Management

#### Package Manager

- **NuGet**: For managing .NET dependencies.

#### Sample File (packages.config)

```xml
<?xml version="1.0" encoding="utf-8"?>
<packages>
  <package id="Microsoft.AspNetCore.App" version="2.1.1" targetFramework="netcoreapp2.1" />
  <package id="Microsoft.EntityFrameworkCore" version="2.1.1" targetFramework="netcoreapp2.1" />
  <package id="Moq" version="4.10.1" targetFramework="netcoreapp2.1" />
  <package id="xunit" version="2.4.1" targetFramework="netcoreapp2.1" />
</packages>
```

### 6. Dockerfile Contents

```dockerfile
# Use the official .NET Core SDK image
FROM mcr.microsoft.com/dotnet/core/sdk:2.1 AS build
WORKDIR /app

# Copy the project files
COPY . ./

# Restore dependencies
RUN dotnet restore

# Build the project
RUN dotnet publish -c Release -o out

# Use the official .NET Core runtime image
FROM mcr.microsoft.com/dotnet/core/aspnet:2.1 AS runtime
WORKDIR /app
COPY --from=build /app/out .

# Expose the port the app runs on
EXPOSE 80

# Run the application
ENTRYPOINT ["dotnet", "TitleRequests.Api.dll"]
```

### 7. Contents for .dockerignore and .gitignore Files

#### .dockerignore

```plaintext
**/.classpath
**/.dockerignore
**/.git
**/.gitignore
**/.project
**/.settings
**/.toolstarget
**/*.md
**/bin
**/obj
```

#### .gitignore

```plaintext
# Ignore Visual Studio temporary files, build results, and
# files generated by popular Visual Studio add-ons.

# User-specific files
*.rsuser
*.suo
*.user
*.userosscache
*.sln.docstates

# User-specific files (Mono Auto Generated)
mono_crash.*

# User-specific files (VSCode)
.vscode/*

# Mono auto generated files
mono_crash.*

# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bin/
obj/

# Uncomment if you have tasks that create the project's static files in wwwroot
#wwwroot/

# Ignore Docker files
**/Dockerfile
**/docker-compose*
**/.dockerignore

# Ignore logs
logs/
*.log

# Ignore .NET Core project files
project.lock.json
project.fragment.lock.json
artifacts/

# Ignore NuGet packages
*.nupkg

# Ignore build output
*.dll
*.exe
*.app
*.so
*.dylib
*.pdb
*.mdb

# Ignore publish output
*.publish.xml

# Ignore npm packages
node_modules/

# Ignore yarn packages
yarn.lock

# Ignore JetBrains Rider project files
.idea/
*.sln.iml

# Ignore Rider's workspace.xml
.idea/workspace.xml

# Ignore Rider's tasks.xml
.idea/tasks.xml

# Ignore Rider's dictionaries
.idea/dictionaries

# Ignore Rider's vcs.xml
.idea/vcs.xml

# Ignore Rider's modules.xml
.idea/modules.xml


## License and Legal Considerations

This project should use the following license:

```
This code base copyrights belong to XYZ
```"""
    inputqh= {"generated_project_path": "/home/pranay/Desktop/Generatedfiles/latest/2024-07-29_11-02-38-752576",
            "license_text": "This code base copyrights belong to XYZ",
            "license_url": "https://raw.githubusercontent.com/intelops/tarian-detector/8a4ff75fe31c4ffcef2db077e67a36a067f1437b/LICENSE",
            "project_name": "TitleRequestsMicroservice",
            "project_folder_structure": "## Folder Structure\n\n```plaintext\nTitleRequestsMicroservice/\n├── src/\n│   ├── TitleRequests.Api/\n│   │   ├── Controllers/\n│   │   ├── Models/\n│   │   ├── Services/\n│   │   ├── DataAccess/\n│   │   ├── Migrations/\n│   │   ├── Program.cs\n│   │   ├── Startup.cs\n│   │   └── appsettings.json\n│   ├── TitleRequests.Common/\n│   │   ├── Logging/\n│   │   ├── Monitoring/\n│   │   └── Utilities/\n│   └── TitleRequests.Tests/\n│       ├── UnitTests/\n│       ├── IntegrationTests/\n│       └── TestSettings.json\n├── docs/\n│   ├── Architecture/\n│   ├── Requirements/\n│   └── README.md\n├── scripts/\n│   ├── build.sh\n│   ├── deploy.sh\n│   └── test.sh\n├── .gitignore\n├── LICENSE\n└── README.md\n```\n\n### Explanation of the Purpose for Each Major Directory\n\n- **src/**: Contains all the source code for the microservice.\n  - **TitleRequests.Api/**: The main project directory for the Title Requests Microservice.\n    - **Controllers/**: Contains the API controllers that handle HTTP requests.\n    - **Models/**: Contains the data models such as `TitleRequest`, `TitleResponse`, and `ErrorModel`.\n    - **Services/**: Contains the business logic for processing title requests.\n    - **DataAccess/**: Contains the data access layer for interacting with the database.\n    - **Migrations/**: Contains database migration files.\n    - **Program.cs**: The entry point of the application.\n    - **Startup.cs**: Configures the application services and middleware.\n    - **appsettings.json**: Configuration file for application settings.\n  - **TitleRequests.Common/**: Contains common or shared code that can be used across multiple projects.\n    - **Logging/**: Contains logging-related utilities and configurations.\n    - **Monitoring/**: Contains monitoring-related utilities and configurations.\n    - **Utilities/**: Contains general utility classes and methods.\n  - **TitleRequests.Tests/**: Contains all test projects.\n    - **UnitTests/**: Contains unit tests for the microservice.\n    - **IntegrationTests/**: Contains integration tests for the microservice.\n    - **TestSettings.json**: Configuration file for test settings.\n- **docs/**: Contains documentation related to the project.\n  - **Architecture/**: Contains architecture-related documentation.\n  - **Requirements/**: Contains requirements-related documentation.\n  - **README.md**: The main readme file for the documentation.\n- **scripts/**: Contains scripts for building, deploying, and testing the microservice.\n  - **build.sh**: Script for building the project.\n  - **deploy.sh**: Script for deploying the project.\n  - **test.sh**: Script for running tests.\n- **.gitignore**: Specifies files and directories to be ignored by Git.\n- **LICENSE**: Contains the license information for the project.\n- **README.md**: The main readme file for the project.",
            "requirements_overview": requirements_doc, 
            "current_task":init_task ,
            "additional_info":"",
            "question":"", 
            "remarks": "",
            "work_package":"""{
    "work_package_name": "Install .NET SDK",
    "description": "Initialize a new .NET project for the Title Requests Microservice. Set up the project structure with folders for Controllers, Services, Repositories, Models, and Validators. Configure the project to use MongoDB.",
    "name": "Project Setup",
    "language": "C#",
    "restConfig": {
        "server": {
            "DB": "MongoDB",
            "uri_string": "mongodb://localhost:27017/<database name>",
            "port": "80",
            "resources": [
                {
                    "name": "TitleRequest",
                    "allowedMethods": [
                        "GET"
                    ],
                    "fields": {
                        "requestId": {
                            "datatype": "string"
                        },
                        "requestDate": {
                            "datatype": "string",
                            "format": "date-time"
                        },
                        "propertyDetails": {
                            "datatype": "object",
                            "fields": {
                                "address": {
                                    "datatype": "string"
                                },
                                "city": {
                                    "datatype": "string"
                                },
                                "state": {
                                    "datatype": "string"
                                },
                                "zipCode": {
                                    "datatype": "string"
                                }
                            }
                        },
                        "requesterDetails": {
                            "datatype": "object",
                            "fields": {
                                "name": {
                                    "datatype": "string"
                                },
                                "contact": {
                                    "datatype": "string"
                                }
                            }
                        }
                    }
                },
                {
                    "name": "TitleResponse",
                    "allowedMethods": [
                        "GET"
                    ],
                    "fields": {
                        "responseId": {
                            "datatype": "string"
                        },
                        "responseDate": {
                            "datatype": "string",
                            "format": "date-time"
                        },
                        "titleDetails": {
                            "datatype": "object",
                            "fields": {
                                "titleId": {
                                    "datatype": "string"
                                },
                                "titleStatus": {
                                    "datatype": "string"
                                },
                                "issueDate": {
                                    "datatype": "string",
                                    "format": "date-time"
                                }
                            }
                        }
                    }
                }
            ]
        },
        "framework": ".NET 5.0"
    },
    "LICENSE_URL": "https://opensource.org/licenses/Apache-2.0",
    "LICENSE_TEXT": "SPDX-License-Identifier: Apache-2.0\nCopyright 2024 Authors of CRBE & the Organization created CRBE"
}"""}
    


    # with open("/home/pranay/Desktop/Generatedfiles/latest/new_file.json","r") as json_file:
    #     f=json.load(json_file)
    
#     planner_thread_id = "3"
#     Planner = PlannerWorkFlow(llm=llm, thread_id=planner_thread_id)
    # result= Coder.app.invoke(inputqh)

    llm=OllamaLLM(model="stablelm2:1.6b")
    response=llm.invoke("tell me a joke ")
    print(response)
    # pprint(result)
