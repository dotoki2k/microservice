## Desgin

![image.png](./workflow.png)

## Technology Using:

- Python
- FastAPI
- JWT
- Postgres
- Docker

## Component:

Currently, this project contains 4 services:

- Api Gateway
- User service
- Product service
- Order service

With a separate function, simulate an e-commerce project.

### API Gateway:

The API Gateway is responsible for managing:

- Request routing.
- Authentication & Authorization
- Rate Limiting
- ..

### User Service:

The User Service is responsible for managing all user-related functionalities, such as creating and storing user information. Additionally, it handles token generation for authentication purposes on the Gateway API.

### Product Service:

The Product Service is responsible for managing all product-related functionalities, such as creating and storing product information.

### Order Service:

The Order Service is responsible for managing all order-related functionalities, such as creating and storing order information.