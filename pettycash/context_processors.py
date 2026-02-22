#context_processors.py
from .models import Notification
from finance.models import PettyCashFund

def notifications_processor(request):

    if not request.user.is_authenticated:
        return {}

    unread = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by("-created_at")

    # ==========================================
    # CHECK IF CUSTODIAN HAS ACTIVE FUND
    # ==========================================
    has_active_fund = False

    if request.user.groups.filter(name="Custodian").exists():
        has_active_fund = PettyCashFund.objects.filter(
            custodian=request.user,
            is_active=True
        ).exists()

    return {
        "notifications": unread[:5],
        "unread_notifications_count": unread.count(),
        "has_active_fund": has_active_fund,
    }
