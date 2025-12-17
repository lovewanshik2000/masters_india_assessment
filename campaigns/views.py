from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import F, Q
from django.db import transaction
from datetime import date
from decimal import Decimal

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from .mixins import ViewPermissionMixin, StaffRequiredMixin

from .models import Customer, Campaign, CampaignUsage
from .serializers import CustomerSerializer, CampaignSerializer, CampaignUsageSerializer, ApplicableCampaignSerializer
from .forms import CustomerForm, CampaignForm, DiscountPreviewForm
from .utils import api_response
from .pagination import StandardizedPagination
from .permissions import IsStaffOrReadOnly, IsStaffUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Sum


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'campaigns/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # Statistics
        context['total_campaigns'] = Campaign.objects.count()
        context['active_campaigns'] = Campaign.objects.filter(is_active=True).count()
        context['total_customers'] = Customer.objects.count()
        context['total_budget'] = Campaign.objects.aggregate(total=Sum('total_budget'))['total'] or 0
        context['consumed_budget'] = Campaign.objects.aggregate(consumed=Sum('consumed_budget'))['consumed'] or 0
        context['total_usage'] = CampaignUsage.objects.count()
        context['today_usage'] = CampaignUsage.objects.filter(usage_date=today).count()
        
        # Recent activity
        context['recent_campaigns'] = Campaign.objects.all().order_by('-created_at')[:5]
        context['recent_usage'] = CampaignUsage.objects.select_related('campaign', 'customer').order_by('-updated_at')[:5]
        
        return context


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = 'customer_id'
    pagination_class = StandardizedPagination
    permission_classes = [IsStaffOrReadOnly]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(success=True, message="Customers retrieved successfully", data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return api_response(success=True, message="Customer created successfully", data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message="Validation failed", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(success=True, message="Customer retrieved successfully", data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return api_response(success=True, message="Customer updated successfully", data=serializer.data)
        return api_response(success=False, message="Validation failed", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(success=True, message="Customer deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().prefetch_related('targeted_customers')
    serializer_class = CampaignSerializer
    pagination_class = StandardizedPagination
    permission_classes = [IsStaffOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        discount_type = self.request.query_params.get('discount_type')
        if discount_type:
            queryset = queryset.filter(discount_type=discount_type.upper())
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(success=True, message="Campaigns retrieved successfully", data=serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return api_response(success=True, message="Campaign created successfully", data=serializer.data, status_code=status.HTTP_201_CREATED)
        return api_response(success=False, message="Validation failed", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(success=True, message="Campaign retrieved successfully", data=serializer.data)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return api_response(success=True, message="Campaign updated successfully", data=serializer.data)
        return api_response(success=False, message="Validation failed", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(success=True, message="Campaign deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


class DiscountResolutionView(APIView):
    permission_classes = [IsStaffOrReadOnly]
    
    @swagger_auto_schema(
        operation_description="Get all applicable discount campaigns for a customer based on cart and delivery values",
        manual_parameters=[
            openapi.Parameter('customer_id', openapi.IN_QUERY, description="Customer's unique ID", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('cart_total', openapi.IN_QUERY, description="Total cart value", type=openapi.TYPE_NUMBER, required=True),
            openapi.Parameter('delivery_fee', openapi.IN_QUERY, description="Delivery fee amount", type=openapi.TYPE_NUMBER, required=True),
        ],
        responses={
            200: openapi.Response('Success', ApplicableCampaignSerializer(many=True)),
            400: 'Bad Request - Missing or invalid parameters',
            404: 'Customer not found'
        }
    )
    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        cart_total = request.query_params.get('cart_total')
        delivery_fee = request.query_params.get('delivery_fee')
        
        if not customer_id:
            return api_response(success=False, message="customer_id is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if cart_total is None:
            return api_response(success=False, message="cart_total is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if delivery_fee is None:
            return api_response(success=False, message="delivery_fee is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_total = Decimal(cart_total)
            delivery_fee = Decimal(delivery_fee)
        except (ValueError, TypeError):
            return api_response(success=False, message="cart_total and delivery_fee must be valid numbers", status_code=status.HTTP_400_BAD_REQUEST)
        
        if cart_total < 0 or delivery_fee < 0:
            return api_response(success=False, message="cart_total and delivery_fee must be non-negative", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return api_response(success=False, message=f"Customer with ID {customer_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        today = date.today()
        campaigns = Campaign.objects.filter(
            targeted_customers=customer,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).prefetch_related('targeted_customers')
        
        applicable_campaigns = []
        for campaign in campaigns:
            if campaign.consumed_budget >= campaign.total_budget:
                continue
            
            current_usage = self._get_customer_usage_today(campaign, customer)
            if current_usage >= campaign.max_transactions_per_customer_per_day:
                continue
            
            remaining_budget = campaign.total_budget - campaign.consumed_budget
            if remaining_budget <= 0:
                continue
            
            applicable_campaigns.append(campaign)
        
        serializer = ApplicableCampaignSerializer(
            applicable_campaigns, many=True,
            context={'cart_total': cart_total, 'delivery_fee': delivery_fee}
        )
        
        response_data = {
            'customer_id': customer_id,
            'cart_total': str(cart_total),
            'delivery_fee': str(delivery_fee),
            'applicable_campaigns': serializer.data
        }
        
        return api_response(success=True, message="Applicable campaigns retrieved successfully", data=response_data)
    
    def _get_customer_usage_today(self, campaign, customer):
        today = date.today()
        usage = CampaignUsage.objects.filter(
            campaign=campaign, customer=customer, usage_date=today
        ).first()
        return usage.usage_count if usage else 0


class CampaignUsageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CampaignUsage.objects.all().select_related('campaign', 'customer')
    serializer_class = CampaignUsageSerializer
    pagination_class = StandardizedPagination
    permission_classes = [IsStaffOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer__customer_id=customer_id)
        usage_date = self.request.query_params.get('usage_date')
        if usage_date:
            queryset = queryset.filter(usage_date=usage_date)
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return api_response(success=True, message="Campaign usage records retrieved successfully", data=serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(success=True, message="Campaign usage record retrieved successfully", data=serializer.data)




class CampaignListView(ViewPermissionMixin, ListView):
    model = Campaign
    template_name = 'campaigns/list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Campaign.objects.all().prefetch_related('targeted_customers')
        filter_active = self.request.GET.get('active')
        if filter_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif filter_active == 'false':
            queryset = queryset.filter(is_active=False)
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_count'] = Campaign.objects.filter(is_active=True).count()
        context['inactive_count'] = Campaign.objects.filter(is_active=False).count()
        context['filter_active'] = self.request.GET.get('active', '')
        for campaign in context['campaigns']:
            campaign.is_valid = self._is_campaign_valid(campaign)
        return context
    
    def _is_campaign_valid(self, campaign):
        if not campaign.is_active:
            return False
        today = date.today()
        if not (campaign.start_date <= today <= campaign.end_date):
            return False
        if campaign.consumed_budget >= campaign.total_budget:
            return False
        return True


class CampaignCreateView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'campaigns/form.html'
    success_url = reverse_lazy('campaign-list')
    success_message = "Campaign '%(name)s' created successfully!"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Campaign'
        context['submit_text'] = 'Create Campaign'
        return context


class CampaignUpdateView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = 'campaigns/form.html'
    success_url = reverse_lazy('campaign-list')
    success_message = "Campaign '%(name)s' updated successfully!"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Edit Campaign: {self.object.name}'
        context['submit_text'] = 'Update Campaign'
        return context


class CampaignDeleteView(LoginRequiredMixin, StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Campaign
    template_name = 'campaigns/confirm_delete.html'
    success_url = reverse_lazy('campaign-list')
    success_message = "Campaign deleted successfully!"
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)




class CustomerListView(ViewPermissionMixin, ListView):
    model = Customer
    template_name = 'campaigns/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Customer.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer_id__icontains=search) |
                Q(name__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset


class CustomerCreateView(ViewPermissionMixin, StaffRequiredMixin, SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'campaigns/customer_form.html'
    success_url = reverse_lazy('customer-list')
    success_message = "Customer '%(name)s' created successfully!"


class CustomerUpdateView(ViewPermissionMixin, StaffRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'campaigns/customer_form.html'
    success_url = reverse_lazy('customer-list')
    success_message = "Customer '%(name)s' updated successfully!"


class CustomerDeleteView(ViewPermissionMixin, StaffRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Customer
    template_name = 'campaigns/customer_confirm_delete.html'
    success_url = reverse_lazy('customer-list')
    success_message = "Customer deleted successfully!"
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class UsageListView(ViewPermissionMixin, ListView):
    model = CampaignUsage
    template_name = 'campaigns/usage_list.html'
    context_object_name = 'usage_records'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CampaignUsage.objects.all().select_related('campaign', 'customer').order_by('-usage_date', '-updated_at')
        
        campaign_id = self.request.GET.get('campaign')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        customer_id = self.request.GET.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer__customer_id__icontains=customer_id)
        
        usage_date = self.request.GET.get('usage_date')
        if usage_date:
            queryset = queryset.filter(usage_date=usage_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campaigns'] = Campaign.objects.all().order_by('name')
        return context


class ApplyDiscountTemplateView(ViewPermissionMixin, FormView):
    template_name = 'campaigns/apply_discount.html'
    
    def get(self, request, *args, **kwargs):
        context = {
            'customer_id': request.GET.get('customer_id', ''),
            'cart_total': request.GET.get('cart_total', ''),
            'delivery_fee': request.GET.get('delivery_fee', ''),
        }
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        customer_id = request.POST.get('customer_id')
        cart_total = request.POST.get('cart_total')
        delivery_fee = request.POST.get('delivery_fee')
        campaign_ids = request.POST.getlist('campaign_ids')
        action = request.POST.get('action')
        
        if not customer_id or not cart_total or not delivery_fee:
            messages.error(request, 'Please fill in all required fields')
            return self.render_to_response(self.get_context_data())
        
        try:
            cart_total = Decimal(cart_total)
            delivery_fee = Decimal(delivery_fee)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid cart total or delivery fee')
            return self.render_to_response(self.get_context_data())
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            messages.error(request, f'Customer with ID {customer_id} not found')
            return self.render_to_response(self.get_context_data())
        
        today = date.today()
        available_campaigns = Campaign.objects.filter(
            targeted_customers=customer,
            is_active=True,
            start_date__lte=today,
            end_date__gte=today
        ).prefetch_related('targeted_customers')
        
        applicable_campaigns = []
        unavailable_campaigns = []
        
        for campaign in available_campaigns:
            if campaign.consumed_budget >= campaign.total_budget:
                unavailable_campaigns.append({
                    'campaign': campaign,
                    'reason': f'Budget exhausted (₹{campaign.total_budget} fully consumed)'
                })
                continue
            
            current_usage = self._get_customer_usage_today(campaign, customer)
            if current_usage >= campaign.max_transactions_per_customer_per_day:
                unavailable_campaigns.append({
                    'campaign': campaign,
                    'reason': f'Daily usage limit reached ({current_usage}/{campaign.max_transactions_per_customer_per_day} uses today)'
                })
                continue
            
            remaining_budget = campaign.total_budget - campaign.consumed_budget
            campaign.remaining_budget = remaining_budget
            applicable_campaigns.append(campaign)
        
        # Show info messages for unavailable campaigns
        if unavailable_campaigns:
            for item in unavailable_campaigns:
                messages.info(request, f"{item['campaign'].name}: {item['reason']}")
        
        # Show warning if no campaigns are available
        if not applicable_campaigns and available_campaigns:
            messages.warning(request, 'All targeted campaigns are currently unavailable due to budget or usage limits.')
        elif not available_campaigns:
            messages.info(request, 'No active campaigns are currently targeting this customer.')
        
        context = {
            'customer_id': customer_id,
            'cart_total': cart_total,
            'delivery_fee': delivery_fee,
            'available_campaigns': applicable_campaigns,
            'unavailable_campaigns': unavailable_campaigns,
        }
        
        if action == 'preview' and campaign_ids:
            result = self._preview_discounts(customer, cart_total, delivery_fee, campaign_ids)
            context.update({
                'show_results': True,
                'result': result,
                'applied': False
            })
        elif action == 'apply' and campaign_ids:
            result = self._apply_discounts(customer, cart_total, delivery_fee, campaign_ids)
            if result.get('success'):
                messages.success(request, 'Discounts applied successfully!')
                context.update({
                    'show_results': True,
                    'result': result['data'],
                    'applied': True
                })
            else:
                messages.error(request, result.get('message', 'Failed to apply discounts'))
        
        return self.render_to_response(context)
    
    def _get_customer_usage_today(self, campaign, customer):
        today = date.today()
        usage = CampaignUsage.objects.filter(campaign=campaign, customer=customer, usage_date=today).first()
        return usage.usage_count if usage else 0
    
    def _preview_discounts(self, customer, cart_total, delivery_fee, campaign_ids):
        applied_discounts = []
        total_cart_discount = Decimal('0')
        total_delivery_discount = Decimal('0')
        
        for campaign_id in campaign_ids:
            try:
                campaign = Campaign.objects.get(id=campaign_id)
                remaining_budget = campaign.total_budget - campaign.consumed_budget
                
                if campaign.discount_type == Campaign.DISCOUNT_TYPE_CART:
                    applicable_amount = min(campaign.discount_value, cart_total, remaining_budget)
                    total_cart_discount += applicable_amount
                else:
                    applicable_amount = min(campaign.discount_value, delivery_fee, remaining_budget)
                    total_delivery_discount += applicable_amount
                
                applied_discounts.append({
                    'campaign_id': campaign.id,
                    'campaign_name': campaign.name,
                    'discount_type': campaign.discount_type,
                    'discount_applied': float(applicable_amount)
                })
            except Campaign.DoesNotExist:
                continue
        
        final_cart_total = cart_total - total_cart_discount
        final_delivery_fee = delivery_fee - total_delivery_discount
        final_amount = final_cart_total + final_delivery_fee
        
        return {
            'customer': customer,
            'original_cart_total': float(cart_total),
            'original_delivery_fee': float(delivery_fee),
            'total_cart_discount': float(total_cart_discount),
            'total_delivery_discount': float(total_delivery_discount),
            'final_cart_total': float(final_cart_total),
            'final_delivery_fee': float(final_delivery_fee),
            'final_amount': float(final_amount),
            'applied_discounts': applied_discounts
        }
    
    def _apply_discounts(self, customer, cart_total, delivery_fee, campaign_ids):
        today = date.today()
        applied_discounts = []
        total_cart_discount = Decimal('0')
        total_delivery_discount = Decimal('0')
        
        try:
            with transaction.atomic():
                for campaign_id in campaign_ids:
                    campaign = Campaign.objects.select_for_update().get(id=campaign_id)
                    
                    if not campaign.is_active:
                        return {'success': False, 'message': f"Campaign '{campaign.name}' is not active"}
                    
                    if not (campaign.start_date <= today <= campaign.end_date):
                        return {'success': False, 'message': f"Campaign '{campaign.name}' is not within valid date range"}
                    
                    usage, created = CampaignUsage.objects.get_or_create(
                        campaign=campaign, customer=customer, usage_date=today,
                        defaults={'usage_count': 0}
                    )
                    
                    if usage.usage_count >= campaign.max_transactions_per_customer_per_day:
                        return {'success': False, 'message': f"Daily usage limit exceeded for campaign '{campaign.name}'"}
                    
                    remaining_budget = campaign.total_budget - campaign.consumed_budget
                    
                    if campaign.discount_type == Campaign.DISCOUNT_TYPE_CART:
                        applicable_amount = min(campaign.discount_value, cart_total, remaining_budget)
                        total_cart_discount += applicable_amount
                    else:
                        applicable_amount = min(campaign.discount_value, delivery_fee, remaining_budget)
                        total_delivery_discount += applicable_amount
                    
                    if applicable_amount <= 0:
                        return {'success': False, 'message': f"No budget available for campaign '{campaign.name}'"}
                    
                    campaign.consumed_budget = F('consumed_budget') + applicable_amount
                    campaign.save(update_fields=['consumed_budget'])
                    
                    usage.usage_count = F('usage_count') + 1
                    usage.save(update_fields=['usage_count'])
                    
                    campaign.refresh_from_db()
                    usage.refresh_from_db()
                    
                    applied_discounts.append({
                        'campaign_id': campaign.id,
                        'campaign_name': campaign.name,
                        'discount_type': campaign.discount_type,
                        'discount_applied': float(applicable_amount)
                    })
            
            final_cart_total = cart_total - total_cart_discount
            final_delivery_fee = delivery_fee - total_delivery_discount
            final_amount = final_cart_total + final_delivery_fee
            
            return {
                'success': True,
                'data': {
                    'customer': customer,
                    'original_cart_total': float(cart_total),
                    'original_delivery_fee': float(delivery_fee),
                    'total_cart_discount': float(total_cart_discount),
                    'total_delivery_discount': float(total_delivery_discount),
                    'final_cart_total': float(final_cart_total),
                    'final_delivery_fee': float(final_delivery_fee),
                    'final_amount': float(final_amount),
                    'applied_discounts': applied_discounts
                }
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class DiscountPreviewView(ViewPermissionMixin, FormView):
    template_name = 'discounts/preview.html'
    form_class = DiscountPreviewForm
    
    def form_valid(self, form):
        customer_id = form.cleaned_data['customer_id']
        cart_total = form.cleaned_data['cart_total']
        delivery_fee = form.cleaned_data['delivery_fee']
        customer = Customer.objects.get(customer_id=customer_id)
        today = date.today()
        all_campaigns = Campaign.objects.filter(targeted_customers=customer).prefetch_related('targeted_customers')
        
        applicable_campaigns = []
        not_applicable_campaigns = []
        
        for campaign in all_campaigns:
            if not self._is_campaign_valid(campaign):
                reason = self._get_invalid_reason(campaign, today)
                not_applicable_campaigns.append({'campaign': campaign, 'reason': reason})
                continue
            
            if not self._can_customer_use_today(campaign, customer):
                not_applicable_campaigns.append({
                    'campaign': campaign,
                    'reason': f'Daily limit exceeded ({campaign.max_transactions_per_customer_per_day} uses per day)'
                })
                continue
            
            remaining_budget = campaign.total_budget - campaign.consumed_budget
            if campaign.discount_type == Campaign.DISCOUNT_TYPE_CART:
                applicable_amount = min(campaign.discount_value, cart_total, remaining_budget)
            else:
                applicable_amount = min(campaign.discount_value, delivery_fee, remaining_budget)
            
            applicable_campaigns.append({'campaign': campaign, 'applicable_discount': applicable_amount})
        
        context = self.get_context_data(form=form)
        context.update({
            'customer': customer,
            'cart_total': cart_total,
            'delivery_fee': delivery_fee,
            'applicable_campaigns': applicable_campaigns,
            'not_applicable_campaigns': not_applicable_campaigns,
            'show_results': True
        })
        return self.render_to_response(context)
    
    def _is_campaign_valid(self, campaign):
        if not campaign.is_active:
            return False
        today = date.today()
        if not (campaign.start_date <= today <= campaign.end_date):
            return False
        if campaign.consumed_budget >= campaign.total_budget:
            return False
        return True
    
    def _can_customer_use_today(self, campaign, customer):
        current_usage = self._get_customer_usage_today(campaign, customer)
        return current_usage < campaign.max_transactions_per_customer_per_day
    
    
    def _get_customer_usage_today(self, campaign, customer):
        today = date.today()
        usage = CampaignUsage.objects.filter(campaign=campaign, customer=customer, usage_date=today).first()
        return usage.usage_count if usage else 0
    
    def _get_invalid_reason(self, campaign, today):
        if not campaign.is_active:
            return 'Campaign is not active'
        if today < campaign.start_date:
            return f'Campaign starts on {campaign.start_date}'
        if today > campaign.end_date:
            return f'Campaign ended on {campaign.end_date}'
        if campaign.consumed_budget >= campaign.total_budget:
            return 'Campaign budget exhausted'
        return 'Campaign is not valid'



class ApplyDiscountView(APIView):
    permission_classes = [IsStaffUser]
    
    @swagger_auto_schema(
        operation_description="Apply discount campaigns to an order and update budget/usage tracking",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['customer_id', 'cart_total', 'delivery_fee', 'campaign_ids'],
            properties={
                'customer_id': openapi.Schema(type=openapi.TYPE_STRING, description='Customer unique ID'),
                'cart_total': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total cart value'),
                'delivery_fee': openapi.Schema(type=openapi.TYPE_NUMBER, description='Delivery fee amount'),
                'campaign_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description='List of campaign IDs to apply'),
            }
        ),
        responses={
            200: 'Discount applied successfully',
            400: 'Bad Request',
            404: 'Customer or Campaign not found'
        }
    )
    def post(self, request):
        customer_id = request.data.get('customer_id')
        cart_total = request.data.get('cart_total')
        delivery_fee = request.data.get('delivery_fee')
        campaign_ids = request.data.get('campaign_ids', [])
        
        if not customer_id:
            return api_response(success=False, message="customer_id is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if cart_total is None:
            return api_response(success=False, message="cart_total is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if delivery_fee is None:
            return api_response(success=False, message="delivery_fee is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if not campaign_ids:
            return api_response(success=False, message="campaign_ids is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_total = Decimal(str(cart_total))
            delivery_fee = Decimal(str(delivery_fee))
        except (ValueError, TypeError):
            return api_response(success=False, message="cart_total and delivery_fee must be valid numbers", status_code=status.HTTP_400_BAD_REQUEST)
        
        if cart_total < 0 or delivery_fee < 0:
            return api_response(success=False, message="cart_total and delivery_fee must be non-negative", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return api_response(success=False, message=f"Customer with ID {customer_id} not found", status_code=status.HTTP_404_NOT_FOUND)
        
        today = date.today()
        applied_discounts = []
        total_cart_discount = Decimal('0')
        total_delivery_discount = Decimal('0')
        
        with transaction.atomic():
            for campaign_id in campaign_ids:
                try:
                    campaign = Campaign.objects.select_for_update().get(id=campaign_id)
                except Campaign.DoesNotExist:
                    return api_response(success=False, message=f"Campaign with ID {campaign_id} not found", status_code=status.HTTP_404_NOT_FOUND)
                
                if not campaign.is_active:
                    return api_response(success=False, message=f"Campaign '{campaign.name}' is not active", status_code=status.HTTP_400_BAD_REQUEST)
                
                if not (campaign.start_date <= today <= campaign.end_date):
                    return api_response(success=False, message=f"Campaign '{campaign.name}' is not within valid date range", status_code=status.HTTP_400_BAD_REQUEST)
                
                if not campaign.targeted_customers.filter(id=customer.id).exists():
                    return api_response(success=False, message=f"Customer not eligible for campaign '{campaign.name}'", status_code=status.HTTP_400_BAD_REQUEST)
                
                usage, created = CampaignUsage.objects.get_or_create(
                    campaign=campaign, customer=customer, usage_date=today,
                    defaults={'usage_count': 0}
                )
                
                if usage.usage_count >= campaign.max_transactions_per_customer_per_day:
                    return api_response(success=False, message=f"Daily usage limit exceeded for campaign '{campaign.name}'", status_code=status.HTTP_400_BAD_REQUEST)
                
                remaining_budget = campaign.total_budget - campaign.consumed_budget
                
                if campaign.discount_type == Campaign.DISCOUNT_TYPE_CART:
                    applicable_amount = min(campaign.discount_value, cart_total, remaining_budget)
                    total_cart_discount += applicable_amount
                else:
                    applicable_amount = min(campaign.discount_value, delivery_fee, remaining_budget)
                    total_delivery_discount += applicable_amount
                
                if applicable_amount <= 0:
                    return api_response(success=False, message=f"No budget available for campaign '{campaign.name}'", status_code=status.HTTP_400_BAD_REQUEST)
                
                campaign.consumed_budget = F('consumed_budget') + applicable_amount
                campaign.save(update_fields=['consumed_budget'])
                
                usage.usage_count = F('usage_count') + 1
                usage.save(update_fields=['usage_count'])
                
                campaign.refresh_from_db()
                usage.refresh_from_db()
                
                applied_discounts.append({
                    'campaign_id': campaign.id,
                    'campaign_name': campaign.name,
                    'discount_type': campaign.discount_type,
                    'discount_applied': float(applicable_amount)
                })
        
        final_cart_total = cart_total - total_cart_discount
        final_delivery_fee = delivery_fee - total_delivery_discount
        final_amount = final_cart_total + final_delivery_fee
        
        response_data = {
            'customer_id': customer_id,
            'original_cart_total': float(cart_total),
            'original_delivery_fee': float(delivery_fee),
            'total_cart_discount': float(total_cart_discount),
            'total_delivery_discount': float(total_delivery_discount),
            'final_cart_total': float(final_cart_total),
            'final_delivery_fee': float(final_delivery_fee),
            'final_amount': float(final_amount),
            'applied_discounts': applied_discounts
        }
        
        return api_response(success=True, message="Discounts applied successfully", data=response_data, status_code=status.HTTP_200_OK)
    
    def _get_invalid_reason(self, campaign, today):
        if not campaign.is_active:
            return 'Campaign is inactive'
        if today < campaign.start_date:
            return f'Campaign starts on {campaign.start_date}'
        if today > campaign.end_date:
            return f'Campaign expired on {campaign.end_date}'
        if campaign.consumed_budget >= campaign.total_budget:
            return 'Campaign budget exhausted'
        return 'Campaign not valid'
