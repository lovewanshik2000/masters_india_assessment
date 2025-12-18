"""
Extended test suite for the Discount Campaign Management System.

This module includes additional tests for:
- Model field validation (validators)
- API edge cases (invalid JSON, missing fields, types)
- Business logic edge cases (budget boundaries)
- Authentication edge cases (invalid tokens)
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import json

from .models import Customer, Campaign, CampaignUsage


class ExtendedModelValidationTestCase(TestCase):
    """Test cases for specific model field validators."""
    
    def setUp(self):
        self.campaign_data = {
            'name': 'Validation Test',
            'description': 'Testing validators',
            'discount_type': Campaign.DISCOUNT_TYPE_CART,
            'discount_value': Decimal('100.00'),
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'total_budget': Decimal('10000.00'),
            'consumed_budget': Decimal('0.00'),
            'max_transactions_per_customer_per_day': 3,
            'is_active': True
        }

    def test_discount_value_min_validator(self):
        """Verify discount_value cannot be less than 0.01."""
        self.campaign_data['discount_value'] = Decimal('0.00')
        campaign = Campaign(**self.campaign_data)
        with self.assertRaises(ValidationError) as cm:
            campaign.full_clean()
        self.assertIn('discount_value', cm.exception.message_dict)

    def test_total_budget_min_validator(self):
        """Verify total_budget cannot be less than 0.01."""
        self.campaign_data['total_budget'] = Decimal('0.00')
        campaign = Campaign(**self.campaign_data)
        with self.assertRaises(ValidationError) as cm:
            campaign.full_clean()
        self.assertIn('total_budget', cm.exception.message_dict)

    def test_consumed_budget_min_validator(self):
        """Verify consumed_budget cannot be negative."""
        self.campaign_data['consumed_budget'] = Decimal('-10.00')
        campaign = Campaign(**self.campaign_data)
        with self.assertRaises(ValidationError) as cm:
            campaign.full_clean()
        self.assertIn('consumed_budget', cm.exception.message_dict)

    def test_max_transactions_min_validator(self):
        """Verify max_transactions_per_customer_per_day cannot be less than 1."""
        self.campaign_data['max_transactions_per_customer_per_day'] = 0
        campaign = Campaign(**self.campaign_data)
        with self.assertRaises(ValidationError) as cm:
            campaign.full_clean()
        self.assertIn('max_transactions_per_customer_per_day', cm.exception.message_dict)


class ExtendedAPIEdgeCaseTestCase(APITestCase):
    """Test cases for API edge cases."""

    def setUp(self):
        # Create staff user for authentication
        self.staff_user = User.objects.create_user(
            username='staff_edge',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        
        self.customer = Customer.objects.create(
            customer_id='CUST_EDGE',
            name='Edge Case User',
            email='edge@example.com'
        )

    def test_create_campaign_invalid_json(self):
        """Verify API handles malformed JSON gracefully."""
        # This is a bit tricky with APITestCase client as it handles serialization,
        # but we can pass a string with content_type='application/json'
        response = self.client.post(
            '/api/campaigns/',
            data='{invalid_json:',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_campaign_missing_fields(self):
        """Verify API returns 400 for missing required fields."""
        data = {
            'name': 'Missing Fields',
            # Missing other required fields
        }
        response = self.client.post('/api/campaigns/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('discount_type', response.data['data'])

    def test_create_campaign_invalid_types(self):
        """Verify API returns 400 for invalid data types."""
        data = {
            'name': 'Invalid Types',
            'discount_type': 'CART',
            'discount_value': 'not_a_number',  # Invalid
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=30)),
            'total_budget': '1000.00',
            'max_transactions_per_customer_per_day': 5,
            'targeted_customer_ids': [self.customer.id],
            'is_active': True
        }
        response = self.client.post('/api/campaigns/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('discount_value', response.data['data'])

    def test_list_campaigns_pagination(self):
        """Verify pagination works correctly with > 20 items."""
        # Create 25 campaigns
        for i in range(25):
            Campaign.objects.create(
                name=f'Pagination Test {i}',
                discount_type=Campaign.DISCOUNT_TYPE_CART,
                discount_value=Decimal('10.00'),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                total_budget=Decimal('1000.00'),
                max_transactions_per_customer_per_day=1
            )
        
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 20)  # Default page size
        self.assertIsNotNone(response.data['data']['next'])


class BusinessLogicEdgeCaseTestCase(TestCase):
    """Test cases for specific business logic edge cases."""

    def setUp(self):
        self.customer = Customer.objects.create(
            customer_id='CUST_BIZ',
            name='Biz Logic User',
            email='biz@example.com'
        )
        self.campaign = Campaign.objects.create(
            name='Budget Boundary',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('100.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('1000.00'),
            consumed_budget=Decimal('900.00'), # 100 remaining
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        self.campaign.targeted_customers.add(self.customer)

    def test_campaign_exhaustion_exact_boundary(self):
        """Verify behavior when budget is exactly exhausted."""
        # Campaign has 100 remaining. Discount is 100.
        self.assertTrue(self.campaign.has_budget_for_discount(Decimal('100.00')))
        
        # Consume the last 100
        self.campaign.consumed_budget += Decimal('100.00')
        self.campaign.save()
        
        # Now it should be invalid/exhausted
        self.assertFalse(self.campaign.has_budget_for_discount(Decimal('0.01')))
        self.assertFalse(self.campaign.is_valid())


class AuthenticationEdgeCaseTestCase(APITestCase):
    """Test cases for authentication edge cases."""

    def test_invalid_token_format(self):
        """Verify API returns 401 for malformed tokens."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_string')
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_auth_header(self):
        """Verify API returns 401 when auth header is missing."""
        # Ensure no credentials are set
        self.client.credentials() 
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
