from django import forms
from django.core.exceptions import ValidationError
from .models import Campaign, Customer
from datetime import date


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'email']
        widgets = {
            'customer_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CUST001'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@example.com'}),
        }


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'discount_type', 'discount_value',
            'start_date', 'end_date', 'total_budget',
            'max_transactions_per_customer_per_day', 'targeted_customers', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter campaign name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter campaign description'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'max_transactions_per_customer_per_day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': '1'}),
            'targeted_customers': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        help_texts = {
            'discount_type': 'Choose whether discount applies to cart or delivery',
            'discount_value': 'Flat discount amount',
            'start_date': 'Campaign start date',
            'end_date': 'Campaign end date (must be after start date)',
            'total_budget': 'Total budget allocated for this campaign',
            'max_transactions_per_customer_per_day': 'Maximum uses per customer per day',
            'targeted_customers': 'Hold Ctrl/Cmd to select multiple customers',
            'is_active': 'Uncheck to deactivate campaign'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        discount_value = cleaned_data.get('discount_value')
        total_budget = cleaned_data.get('total_budget')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({'end_date': 'End date must be after start date.'})
        
        if discount_value and discount_value <= 0:
            raise ValidationError({'discount_value': 'Discount value must be greater than zero.'})
        
        if total_budget and total_budget <= 0:
            raise ValidationError({'total_budget': 'Total budget must be greater than zero.'})
        
        return cleaned_data


class DiscountPreviewForm(forms.Form):
    customer_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your customer ID (e.g., CUST001)'}),
        help_text='Your unique customer identifier'
    )
    
    cart_total = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
        help_text='Total cart value'
    )
    
    delivery_fee = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
        help_text='Delivery fee amount'
    )
    
    def clean_customer_id(self):
        customer_id = self.cleaned_data.get('customer_id')
        if not Customer.objects.filter(customer_id=customer_id).exists():
            raise ValidationError(f'Customer with ID "{customer_id}" not found. Please check your customer ID.')
        return customer_id
