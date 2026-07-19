# Inventory Management API

A RESTful Inventory Management API built with Flask and MySQL. The project provides authentication, role-based authorization, product management, order management, and interactive API documentation using Swagger.

---

## Features

- JWT Authentication
- Refresh Tokens
- Role-Based Access Control (Admin)
- User CRUD Operations
- Product CRUD Operations
- Order CRUD Operations
- Order Item Management
- Product Search
- User Search
- Pagination
- Sorting
- Swagger API Documentation

---

## Tech Stack

- Python
- Flask
- MySQL
- Flask-JWT-Extended
- Flasgger (Swagger)
- bcrypt

---

## Project Structure

```text
project/
│
├── docs/
│   ├── auth/
│   ├── users/
│   ├── products/
│   └── orders/
│
├── routes/
│   ├── users.py
│   ├── products.py
│   └── orders.py
│
├── utils/
│   └── auth.py
│
├── app.py
├── db.py
├── config.py
└── requirements.txt
```

---

## Authentication

Login to receive:

- Access Token
- Refresh Token

Use the access token in Swagger:

```text
Bearer <access_token>
```

---

## API Documentation

After running the application, open:

```text
http://127.0.0.1:5000/apidocs
```

---

## Installation

Clone the repository

```bash
git clone <repository-url>
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

---

## Future Improvements

- Environment variables
- Docker support
- Unit Tests
- Product image uploads
- Password reset
- Email verification

---

## Author

Ali Abbas Mashriqi
