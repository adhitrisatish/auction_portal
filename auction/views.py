
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile
from .models import Item, Bid
from django.utils import timezone
from django.contrib.auth import logout


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']

        user = User.objects.create_user(username=username, password=password)

        profile = Profile.objects.get(user=user)
        profile.role = role
        profile.save()

        return redirect('login')

    return render(request, 'register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)

            # Role-based redirect
            profile = Profile.objects.get(user=user)

            if profile.role == 'buyer':
                return redirect('/buyer')
            elif profile.role == 'seller':
                return redirect('/seller')
            else:
                return redirect('/auctioneer')

    return render(request, 'login.html')

def buyer_dashboard(request):
    return render(request, 'buyer.html')

def seller_dashboard(request):
    items = Item.objects.filter(seller=request.user)

    item_data = []

    for item in items:
        bids = Bid.objects.filter(item=item).order_by('-amount')
        item_data.append({
            'item': item,
            'bids': bids
        })

    return render(request, 'seller.html', {'item_data': item_data})

def auctioneer_dashboard(request):
    return render(request, 'auctioneer.html')

from .models import Item

def add_item(request):
    if request.method == 'POST':
        Item.objects.create(
            name=request.POST['name'],
            description=request.POST['description'],
            base_price=request.POST['price'],
            seller=request.user,
            start_time=request.POST['start'],
            end_time=request.POST['end']
        )
        return redirect('/seller')

    return render(request, 'add_item.html')

def buyer_items(request):
    items = Item.objects.all()
    return render(request, 'buyer_items.html', {'items': items})

def place_bid(request, item_id):
    item = Item.objects.get(id=item_id)
    message = ""

    now = timezone.now()

    if request.method == 'POST':
        amount = float(request.POST['amount'])

        if now < item.start_time:
            message = "Auction has not started yet!"
        elif now > item.end_time:
            message = "Auction has ended!"
        else:
            # existing bidding logic here
            highest_bid = Bid.objects.filter(item=item).order_by('-amount').first()

            if highest_bid:
                if amount > highest_bid.amount:
                    Bid.objects.create(
                        item=item,
                        buyer=request.user,
                        amount=amount
                    )
                    message = "Bid placed successfully!"
                else:
                    message = "Bid must be higher than current highest bid!"
            else:
                if amount >= item.base_price:
                    Bid.objects.create(
                        item=item,
                        buyer=request.user,
                        amount=amount
                    )
                    message = "Bid placed successfully!"
                else:
                    message = "Bid must be at least the base price!"

    highest_bid = Bid.objects.filter(item_id=item_id).order_by('-amount').first()
    bids = Bid.objects.filter(item_id=item_id).order_by('-amount')

    return render(request, 'bid.html', {
        'item': item,
        'message': message,
        'highest_bid': highest_bid,
        'bids': bids
    })

def auctioneer_dashboard(request):
    items = Item.objects.all()
    return render(request, 'auctioneer.html', {'items': items})

def approve_item(request, item_id):
    item = Item.objects.get(id=item_id)
    item.status = 'approved'
    item.save()
    return redirect('/auctioneer/')

def buyer_items(request):
    items = Item.objects.filter(status='approved')
    return render(request, 'buyer_items.html', {'items': items})

def declare_winner(request, item_id):
    item = Item.objects.get(id=item_id)

    if timezone.now() > item.end_time:
        highest_bid = Bid.objects.filter(item_id=item_id).order_by('-amount').first()

        if highest_bid:
            item.winner = highest_bid.buyer
            item.save()

        return render(request, 'winner.html', {
            'item': item,
            'winner': highest_bid
        })

    return redirect('/auctioneer/')

def user_logout(request):
    logout(request)
    return redirect('login')