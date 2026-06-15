import uuid
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from owners.models import Owner
from users.models import User
from .models import Transaction
from .serializers import TransactionCreateSerializer, TransactionSerializer
from .utils import generate_payu_hash, verify_payu_hash

@api_view(["POST"])
def initiate_transaction(request):
    """
    Creates a pending transaction and generates the hash required for the frontend
    to send to PayU.
    
    Expected JSON Payload:
    {
      "userId": 1,
      "ownerId": 2,
      "hostelId": 1,
      "amount": 5000,
      "paymentType": "Booking",
      "description": "Payment for booking"
    }
    """
    serializer = TransactionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    data = serializer.validated_data
    owner = Owner.objects.get(id=data["ownerId"])
    user = User.objects.get(id=data["userId"])
    
    if not owner.payu_key or not owner.payu_salt:
        return Response({"message": "Owner has not configured PayU"}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a unique local transaction ID
    local_txnid = f"TXN_{uuid.uuid4().hex[:10].upper()}"
    
    with transaction.atomic():
        txn = Transaction.objects.create(
            user_id=data["userId"],
            owner_id=data["ownerId"],
            hostel_id=data["hostelId"],
            amount=data["amount"],
            payment_type=data["paymentType"],
            description=data.get("description", ""),
            status="pending"
        )
        
        # PayU product info can be our internal ID or a string
        productinfo = f"Hostel Payment - {txn.id}"
        
        # Generate the hash to send to frontend
        txn_hash = generate_payu_hash(
            key=owner.payu_key,
            txnid=local_txnid,
            amount=str(data["amount"]),
            productinfo=productinfo,
            firstname=user.name or "User",
            email=user.email,
            salt=owner.payu_salt
        )
        
        txn.payu_hash = txn_hash
        txn.transaction_id = local_txnid # Storing our generated txnid
        txn.save()

    return Response(
        {
            "message": "Transaction initiated",
            "transaction": TransactionSerializer(txn).data,
            "payuParams": {
                "key": owner.payu_key,
                "txnid": local_txnid,
                "amount": str(data["amount"]),
                "productinfo": productinfo,
                "firstname": user.name or "User",
                "email": user.email,
                "hash": txn_hash
            }
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["POST"])
def verify_payu_payment(request):
    """
    Webhook/Callback endpoint for PayU to send success/failure status.
    It securely verifies the hash sent by PayU.
    
    Expected JSON Payload:
    {
      "txnid": "TXN_12345",
      "hash": "abcdef...",
      "status": "success",
      "key": "...",
      "amount": 5000,
      "productinfo": "Hostel Payment...",
      "firstname": "John",
      "email": "john@example.com"
    }
    """
    data = request.data
    txnid = data.get("txnid")
    posted_hash = data.get("hash")
    payu_status = data.get("status")
    
    if not txnid or not posted_hash:
        return Response({"message": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        txn = Transaction.objects.get(transaction_id=txnid)
    except Transaction.DoesNotExist:
        return Response({"message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
        
    owner = txn.owner
    
    # Recreate the hash based on the payload received
    is_valid = verify_payu_hash(
        key=data.get("key"),
        txnid=txnid,
        amount=data.get("amount"),
        productinfo=data.get("productinfo"),
        firstname=data.get("firstname"),
        email=data.get("email"),
        status=payu_status,
        salt=owner.payu_salt,
        posted_hash=posted_hash
    )
    
    if not is_valid:
        return Response({"message": "Hash verification failed. Potential tampering."}, status=status.HTTP_400_BAD_REQUEST)
        
    # If valid, update status
    with transaction.atomic():
        if payu_status.lower() == "success":
            txn.status = "success"
        else:
            txn.status = "failed"
        txn.save()
        
    return Response(
        {
            "message": f"Transaction marked as {txn.status}",
            "transaction": TransactionSerializer(txn).data
        },
        status=status.HTTP_200_OK
    )

@api_view(["GET"])
def get_user_transactions(request, user_id):
    transactions = Transaction.objects.filter(user_id=user_id).select_related("user", "hostel")
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["GET"])
def get_owner_transactions(request, owner_id):
    transactions = Transaction.objects.filter(owner_id=owner_id).select_related("user", "hostel")
    serializer = TransactionSerializer(transactions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
