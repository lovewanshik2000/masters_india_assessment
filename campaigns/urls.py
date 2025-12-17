"""
URL configuration for campaigns app - TEMPLATE VIEWS ONLY.

For API endpoints, see api_urls.py
"""

from django.urls import path
from .views import (
    DashboardView,
    CustomerListView, CustomerCreateView, CustomerUpdateView, CustomerDeleteView,
    CampaignListView, CampaignCreateView, CampaignUpdateView, CampaignDeleteView,
    DiscountPreviewView, UsageListView, ApplyDiscountTemplateView
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer-update'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer-delete'),
    path('campaigns/', CampaignListView.as_view(), name='campaign-list'),
    path('campaigns/create/', CampaignCreateView.as_view(), name='campaign-create'),
    path('campaigns/<int:pk>/update/', CampaignUpdateView.as_view(), name='campaign-update'),
    path('campaigns/<int:pk>/delete/', CampaignDeleteView.as_view(), name='campaign-delete'),
    path('discount-preview/', DiscountPreviewView.as_view(), name='discount-preview'),
    path('usage/', UsageListView.as_view(), name='usage-list'),
    path('apply-discount/', ApplyDiscountTemplateView.as_view(), name='apply-discount'),
]
