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