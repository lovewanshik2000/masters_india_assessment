from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Customer, Campaign, CampaignUsage

class DiscountCalculationGapTestCase(APITestCase):
    """Test cases for specific discount calculation edge cases."""
    
    def setUp(self):
        # Create staff user for authentication
        self.staff_user = User.objects.create_user(
            username='staff_gap',
            password='testpass123',
            is_staff=True
        )
        staff_refresh = RefreshToken.for_user(self.staff_user)
        self.staff_token = str(staff_refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.staff_token}')
        
        self.customer = Customer.objects.create(
            customer_id='CUST_GAP',
            name='Gap Analysis User',
            email='gap@example.com'
        )
        
        # Campaign with 100 discount, 1000 budget
        self.campaign = Campaign.objects.create(
            name='Gap Test Campaign',
            discount_type=Campaign.DISCOUNT_TYPE_CART,
            discount_value=Decimal('100.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=Decimal('1000.00'),
            consumed_budget=Decimal('0.00'),
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        self.campaign.targeted_customers.add(self.customer)

    def test_discount_capped_by_cart_total(self):
        """Test that discount does not exceed cart total."""
        # Cart total 50 < Discount 100
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST_GAP',
                'cart_total': '50.00',
                'delivery_fee': '10.00'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campaign_data = response.data['data']['applicable_campaigns'][0]
        self.assertEqual(Decimal(campaign_data['applicable_discount']), Decimal('50.00'))

    def test_discount_capped_by_remaining_budget(self):
        """Test that discount does not exceed remaining budget."""
        # Remaining budget 40 < Discount 100
        self.campaign.consumed_budget = Decimal('960.00') # 40 remaining
        self.campaign.save()
        
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST_GAP',
                'cart_total': '200.00',
                'delivery_fee': '10.00'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campaign_data = response.data['data']['applicable_campaigns'][0]
        self.assertEqual(Decimal(campaign_data['applicable_discount']), Decimal('40.00'))

    def test_discount_capped_by_delivery_fee(self):
        """Test that delivery discount does not exceed delivery fee."""
        # Change to delivery discount
        self.campaign.discount_type = Campaign.DISCOUNT_TYPE_DELIVERY
        self.campaign.discount_value = Decimal('50.00')
        self.campaign.save()
        
        # Delivery fee 30 < Discount 50
        response = self.client.get(
            '/api/discounts/applicable/',
            {
                'customer_id': 'CUST_GAP',
                'cart_total': '200.00',
                'delivery_fee': '30.00'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campaign_data = response.data['data']['applicable_campaigns'][0]
        self.assertEqual(Decimal(campaign_data['applicable_discount']), Decimal('30.00'))
