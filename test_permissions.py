"""
Test script to verify permission system for non-admin users.
This script tests that:
1. Non-staff users can view campaigns, customers, and usage records
2. Non-staff users cannot access create/update/delete views
3. Staff users can access all views
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from campaigns.models import Campaign, Customer
from datetime import date, timedelta


class PermissionSystemTest(TestCase):
    def setUp(self):
        """Set up test users and data"""
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff_test',
            password='testpass123',
            is_staff=True
        )
        
        # Create regular (non-staff) user
        self.regular_user = User.objects.create_user(
            username='regular_test',
            password='testpass123',
            is_staff=False
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            customer_id='TEST001',
            name='Test Customer',
            email='test@example.com'
        )
        
        # Create test campaign
        self.campaign = Campaign.objects.create(
            name='Test Campaign',
            description='Test Description',
            discount_type='CART',
            discount_value=100.00,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            total_budget=10000.00,
            max_transactions_per_customer_per_day=3,
            is_active=True
        )
        self.campaign.targeted_customers.add(self.customer)
        
        self.client = Client()
    
    def test_regular_user_can_view_campaigns(self):
        """Test that non-staff users can view campaign list"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('campaign-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Campaign')
        self.assertContains(response, 'View Only Mode')
    
    def test_regular_user_can_view_customers(self):
        """Test that non-staff users can view customer list"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('customer-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Customer')
        self.assertContains(response, 'View Only Mode')
    
    def test_regular_user_can_view_usage(self):
        """Test that non-staff users can view usage records"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('usage-list'))
        self.assertEqual(response.status_code, 200)
    
    def test_regular_user_cannot_create_campaign(self):
        """Test that non-staff users cannot access campaign create view"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('campaign-create'))
        # Should redirect to dashboard with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_regular_user_cannot_update_campaign(self):
        """Test that non-staff users cannot access campaign update view"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('campaign-update', args=[self.campaign.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_regular_user_cannot_delete_campaign(self):
        """Test that non-staff users cannot access campaign delete view"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('campaign-delete', args=[self.campaign.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_regular_user_cannot_create_customer(self):
        """Test that non-staff users cannot access customer create view"""
        self.client.login(username='regular_test', password='testpass123')
        response = self.client.get(reverse('customer-create'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))
    
    def test_staff_user_can_access_all_views(self):
        """Test that staff users can access all views"""
        self.client.login(username='staff_test', password='testpass123')
        
        # Test list views
        response = self.client.get(reverse('campaign-list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'View Only Mode')
        
        # Test create view
        response = self.client.get(reverse('campaign-create'))
        self.assertEqual(response.status_code, 200)
        
        # Test update view
        response = self.client.get(reverse('campaign-update', args=[self.campaign.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Test delete view
        response = self.client.get(reverse('campaign-delete', args=[self.campaign.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('campaign-list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'discount_system.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])
