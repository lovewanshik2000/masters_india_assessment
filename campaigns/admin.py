from django.contrib import admin
from .models import Customer, Campaign, CampaignUsage


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'name', 'email', 'created_at']
    search_fields = ['customer_id', 'name', 'email']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'discount_type', 'discount_value', 'start_date', 'end_date',
        'total_budget', 'consumed_budget', 'is_active', 'is_valid'
    ]
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['consumed_budget', 'created_at', 'updated_at']
    filter_horizontal = ['targeted_customers']
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'description', 'is_active')}),
        ('Discount Details', {'fields': ('discount_type', 'discount_value')}),
        ('Date Range', {'fields': ('start_date', 'end_date')}),
        ('Budget', {'fields': ('total_budget', 'consumed_budget')}),
        ('Constraints', {'fields': ('max_transactions_per_customer_per_day', 'targeted_customers')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(CampaignUsage)
class CampaignUsageAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'customer', 'usage_date', 'usage_count', 'updated_at']
    list_filter = ['usage_date', 'campaign']
    search_fields = ['campaign__name', 'customer__customer_id', 'customer__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'usage_date'
