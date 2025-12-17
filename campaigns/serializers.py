from rest_framework import serializers
from .models import Customer, Campaign, CampaignUsage
from datetime import date


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'customer_id', 'name', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class CampaignSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()
    remaining_budget = serializers.SerializerMethodField()
    targeted_customer_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Customer.objects.all(), source='targeted_customers', write_only=True
    )
    targeted_customers = CustomerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'start_date', 'end_date', 'total_budget', 'consumed_budget',
            'remaining_budget', 'max_transactions_per_customer_per_day',
            'targeted_customer_ids', 'targeted_customers', 'is_active',
            'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'consumed_budget', 'created_at', 'updated_at']
    
    def get_is_valid(self, obj):
        if not obj.is_active:
            return False
        today = date.today()
        if not (obj.start_date <= today <= obj.end_date):
            return False
        if obj.consumed_budget >= obj.total_budget:
            return False
        return True
    
    def get_remaining_budget(self, obj):
        return obj.total_budget - obj.consumed_budget
    
    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        
        total_budget = data.get('total_budget')
        if total_budget and total_budget <= 0:
            raise serializers.ValidationError({'total_budget': 'Total budget must be greater than zero.'})
        
        discount_value = data.get('discount_value')
        if discount_value and discount_value <= 0:
            raise serializers.ValidationError({'discount_value': 'Discount value must be greater than zero.'})
        
        return data


class CampaignUsageSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    customer_id = serializers.CharField(source='customer.customer_id', read_only=True)
    
    class Meta:
        model = CampaignUsage
        fields = [
            'id', 'campaign', 'campaign_name', 'customer', 'customer_id',
            'usage_date', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApplicableCampaignSerializer(serializers.ModelSerializer):
    remaining_budget = serializers.SerializerMethodField()
    applicable_discount = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'discount_type', 'discount_value',
            'applicable_discount', 'start_date', 'end_date', 'remaining_budget',
            'max_transactions_per_customer_per_day'
        ]
    
    def get_remaining_budget(self, obj):
        return obj.total_budget - obj.consumed_budget
    
    def get_applicable_discount(self, obj):
        context = self.context
        cart_total = context.get('cart_total', 0)
        delivery_fee = context.get('delivery_fee', 0)
        remaining_budget = obj.total_budget - obj.consumed_budget
        
        if obj.discount_type == Campaign.DISCOUNT_TYPE_CART:
            applicable_amount = min(obj.discount_value, cart_total, remaining_budget)
        else:
            applicable_amount = min(obj.discount_value, delivery_fee, remaining_budget)
        
        return applicable_amount
