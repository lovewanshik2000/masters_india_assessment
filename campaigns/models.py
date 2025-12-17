from django.db import models
from django.core.validators import MinValueValidator


class Customer(models.Model):
    customer_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.name} ({self.customer_id})"


class Campaign(models.Model):
    DISCOUNT_TYPE_CART = 'CART'
    DISCOUNT_TYPE_DELIVERY = 'DELIVERY'
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_CART, 'Cart Discount'),
        (DISCOUNT_TYPE_DELIVERY, 'Delivery Discount'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    consumed_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    max_transactions_per_customer_per_day = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    targeted_customers = models.ManyToManyField(Customer, related_name='campaigns')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Campaign'
        verbose_name_plural = 'Campaigns'
        indexes = [
            models.Index(fields=['discount_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def is_valid(self):
        from datetime import date
        today = date.today()
        return (
            self.is_active and
            self.start_date <= today <= self.end_date and
            self.consumed_budget < self.total_budget
        )

    def can_customer_use_today(self, customer):
        from datetime import date
        today = date.today()
        try:
            usage = self.usages.get(customer=customer, usage_date=today)
            return usage.usage_count < self.max_transactions_per_customer_per_day
        except CampaignUsage.DoesNotExist:
            return True

    def has_budget_for_discount(self, discount_amount):
        return (self.total_budget - self.consumed_budget) >= discount_amount

    def is_customer_eligible(self, customer):
        return self.targeted_customers.filter(id=customer.id).exists()


class CampaignUsage(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='usages')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='campaign_usages')
    usage_date = models.DateField()
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Campaign Usage'
        verbose_name_plural = 'Campaign Usages'
        unique_together = [['campaign', 'customer', 'usage_date']]
        indexes = [
            models.Index(fields=['campaign', 'customer', 'usage_date']),
            models.Index(fields=['usage_date']),
        ]
        ordering = ['-usage_date', '-updated_at']
    
    def __str__(self):
        return f"{self.campaign.name} - {self.customer.customer_id} - {self.usage_date} ({self.usage_count})"
