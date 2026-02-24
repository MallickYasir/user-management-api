# FastAPI MySQL User Management API

A secure, production-ready REST API built with **FastAPI**, **SQLModel**, and **MySQL**. It features JWT authentication, role-based access control, and full CRUD operations for users and items.

## Features
- 🔐 **JWT Authentication**: Secure login and registration with password hashing (Bcrypt).
- 👤 **User Management**: Register, login, and profile management.
- 📦 **Item CRUD**: Create, Read, Update, Delete items linked to specific users.
- 🛡️ **Authorization**: Users can only modify their own items; Admins can view all users.
- 🗄️ **Async Database**: Built with `sqlmodel` and `asyncmy` for high performance.
- 📜 **Auto Documentation**: Interactive API docs generated automatically at `/docs`.

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: MySQL (via SQLModel & asyncmy)
- **Security**: Python-Jose (JWT), Passlib (Password Hashing)
- **Environment**: python-dotenv

##  Quick Start

### 1. Clone the repository
```bash
git clone <https://github.com/MallickYasir/user-management-api>
cd user-management-apicls
