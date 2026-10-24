
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile
from .models import Item, Bid
from django.utils import timezone
from django.contrib.auth import logout
from notifications.models import Notification
import uuid
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from .models import Item, Bid, Payment
from django.db.models import Max
from .fraud_detection import check_bid_for_fraud
from decimal import Decimal, InvalidOperation


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



@login_required
def buyer_dashboard(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")[:5]

    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    items = Item.objects.filter(status='approved')

    # Find items won by the logged-in buyer
    won_items = Item.objects.filter(
        winner=request.user
    )

    # Also find ended auctions whose winner has not yet been declared
    ended_items = Item.objects.filter(
        end_time__lte=timezone.now(),
        status='approved'
    )

    for item in ended_items:
        highest_bid = Bid.objects.filter(
            item=item
        ).order_by('-amount', '-timestamp').first()

        if highest_bid:
            item.winner = highest_bid.buyer
            item.save(update_fields=['winner'])

    won_items = Item.objects.filter(winner=request.user)

    return render(request, 'buyer.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'items': items,
        'won_items': won_items,
    })



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



@login_required
def place_bid(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    message = ""
    now = timezone.now()

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', ''))
        except (InvalidOperation, TypeError, ValueError):
            amount = Decimal('0')
            message = "Please enter a valid bid amount."

        if not message and (not amount.is_finite() or amount <= 0):
            message = "Bid amount must be a positive number."

        elif not message and now < item.start_time:
            message = "Auction has not started yet!"

        elif not message and now >= item.end_time:
            message = "Auction has ended!"

        elif not message:
            highest_bid = Bid.objects.filter(
                item=item
            ).order_by('-amount', '-timestamp').first()

            if highest_bid and amount <= Decimal(str(highest_bid.amount)):
                message = "Bid must be higher than the current highest bid!"

            elif not highest_bid and amount < Decimal(str(item.base_price)):
                message = "Bid must be at least the base price!"

            else:
                new_bid = Bid.objects.create(
                    item=item,
                    buyer=request.user,
                    amount=amount,
                )

                # Notify the previous highest bidder.
                if highest_bid and highest_bid.buyer != request.user:
                    Notification.objects.create(
                        recipient=highest_bid.buyer,
                        message=(
                            f"You have been outbid on {item.name}! "
                            f"The new bid is ₹{amount:.2f}."
                        ),
                        notification_type="outbid"
                    )

                # Automatically check the new bid for suspicious patterns.
                try:
                    alerts = check_bid_for_fraud(new_bid)

                    if alerts:
                        message = (
                            "Bid placed successfully! "
                            "This activity has been flagged for review."
                        )
                    else:
                        message = "Bid placed successfully!"

                except Exception:
                    # Do not tell the user that fraud detection succeeded
                    # if the fraud check encountered an error.
                    message = (
                        "Bid placed successfully, but the fraud check "
                        "could not be completed."
                    )

    highest_bid = Bid.objects.filter(
        item=item
    ).order_by('-amount', '-timestamp').first()

    bids = Bid.objects.filter(
        item=item
    ).order_by('-amount', '-timestamp')

    return render(request, 'bid.html', {
        'item': item,
        'message': message,
        'highest_bid': highest_bid,
        'bids': bids,
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

@login_required
def payment_checkout(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Only the declared winner can pay
    if item.winner != request.user:
        return render(request, 'payment_error.html', {
            'message': 'Only the auction winner can make this payment.'
        })

    highest_bid = Bid.objects.filter(
        item=item
    ).order_by('-amount', '-timestamp').first()

    if not highest_bid or highest_bid.buyer != request.user:
        return render(request, 'payment_error.html', {
            'message': 'No valid winning bid was found.'
        })

    # Prevent paying twice
    if Payment.objects.filter(
        item=item,
        status='success'
    ).exists():
        return render(request, 'payment_error.html', {
            'message': 'This item has already been paid for.'
        })

    return render(request, 'payment_checkout.html', {
        'item': item,
        'amount': Decimal(str(highest_bid.amount)),
    })


@login_required
@require_POST
def process_payment(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    # Verify the winner again on submission
    if item.winner != request.user:
        return render(request, 'payment_error.html', {
            'message': 'You are not authorized to pay for this item.'
        })

    highest_bid = Bid.objects.filter(
        item=item
    ).order_by('-amount', '-timestamp').first()

    if not highest_bid or highest_bid.buyer != request.user:
        return render(request, 'payment_error.html', {
            'message': 'No valid winning bid was found.'
        })

    if Payment.objects.filter(item=item, status='success').exists():
        return render(request, 'payment_error.html', {
            'message': 'This item has already been paid for.'
        })

    payment_method = request.POST.get('payment_method')
    outcome = request.POST.get('outcome')

    valid_methods = ['upi', 'card', 'netbanking']

    if payment_method not in valid_methods or outcome not in ['success', 'failed']:
        return render(request, 'payment_error.html', {
            'message': 'Invalid payment option.'
        })

    payment = Payment.objects.create(
        item=item,
        buyer=request.user,
        amount=Decimal(str(highest_bid.amount)),
        payment_method=payment_method,
        status=outcome,
        transaction_id=f"SIM-{uuid.uuid4().hex[:16].upper()}",
    )

    return render(request, 'payment_result.html', {
        'payment': payment,
        'item': item,
    })


def user_logout(request):
    logout(request)
    return redirect('login')