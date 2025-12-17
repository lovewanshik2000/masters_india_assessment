"""
Sample data creation script for Discount Campaign Management System.

Run this script to populate the database with sample customers and campaigns.

Usage:
    python manage.py shell < create_sample_data.py
"""

from campaigns.models import Customer, Campaign
from datetime import date, timedelta
from decimal import Decimal

print("Creating sample data...")

# Create customers
customers_data = [
    {"customer_id": "CUST001", "name": "John Doe", "email": "john@example.com"},
    {"customer_id": "CUST002", "name": "Jane Smith", "email": "jane@example.com"},
    {"customer_id": "CUST003", "name": "Bob Johnson", "email": "bob@example.com"},
    {"customer_id": "CUST004", "name": "Alice Williams", "email": "alice@example.com"},
]

customers = []
for data in customers_data:
    customer, created = Customer.objects.get_or_create(
        customer_id=data["customer_id"],
        defaults={"name": data["name"], "email": data["email"]}
    )
    customers.append(customer)
    if created:
        print(f"✓ Created customer: {customer.name}")
    else:
        print(f"- Customer already exists: {customer.name}")

# Create campaigns
today = date.today()

# Campaign 1: Cart Discount for all customers
campaign1, created = Campaign.objects.get_or_create(
    name="Holiday Cart Discount",
    defaults={
        "description": "Get ₹100 off on your cart during the holiday season",
        "discount_type": Campaign.DISCOUNT_TYPE_CART,
        "discount_value": Decimal("100.00"),
        "start_date": today,
        "end_date": today + timedelta(days=30),
        "total_budget": Decimal("50000.00"),
        "max_transactions_per_customer_per_day": 3,
        "is_active": True
    }
)
if created:
    campaign1.targeted_customers.set(customers)
    print(f"✓ Created campaign: {campaign1.name}")
else:
    print(f"- Campaign already exists: {campaign1.name}")

# Campaign 2: Delivery Discount for premium customers
campaign2, created = Campaign.objects.get_or_create(
    name="Free Delivery for Premium",
    defaults={
        "description": "Free delivery for our premium customers",
        "discount_type": Campaign.DISCOUNT_TYPE_DELIVERY,
        "discount_value": Decimal("50.00"),
        "start_date": today,
        "end_date": today + timedelta(days=60),
        "total_budget": Decimal("20000.00"),
        "max_transactions_per_customer_per_day": 5,
        "is_active": True
    }
)
if created:
    # Only target first two customers
    campaign2.targeted_customers.set(customers[:2])
    print(f"✓ Created campaign: {campaign2.name}")
else:
    print(f"- Campaign already exists: {campaign2.name}")

# Campaign 3: Limited Budget Cart Discount
campaign3, created = Campaign.objects.get_or_create(
    name="Flash Sale - Limited Budget",
    defaults={
        "description": "Flash sale with limited budget - first come first served",
        "discount_type": Campaign.DISCOUNT_TYPE_CART,
        "discount_value": Decimal("200.00"),
        "start_date": today,
        "end_date": today + timedelta(days=7),
        "total_budget": Decimal("5000.00"),
        "max_transactions_per_customer_per_day": 1,
        "is_active": True
    }
)
if created:
    campaign3.targeted_customers.set(customers)
    print(f"✓ Created campaign: {campaign3.name}")
else:
    print(f"- Campaign already exists: {campaign3.name}")

# Campaign 4: Inactive campaign (for testing)
campaign4, created = Campaign.objects.get_or_create(
    name="Expired Summer Sale",
    defaults={
        "description": "This campaign is inactive",
        "discount_type": Campaign.DISCOUNT_TYPE_CART,
        "discount_value": Decimal("150.00"),
        "start_date": today - timedelta(days=60),
        "end_date": today - timedelta(days=30),
        "total_budget": Decimal("30000.00"),
        "max_transactions_per_customer_per_day": 2,
        "is_active": False
    }
)
if created:
    campaign4.targeted_customers.set(customers)
    print(f"✓ Created campaign: {campaign4.name}")
else:
    print(f"- Campaign already exists: {campaign4.name}")

print("\n" + "="*50)
print("Sample data creation complete!")
print("="*50)
print(f"\nCreated {Customer.objects.count()} customers")
print(f"Created {Campaign.objects.count()} campaigns")
print(f"Active campaigns: {Campaign.objects.filter(is_active=True).count()}")
print("\nYou can now test the API endpoints:")
print(f"  - List customers: GET http://localhost:8000/api/customers/")
print(f"  - List campaigns: GET http://localhost:8000/api/campaigns/")
print(f"  - Get discounts: GET http://localhost:8000/api/discounts/applicable/?customer_id=CUST001&cart_total=1000&delivery_fee=100")
