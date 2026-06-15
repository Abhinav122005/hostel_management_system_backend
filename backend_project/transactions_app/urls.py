from django.urls import path
from . import views

urlpatterns = [
    # Initiate a new transaction
    path("initiate/", views.initiate_transaction, name="initiate_transaction"),
    # Verify a PayU payment
    path("verify/", views.verify_payu_payment, name="verify_payu_payment"),
    # Get all transactions for a specific user
    path("user/<int:user_id>/", views.get_user_transactions, name="get_user_transactions"),
    # Get all transactions for a specific owner
    path("owner/<int:owner_id>/", views.get_owner_transactions, name="get_owner_transactions"),
]
