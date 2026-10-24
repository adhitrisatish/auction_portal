from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Profile (to store role)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username


# Item (auction item)
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_price = models.FloatField()
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    winner=models.ForeignKey(User,on_delete=models.SET_NULL, null=True, blank=True, related_name='won_items')

    def __str__(self):
        return self.name


# Bid (bidding system)
class Bid(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.amount}"



@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Successful'),
        ('failed', 'Failed'),
    ]

    METHOD_CHOICES = [
        ('upi', 'UPI (Simulated)'),
        ('card', 'Card (Simulated)'),
        ('netbanking', 'Net Banking (Simulated)'),
    ]

    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='auction_payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    transaction_id = models.CharField(
        max_length=40,
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - {self.status}"

class FraudAlert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    bid = models.ForeignKey(
        Bid,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fraud_alerts'
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='fraud_alerts'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fraud_alerts'
    )

    reason = models.TextField()

    risk_score = models.PositiveSmallIntegerField(default=0)

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='low'
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.severity.upper()} risk - {self.user.username}"
