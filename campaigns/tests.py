"""
Comprehensive test suite for the Discount Campaign Management System.

This module includes:
- Model tests for Campaign, Customer, and CampaignUsage
- API tests for CRUD operations
- Integration tests for discount resolution
- Edge case tests
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal

from .models import Customer, Campaign, CampaignUsage


class CustomerModelTestCase(TestCase):
    """Test cases for Customer model."""
    
    def setUp(self):
        """Set up test data."""
        self.customer_data = {
            'customer_id': 'CUST001',
            'name': 'John Doe',
            'email': 'john@example.com'
        }
    
    def test_create_customer(self):
        """Test creating a customer."""
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.customer_id, 'CUST001')
        self.assertEqual(customer.name, 'John Doe')
        self.assertEqual(customer.email, 'john@example.com')
    
    def test_customer_unique_customer_id(self):
        """Test that customer_id must be unique."""
        Customer.objects.create(**self.customer_data)
        with self.assertRaises(Exception):
            Customer.objects.create(**self.customer_data)
    
    def test_customer_unique_email(self):
        """Test that email must be unique."""
        Customer.objects.create(**self.customer_data)
        duplicate_data = self.customer_data.copy()
        duplicate_data['customer_id'] = 'CUST002'
        with self.assertRaises(Exception):
            Customer.objects.create(**duplicate_data)


class CampaignModelTestCase(TestCase):
    """Test cases for Campaign model."""
    
    def setUp(self):
        """Set up test data."""
        self.customer1 = Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        self.customer2 = Customer.objects.create(
            customer_id='CUST002',
            name='Jane Smith',
            email='jane@example.com'
        )
        
        self.campaign_data = {
            'name': 'Summer Sale',
            'description': 'Summer discount campaign',
            'discount_type': Campaign.DISCOUNT_TYPE_CART,
            'discount_value': Decimal('100.00'),
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'total_budget': Decimal('10000.00'),
            'consumed_budget': Decimal('0.00'),
            'max_transactions_per_customer_per_day': 3,
            'is_active': True
        }
    
    def test_create_campaign(self):
        """Test creating a campaign."""
        campaign = Campaign.objects.create(**self.campaign_data)
        campaign.targeted_customers.add(self.customer1)
        
        self.assertEqual(campaign.name, 'Summer Sale')
        self.assertEqual(campaign.discount_type, Campaign.DISCOUNT_TYPE_CART)
        self.assertTrue(campaign.is_valid())
    
    def test_campaign_date_validation(self):
        """Test that end_date must be after start_date."""
        invalid_data = self.campaign_data.copy()
        invalid_data['end_date'] = date.today() - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            campaign = Campaign(**invalid_data)
            campaign.save()
    
    def test_campaign_is_valid_active_check(self):
        """Test that inactive campaigns are not valid."""
        campaign = Campaign.objects.create(**self.campaign_data)
        campaign.is_active = False
        campaign.save()
        
        self.assertFalse(campaign.is_valid())
    
    def test_campaign_is_valid_date_range(self):
        """Test campaign validity based on date range."""
        # Future campaign
        future_data = self.campaign_data.copy()
        future_data['start_date'] = date.today() + timedelta(days=10)
        future_data['end_date'] = date.today() + timedelta(days=40)
        future_campaign = Campaign.objects.create(**future_data)
        
        self.assertFalse(future_campaign.is_valid())
        
        # Expired campaign
        expired_data = self.campaign_data.copy()
        expired_data['start_date'] = date.today() - timedelta(days=40)
        expired_data['end_date'] = date.today() - timedelta(days=10)
        expired_campaign = Campaign.objects.create(**expired_data)
        
        self.assertFalse(expired_campaign.is_valid())
    
    def test_campaign_is_valid_budget_exhausted(self):
        """Test that campaigns with exhausted budget are not valid."""
        campaign = Campaign.objects.create(**self.campaign_data)
        campaign.consumed_budget = campaign.total_budget
        campaign.save()
        
        self.assertFalse(campaign.is_valid())
    
    def test_campaign_has_budget_for_discount(self):
        """Test budget availability check."""
        campaign = Campaign.objects.create(**self.campaign_data)
        
        # Should have budget for 100
        self.assertTrue(campaign.has_budget_for_discount(Decimal('100.00')))
        
        # Should not have budget for more than total budget
        self.assertFalse(campaign.has_budget_for_discount(Decimal('20000.00')))
        
        # Consume some budget
        campaign.consumed_budget = Decimal('9950.00')
        campaign.save()
        
        # Should have budget for 50
        self.assertTrue(campaign.has_budget_for_discount(Decimal('50.00')))
        
        # Should not have budget for 100
        self.assertFalse(campaign.has_budget_for_discount(Decimal('100.00')))
    
    def test_campaign_customer_eligibility(self):
        """Test customer eligibility check."""
        campaign = Campaign.objects.create(**self.campaign_data)
        campaign.targeted_customers.add(self.customer1)
        
        self.assertTrue(campaign.is_customer_eligible(self.customer1))
        self.assertFalse(campaign.is_customer_eligible(self.customer2))
    
    def test_campaign_daily_usage_limit(self):
        """Test daily usage limit enforcement."""
        campaign = Campaign.objects.create(**self.campaign_data)
        campaign.targeted_customers.add(self.customer1)
        
        # Initially, customer can use the campaign
        self.assertTrue(campaign.can_customer_use_today(self.customer1))
        
        # Create usage record
        usage = CampaignUsage.objects.create(
            campaign=campaign,
            customer=self.customer1,
            usage_date=date.today(),
            usage_count=2
        )
        
        # Customer can still use (2 < 3)
        self.assertTrue(campaign.can_customer_use_today(self.customer1))
        
        # Increase usage to limit
        usage.usage_count = 3
        usage.save()
        
        # Customer cannot use anymore
        self.assertFalse(campaign.can_customer_use_today(self.customer1))


class CampaignUsageModelTestCase(TestCase):
    """Test cases for CampaignUsage model."""
    
    def setUp(self):
        """Set up test data."""
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        self.campaign = Campaign.objects.create(
            name='Test Campaign',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=2
        )
        self.campaign.targeted_customers.add(self.customer)
    
    def test_create_usage_record(self):
        """Test creating a usage record."""
        usage = CampaignUsage.objects.create(
            campaign=self.campaign,
            customer=self.customer,
            usage_date=date.today(),
            usage_count=1
        )
        
        self.assertEqual(usage.campaign, self.campaign)
        self.assertEqual(usage.customer, self.customer)
        self.assertEqual(usage.usage_count, 1)
    
    def test_unique_constraint(self):
        """Test unique constraint on campaign-customer-date."""
        CampaignUsage.objects.create(
            campaign=self.campaign,
            customer=self.customer,
            usage_date=date.today(),
            usage_count=1
        )
        
        # Should not be able to create duplicate
        with self.assertRaises(Exception):
            CampaignUsage.objects.create(
                campaign=self.campaign,
                customer=self.customer,
                usage_date=date.today(),
                usage_count=1
            )


class CampaignAPITestCase(APITestCase):
    """Test cases for Campaign API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create staff user for authentication
        from django.contrib.auth.models import User
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.staff_user = User.objects.create_user(
            username='staff_campaign',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        
        # Set authentication for all requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        self.campaign_data = {
            'name': 'API Test Campaign',
            'description': 'Test campaign via API',
            'discount_type': 'CART',
            'discount_value': '75.00',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=30)),
            'total_budget': '8000.00',
            'max_transactions_per_customer_per_day': 5,
            'targeted_customer_ids': [self.customer.id],
            'is_active': True
        }
    
    def test_create_campaign(self):
        """Test creating a campaign via API."""
        response = self.client.post('/api/campaigns/', self.campaign_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'API Test Campaign')
        self.assertTrue(response.data['data']['is_valid'])
    
    def test_list_campaigns(self):
        """Test listing campaigns."""
        campaign = Campaign.objects.create(
            name='List Test',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=3
        )
        
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['data']['results']), 1)
    
    def test_filter_campaigns_by_active(self):
        """Test filtering campaigns by active status."""
        Campaign.objects.create(
            name='Active Campaign',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        
        Campaign.objects.create(
            name='Inactive Campaign',
            discount_type=Campaign.DISCOUNT_TYPE_DELIVERY,
            discount_value=Decimal('25.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('3000.00'),
            max_transactions_per_customer_per_day=2,
            is_active=False
        )
        
        response = self.client.get('/api/campaigns/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for campaign in response.data['data']['results']:
            self.assertTrue(campaign['is_active'])
    
    def test_update_campaign(self):
        """Test updating a campaign."""
        campaign = Campaign.objects.create(
            name='Update Test',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=3
        )
        
        update_data = {
            'name': 'Updated Campaign',
            'discount_type': 'CART',
            'discount_value': '60.00',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=30)),
            'total_budget': '6000.00',
            'max_transactions_per_customer_per_day': 4,
            'targeted_customer_ids': [],
            'is_active': True
        }
        
        response = self.client.put(f'/api/campaigns/{campaign.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'Updated Campaign')
    
    def test_delete_campaign(self):
        """Test deleting a campaign."""
        campaign = Campaign.objects.create(
            name='Delete Test',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=3
        )
        
        response = self.client.delete(f'/api/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Campaign.objects.filter(id=campaign.id).exists())


class DiscountResolutionAPITestCase(APITestCase):
    """Test cases for Discount Resolution API."""
    
    def setUp(self):
        """Set up test data."""
        # Create staff user for authentication
        from django.contrib.auth.models import User
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.staff_user = User.objects.create_user(
            username='staff_discount',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        
        # Set authentication for all requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        
        self.customer1 = Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        self.customer2 = Customer.objects.create(
            customer_id='CUST002',
            name='Jane Smith',
            email='jane@example.com'
        )
        
        # Active cart discount campaign
        self.cart_campaign = Campaign.objects.create(
            name='Cart Discount',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('100.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('10000.00'),
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        self.cart_campaign.targeted_customers.add(self.customer1)
        
        # Active delivery discount campaign
        self.delivery_campaign = Campaign.objects.create(
            name='Delivery Discount',
            discount_type=Campaign.DISCOUNT_TYPE_DELIVERY,
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=2,
            is_active=True
        )
        self.delivery_campaign.targeted_customers.add(self.customer1)
    
    def test_get_applicable_campaigns(self):
        """Test fetching applicable campaigns."""
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['customer_id'], 'CUST001')
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 2)
    
    def test_missing_parameters(self):
        """Test API with missing parameters."""
        response = self.client.get('/api/discounts/applicable/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.get('/api/discounts/applicable/', {'customer_id': 'CUST001'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_customer(self):
        """Test API with non-existent customer."""
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'INVALID',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_customer_not_targeted(self):
        """Test that non-targeted customers don't get campaigns."""
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST002',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 0)
    
    def test_inactive_campaign_not_returned(self):
        """Test that inactive campaigns are not returned."""
        self.cart_campaign.is_active = False
        self.cart_campaign.save()
        
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only delivery campaign should be returned
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 1)
        self.assertEqual(response.data['data']['applicable_campaigns'][0]['discount_type'], 'DELIVERY')
    
    def test_expired_campaign_not_returned(self):
        """Test that expired campaigns are not returned."""
        # Use update to bypass validation
        Campaign.objects.filter(id=self.cart_campaign.id).update(
            end_date=date.today() - timedelta(days=1)
        )
        self.cart_campaign.refresh_from_db()
        
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only delivery campaign should be returned
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 1)
    
    def test_budget_exhausted_campaign_not_returned(self):
        """Test that campaigns with exhausted budget are not returned."""
        self.cart_campaign.consumed_budget = self.cart_campaign.total_budget
        self.cart_campaign.save()
        
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only delivery campaign should be returned
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 1)
    
    def test_daily_limit_exceeded(self):
        """Test that campaigns with exceeded daily limits are not returned."""
        # Create usage record at the limit
        CampaignUsage.objects.create(
            campaign=self.cart_campaign,
            customer=self.customer1,
            usage_date=date.today(),
            usage_count=3  # Equal to max_transactions_per_customer_per_day
        )
        
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only delivery campaign should be returned
        self.assertEqual(len(response.data['data']['applicable_campaigns']), 1)
        self.assertEqual(response.data['data']['applicable_campaigns'][0]['name'], 'Delivery Discount')
    
    def test_applicable_discount_calculation(self):
        """Test that applicable discount is correctly calculated."""
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find cart campaign in response
        cart_campaign_data = next(
            c for c in response.data['data']['applicable_campaigns']
            if c['discount_type'] == 'CART'
        )
        
        # Applicable discount should be min(discount_value, cart_total, remaining_budget)
        # = min(100, 500, 10000) = 100
        self.assertEqual(Decimal(cart_campaign_data['applicable_discount']), Decimal('100.00'))
        
        # Find delivery campaign in response
        delivery_campaign_data = next(
            c for c in response.data['data']['applicable_campaigns']
            if c['discount_type'] == 'DELIVERY'
        )
        
        # Applicable discount should be min(discount_value, delivery_fee, remaining_budget)
        # = min(50, 100, 5000) = 50
        self.assertEqual(Decimal(delivery_campaign_data['applicable_discount']), Decimal('50.00'))


class CustomerAPITestCase(APITestCase):
    """Test cases for Customer API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create staff user for authentication
        from django.contrib.auth.models import User
        from rest_framework_simplejwt.tokens import RefreshToken
        
        self.staff_user = User.objects.create_user(
            username='staff_customer',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        
        # Set authentication for all requests
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
    
    def test_create_customer(self):
        """Test creating a customer via API."""
        customer_data = {
            'customer_id': 'CUST001',
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        response = self.client.post('/api/customers/', customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['customer_id'], 'CUST001')
    
    def test_list_customers(self):
        """Test listing customers."""
        Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['data']['results']), 1)
    
    def test_get_customer_by_customer_id(self):
        """Test retrieving a customer by customer_id."""
        customer = Customer.objects.create(
            customer_id='CUST001',
            name='John Doe',
            email='john@example.com'
        )
        
        response = self.client.get(f'/api/customers/{customer.customer_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['customer_id'], 'CUST001')


# ============================================================================
# API PERMISSION TESTS
# ============================================================================

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class APIPermissionTestCase(APITestCase):
    """Test cases for API permission system."""
    
    def setUp(self):
        """Set up test users and data."""
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_api',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        
        # Create regular (non-staff) user
        self.regular_user = User.objects.create_user(
            username='regular_api',
            email='regular@test.com',
            password='testpass123',
            is_staff=False
        )
        regular_refresh = RefreshToken.for_user(self.regular_user)
        self.regular_token = str(regular_refresh.access_token)
        
        # Create test customer
        self.customer = Customer.objects.create(
            customer_id='CUST001',
            name='Test Customer',
            email='test@example.com'
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            name='Test Campaign',
            description='Test Description',
            discount_type='CART',
            discount_value=Decimal('100.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('10000.00'),
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        self.campaign.targeted_customers.add(self.customer)
        
        self.campaign_data = {
            'name': 'New API Campaign',
            'description': 'New campaign via API',
            'discount_type': 'CART',
            'discount_value': '75.00',
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=30)),
            'total_budget': '8000.00',
            'max_transactions_per_customer_per_day': 5,
            'targeted_customer_ids': [self.customer.id],
            'is_active': True
        }
    
    # Campaign API Permission Tests
    
    def test_unauthenticated_cannot_list_campaigns(self):
        """Test that unauthenticated users cannot list campaigns."""
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_staff_can_list_campaigns(self):
        """Test that staff users can list campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_can_list_campaigns(self):
        """Test that regular users can list campaigns (read-only)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_can_create_campaign(self):
        """Test that staff users can create campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.post('/api/campaigns/', self.campaign_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'New API Campaign')
    
    def test_regular_user_cannot_create_campaign(self):
        """Test that regular users cannot create campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.post('/api/campaigns/', self.campaign_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_staff_can_retrieve_campaign(self):
        """Test that staff users can retrieve campaign details."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.get(f'/api/campaigns/{self.campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_can_retrieve_campaign(self):
        """Test that regular users can retrieve campaign details (read-only)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.get(f'/api/campaigns/{self.campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_can_update_campaign(self):
        """Test that staff users can update campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        update_data = self.campaign_data.copy()
        update_data['name'] = 'Updated Campaign'
        response = self.client.put(f'/api/campaigns/{self.campaign.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_update_campaign(self):
        """Test that regular users cannot update campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        update_data = self.campaign_data.copy()
        update_data['name'] = 'Should Not Update'
        response = self.client.put(f'/api/campaigns/{self.campaign.id}/', update_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_staff_can_delete_campaign(self):
        """Test that staff users can delete campaigns."""
        campaign = Campaign.objects.create(
            name='To Delete',
            discount_type='CART',
            discount_value=Decimal('50.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('5000.00'),
            max_transactions_per_customer_per_day=2
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.delete(f'/api/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Campaign.objects.filter(id=campaign.id).exists())
    
    def test_regular_user_cannot_delete_campaign(self):
        """Test that regular users cannot delete campaigns."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.delete(f'/api/campaigns/{self.campaign.id}/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
        self.assertTrue(Campaign.objects.filter(id=self.campaign.id).exists())
    
    # Customer API Permission Tests
    
    def test_staff_can_create_customer(self):
        """Test that staff users can create customers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        customer_data = {
            'customer_id': 'CUST002',
            'name': 'New Customer',
            'email': 'new@example.com'
        }
        response = self.client.post('/api/customers/', customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_regular_user_cannot_create_customer(self):
        """Test that regular users cannot create customers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        customer_data = {
            'customer_id': 'CUST003',
            'name': 'Should Not Create',
            'email': 'shouldnot@example.com'
        }
        response = self.client.post('/api/customers/', customer_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_regular_user_can_list_customers(self):
        """Test that regular users can list customers (read-only)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.get('/api/customers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_can_update_customer(self):
        """Test that staff users can update customers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        update_data = {
            'customer_id': 'CUST001',
            'name': 'Updated Name',
            'email': 'test@example.com'
        }
        response = self.client.put(f'/api/customers/{self.customer.customer_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_update_customer(self):
        """Test that regular users cannot update customers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        update_data = {
            'customer_id': 'CUST001',
            'name': 'Should Not Update',
            'email': 'test@example.com'
        }
        response = self.client.put(f'/api/customers/{self.customer.customer_id}/', update_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    def test_staff_can_delete_customer(self):
        """Test that staff users can delete customers."""
        customer = Customer.objects.create(
            customer_id='CUST_DELETE',
            name='To Delete',
            email='delete@example.com'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.delete(f'/api/customers/{customer.customer_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_regular_user_cannot_delete_customer(self):
        """Test that regular users cannot delete customers."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.delete(f'/api/customers/{self.customer.customer_id}/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    # Discount Resolution API Permission Tests
    
    def test_staff_can_get_applicable_discounts(self):
        """Test that staff users can get applicable discounts."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_can_get_applicable_discounts(self):
        """Test that regular users can get applicable discounts (read-only)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_can_apply_discounts(self):
        """Test that staff users can apply discounts."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.post(
            '/api/discounts/apply/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00',
                'campaign_ids': [self.campaign.id]
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_cannot_apply_discounts(self):
        """Test that regular users cannot apply discounts."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.post(
            '/api/discounts/apply/',
            {
                'customer_id': 'CUST001',
                'cart_total': '500.00',
                'delivery_fee': '100.00',
                'campaign_ids': [self.campaign.id]
            },
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])
    
    # Campaign Usage API Permission Tests
    
    def test_staff_can_list_usage_records(self):
        """Test that staff users can list usage records."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        response = self.client.get('/api/campaign-usage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_regular_user_can_list_usage_records(self):
        """Test that regular users can list usage records (read-only)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.regular_token}')
        response = self.client.get('/api/campaign-usage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthenticated_cannot_access_usage_records(self):
        """Test that unauthenticated users cannot access usage records."""
        response = self.client.get('/api/campaign-usage/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

