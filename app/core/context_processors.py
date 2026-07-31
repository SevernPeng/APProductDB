from accounts.permissions import account_role, can_review, is_root

from .permissions import can_contribute


def role_capabilities(request):
    return {
        "can_contribute": can_contribute(request.user),
        "can_review_changes": can_review(request.user),
        "can_manage_accounts": is_root(request.user),
        "account_role": account_role(request.user),
    }
