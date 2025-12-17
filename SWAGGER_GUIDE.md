# Swagger API Documentation

## Overview
Swagger/OpenAPI documentation has been added to the Discount Campaign Management API using `drf-yasg`.

## Accessing Swagger UI

### Swagger UI (Interactive)
```
http://localhost:8000/swagger/
```
- Interactive API documentation
- Try out API endpoints directly from the browser
- View request/response schemas
- Test authentication

### ReDoc (Alternative UI)
```
http://localhost:8000/redoc/
```
- Clean, responsive documentation
- Better for reading and sharing
- Three-panel design

### OpenAPI Schema (JSON)
```
http://localhost:8000/swagger.json/
```
- Raw OpenAPI 2.0 schema
- Use for code generation tools
- Import into Postman, Insomnia, etc.

---

## Available API Endpoints

### Customers
- `GET /api/customers/` - List all customers
- `POST /api/customers/` - Create a new customer
- `GET /api/customers/{customer_id}/` - Get customer details
- `PUT /api/customers/{customer_id}/` - Update customer
- `PATCH /api/customers/{customer_id}/` - Partial update customer
- `DELETE /api/customers/{customer_id}/` - Delete customer

### Campaigns
- `GET /api/campaigns/` - List all campaigns
  - Query params: `is_active` (boolean), `discount_type` (CART/DELIVERY)
- `POST /api/campaigns/` - Create a new campaign
- `GET /api/campaigns/{id}/` - Get campaign details
- `PUT /api/campaigns/{id}/` - Update campaign
- `PATCH /api/campaigns/{id}/` - Partial update campaign
- `DELETE /api/campaigns/{id}/` - Delete campaign

### Discount Resolution
- `GET /api/discounts/applicable/` - Get applicable campaigns for a customer
  - Required params: `customer_id`, `cart_total`, `delivery_fee`

### Campaign Usage
- `GET /api/campaign-usage/` - List usage records
  - Query params: `campaign_id`, `customer_id`, `usage_date`
- `GET /api/campaign-usage/{id}/` - Get usage record details

---

## Using Swagger UI

### 1. Navigate to Swagger UI
Open your browser and go to: `http://localhost:8000/swagger/`

### 2. Explore Endpoints
- Click on any endpoint to expand it
- View request parameters, body schema, and response formats
- See example values

### 3. Try It Out
1. Click "Try it out" button
2. Fill in required parameters
3. Click "Execute"
4. View the response

### 4. View Schemas
- Scroll to the bottom to see all data models
- Click on any model to see its structure
- View field types, required fields, and descriptions

---

## Response Format

All API endpoints return standardized responses:

### Success Response
```json
{
  "status": true,
  "message": "Operation completed successfully",
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
    // Error details (optional)
  }
}
```

---

## Example: Testing Discount Resolution

1. Go to `http://localhost:8000/swagger/`
2. Find `GET /api/discounts/applicable/`
3. Click "Try it out"
4. Fill in parameters:
   - `customer_id`: CUST001
   - `cart_total`: 1000
   - `delivery_fee`: 50
5. Click "Execute"
6. View the response with applicable campaigns

---

## Exporting API Documentation

### For Postman
1. Go to `http://localhost:8000/swagger.json/`
2. Copy the JSON content
3. In Postman: Import → Raw Text → Paste JSON
4. All endpoints will be imported

### For Code Generation
Use the OpenAPI schema to generate client SDKs:
```bash
# Example: Generate Python client
openapi-generator-cli generate -i http://localhost:8000/swagger.json/ -g python -o ./client
```

---

## Configuration

The Swagger configuration is in `discount_system/urls.py`:

```python
schema_view = get_schema_view(
    openapi.Info(
        title="Discount Campaign Management API",
        default_version='v1',
        description="API for managing discount campaigns...",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
```

---

## Benefits

1. **Interactive Testing** - Test APIs without writing code
2. **Auto-Generated** - Documentation stays in sync with code
3. **Client Generation** - Generate SDKs in multiple languages
4. **Team Collaboration** - Share API specs with frontend developers
5. **Standards Compliant** - Uses OpenAPI 2.0 specification

---

## Next Steps

1. Start the development server: `python manage.py runserver`
2. Open Swagger UI: `http://localhost:8000/swagger/`
3. Explore and test all API endpoints
4. Share the documentation URL with your team
