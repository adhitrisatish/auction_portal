from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),

    path('buyer/', views.buyer_dashboard, name='buyer'),
    path('seller/', views.seller_dashboard, name='seller'),
    path('auctioneer/', views.auctioneer_dashboard, name='auctioneer'),

    path('items/', views.buyer_items, name='items'),
    path('add-item/', views.add_item, name='add_item'),
    path('bid/<int:item_id>/', views.place_bid, name='bid'),
    path('approve/<int:item_id>/', views.approve_item, name='approve'),
    path('winner/<int:item_id>/', views.declare_winner, name='winner'),
    path('logout/', views.user_logout, name='logout'),
    path(
    'payment/<int:item_id>/',
    views.payment_checkout,
    name='payment_checkout'
),
path(
    'payment/<int:item_id>/process/',
    views.process_payment,
    name='process_payment'
),
]

