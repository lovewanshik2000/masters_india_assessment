# Discount Campaign Management System

A comprehensive Django-based discount campaign management system with RESTful APIs, JWT authentication, and a modern dashboard interface.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Dashboard Guide](#dashboard-guide)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)

---

## ✨ Features

### Core Functionality
- ✅ **Campaign Management** - Create, update, delete discount campaigns
- ✅ **Customer Management** - Manage customer database
- ✅ **Discount Application** - Apply discounts to orders with validation
- ✅ **Usage Tracking** - Track campaign usage per customer
- ✅ **Budget Management** - Monitor and control campaign budgets

### API Features
- ✅ **RESTful APIs** - Complete CRUD operations
- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Swagger/OpenAPI** - Interactive API documentation
- ✅ **Standardized Responses** - Consistent API response format
- ✅ **Pagination** - Efficient data handling

### Dashboard Features
- ✅ **Modern UI** - Beautiful sidebar-based dashboard
- ✅ **Statistics Cards** - Real-time metrics
- ✅ **Quick Actions** - Fast access to common tasks
- ✅ **Recent Activity** - View latest campaigns and usage
- ✅ **Responsive Design** - Mobile-friendly interface

---

## 🛠 Technology Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: drf-yasg (Swagger/OpenAPI)
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Python**: 3.8+

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
```bash
cd /path/to/project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Load sample data (optional)**
```bash
python manage.py loaddata sample_data.json
```

7. **Run development server**
```bash
python manage.py runserver
```

---

## 🚀 Quick Start

### Access the Application

- **Dashboard**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### Default Login
- **Username**: admin
- **Password**: Password@123

---

## 📁 Project Structure

```
discount_system/
├── campaigns/                 # Main application
│   ├── models.py             # Database models
│   ├── serializers.py        # DRF serializers
│   ├── views.py              # Views and viewsets
│   ├── forms.py              # Django forms
│   ├── urls.py               # Template URLs
│   ├── api_urls.py           # API URLs
│   ├── auth_views.py         # Authentication views
│   ├── pagination.py         # Custom pagination
│   ├── utils.py              # Utility functions
│   ├── admin.py              # Admin configuration
│   └── tests.py              # Test suite
├── discount_system/          # Project settings
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py               # WSGI configuration
├── templates/                # HTML templates
│   ├── base.html             # Base template (navbar)
│   ├── base_sidebar.html     # Sidebar dashboard template
│   ├── campaigns/            # Campaign templates
│   │   ├── dashboard.html    # Dashboard home
│   │   ├── list.html         # Campaign list
│   │   ├── form.html         # Campaign form
│   │   ├── customer_list.html
│   │   ├── customer_form.html
│   │   ├── usage_list.html
│   │   └── apply_discount.html
│   └── registration/         # Auth templates
│       └── login.html
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── SWAGGER_GUIDE.md          # Swagger documentation guide
└── DASHBOARD_SUMMARY.md      # Dashboard features summary
```

---

## 🔌 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "password2": "securepassword"
}
```

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user",
  "password": "password"
}

Response:
{
  "status": true,
  "message": "Login successful",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {...}
  }
}
```

#### Refresh Token
```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Campaign Endpoints

#### List Campaigns
```http
GET /api/campaigns/
Authorization: Bearer <access_token>
```

#### Create Campaign
```http
POST /api/campaigns/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "Black Friday Sale",
  "description": "Special discount for Black Friday",
  "discount_type": "CART",
  "discount_value": "100.00",
  "start_date": "2025-11-25",
  "end_date": "2025-11-30",
  "total_budget": "50000.00",
  "max_transactions_per_customer_per_day": 3,
  "targeted_customers": [1, 2, 3],
  "is_active": true
}
```

#### Update Campaign
```http
PUT /api/campaigns/{id}/
PATCH /api/campaigns/{id}/
Authorization: Bearer <access_token>
```

#### Delete Campaign
```http
DELETE /api/campaigns/{id}/
Authorization: Bearer <access_token>
```

### Customer Endpoints

#### List Customers
```http
GET /api/customers/
Authorization: Bearer <access_token>
```

#### Create Customer
```http
POST /api/customers/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "customer_id": "CUST001",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Discount Operations

#### Preview Discounts
```http
POST /api/discounts/preview/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "customer_id": "CUST001",
  "cart_total": "5000.00",
  "delivery_fee": "500.00"
}

Response:
{
  "status": true,
  "message": "Discounts calculated successfully",
  "data": {
    "customer": {...},
    "applicable_campaigns": [...],
    "total_cart_discount": "200.00",
    "total_delivery_discount": "50.00",
    "final_cart_total": "4800.00",
    "final_delivery_fee": "450.00",
    "final_amount": "5250.00"
  }
}
```

#### Apply Discounts
```http
POST /api/discounts/apply/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "customer_id": "CUST001",
  "cart_total": "5000.00",
  "delivery_fee": "500.00",
  "campaign_ids": [1, 2]
}
```

### Usage Tracking

#### List Usage Records
```http
GET /api/usage/
Authorization: Bearer <access_token>
```

---

## 🎨 Dashboard Guide

### Navigation Structure

The dashboard uses a sidebar layout with the following sections:

#### Main
- **Dashboard** - Overview with statistics and recent activity

#### Management
- **Customers** - View and manage customers
- **Campaigns** - View and manage campaigns

#### Operations
- **Preview Discounts** - Preview discount calculations
- **Apply Discounts** - Apply discounts to orders
- **Usage Records** - View campaign usage history

#### Documentation
- **API Docs (Swagger)** - Interactive API documentation
- **API Docs (ReDoc)** - Alternative API documentation

#### Admin
- **Admin Panel** - Django admin interface (staff only)

### Dashboard Features

#### Statistics Cards
- Total Campaigns (with active count)
- Total Customers
- Total Budget (with consumed amount)
- Total Usage (with today's count)

#### Quick Actions
- Create Campaign
- Add Customer
- Apply Discount
- View Reports

#### Recent Activity
- Recent Campaigns (last 5)
- Recent Usage Records (last 5)

---

## 🗄 Database Schema

### Customer Model
```python
- customer_id: CharField (unique)
- name: CharField
- email: EmailField
- created_at: DateTimeField (auto)
- updated_at: DateTimeField (auto)
```

### Campaign Model
```python
- name: CharField
- description: TextField
- discount_type: CharField (CART/DELIVERY)
- discount_value: DecimalField
- start_date: DateField
- end_date: DateField
- total_budget: DecimalField
- consumed_budget: DecimalField (default: 0)
- max_transactions_per_customer_per_day: IntegerField
- targeted_customers: ManyToManyField(Customer)
- is_active: BooleanField
- created_at: DateTimeField (auto)
- updated_at: DateTimeField (auto)
```

### CampaignUsage Model
```python
- campaign: ForeignKey(Campaign)
- customer: ForeignKey(Customer)
- usage_date: DateField
- usage_count: IntegerField (default: 0)
- created_at: DateTimeField (auto)
- updated_at: DateTimeField (auto)

Unique Together: (campaign, customer, usage_date)
```

---

## 🧪 Testing

### Run Tests
```bash
python manage.py test campaigns
```

### Test Coverage
- Model validation tests
- API endpoint tests
- Authentication tests
- Business logic tests
- Edge case handling

---

## 🚢 Deployment

### Environment Variables

Create a `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgres://user:pass@host:port/dbname
```

### Production Settings

1. **Update settings.py**:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Use PostgreSQL database
   - Configure static files

2. **Collect static files**:
```bash
python manage.py collectstatic
```

3. **Run with Gunicorn**:
```bash
gunicorn discount_system.wsgi:application
```

4. **Use Nginx as reverse proxy**

---

## 📝 API Response Format

All API endpoints return responses in this standardized format:

### Success Response
```json
{
  "status": true,
  "message": "Operation successful",
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "status": false,
  "message": "Error description",
  "data": {
    "field_name": ["Error details"]
  }
}
```

---

## 🔒 Security Features

- JWT token authentication
- CSRF protection
- SQL injection prevention (Django ORM)
- XSS protection
- Password hashing (PBKDF2)
- Permission-based access control

---

## 📞 Support

For issues and questions:
- Check the Swagger documentation at `/swagger/`
- Review the test suite in `campaigns/tests.py`
- Consult Django documentation

---

## 📄 License

This project is proprietary software.

---

## 🙏 Acknowledgments

- Django Framework
- Django REST Framework
- Bootstrap 5
- drf-yasg

---

**Version**: 1.0.0  
**Last Updated**: December 2025
