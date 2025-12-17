from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, CampaignViewSet, CampaignUsageViewSet, DiscountResolutionView, ApplyDiscountView
from .auth_views import RegisterView, LoginView, RefreshTokenView

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='api-customer')
router.register(r'campaigns', CampaignViewSet, basename='api-campaign')
router.register(r'campaign-usage', CampaignUsageViewSet, basename='api-campaign-usage')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='api-token-refresh'),
    path('discounts/applicable/', DiscountResolutionView.as_view(), name='api-discount-resolution'),
    path('discounts/apply/', ApplyDiscountView.as_view(), name='api-discount-apply'),
]
