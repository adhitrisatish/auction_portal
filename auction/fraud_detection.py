
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from .models import Bid, FraudAlert


def check_bid_for_fraud(bid):
    """
    Examine a newly placed bid and create a FraudAlert
    if suspicious bidding patterns are detected.
    """

    alerts = []
    risk_score = 0

    # Check recent bids made by the same buyer on this item.
    recent_bids = Bid.objects.filter(
        item=bid.item,
        buyer=bid.buyer,
        timestamp__gte=timezone.now() - timedelta(seconds=30),
    ).exclude(id=bid.id)

    recent_count = recent_bids.count()

    if recent_count >= 4:
        alerts.append(
            f"Rapid bidding: {recent_count + 1} bids "
            "by this buyer on the item within 30 seconds."
        )
        risk_score += 40

    # Compare the new bid with the immediately previous highest bid.
    previous_bid = (
        Bid.objects.filter(item=bid.item)
        .exclude(id=bid.id)
        .order_by("-amount", "-timestamp")
        .first()
    )

    if previous_bid and previous_bid.amount > 0:
        increase = (
            Decimal(str(bid.amount))
            - Decimal(str(previous_bid.amount))
        ) / Decimal(str(previous_bid.amount))

        if increase >= Decimal("2.00"):
            alerts.append(
                "Unusual bid jump: the new bid is at least "
                "200% higher than the previous highest bid."
            )
            risk_score += 35

    # Check for repeated bids by the same buyer across this auction.
    all_buyer_bids = Bid.objects.filter(
        item=bid.item,
        buyer=bid.buyer,
    ).count()

    if all_buyer_bids >= 6:
        alerts.append(
            f"Repeated bidding: this buyer has placed "
            f"{all_buyer_bids} bids on this item."
        )
        risk_score += 25

    # Cap the score at 100.
    risk_score = min(risk_score, 100)

    if not alerts:
        return []

    if risk_score >= 60:
        severity = "high"
    elif risk_score >= 30:
        severity = "medium"
    else:
        severity = "low"

    created_alerts = []

    # Store one alert for each detected reason.
    for reason in alerts:
        alert = FraudAlert.objects.create(
            bid=bid,
            item=bid.item,
            user=bid.buyer,
            reason=reason,
            risk_score=risk_score,
            severity=severity,
            status="pending",
        )
        created_alerts.append(alert)

    return created_alerts
