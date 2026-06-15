import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Call
from users.models import User

# ==========================================
# Create a new call request
# ==========================================
"""
Expected JSON Request:
{
    "callerId": 1,
    "receiverId": 2
}

Expected JSON Response (201 Created):
{
    "message": "Call initiated",
    "data": {
        "id": 1,
        "callerId": 1,
        "receiverId": 2,
        "status": "ringing",
        "createdAt": "2026-06-01T10:00:00Z"
    }
}
"""
@csrf_exempt
def create_call(request):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON request
            data = json.loads(request.body)
            caller_id = data.get('callerId')
            receiver_id = data.get('receiverId')
            
            # Validate input data
            if not caller_id or not receiver_id:
                return JsonResponse({"message": "callerId and receiverId are required"}, status=400)
                
            # Fetch the users from the database
            caller = User.objects.get(id=caller_id)
            receiver = User.objects.get(id=receiver_id)
            
            # Create the call record
            call = Call.objects.create(caller=caller, receiver=receiver)
            
            # Return success response
            return JsonResponse({
                "message": "Call initiated",
                "data": call.to_dict()
            }, status=201)
            
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": "Error creating call", "error": str(e)}, status=500)
    return JsonResponse({"message": "Method not allowed"}, status=405)


# ==========================================
# Update call status
# ==========================================
"""
Expected JSON Request:
{
    "status": "accepted"  // choices: "ringing", "accepted", "declined", "missed"
}

Expected JSON Response (200 OK):
{
    "message": "Call accepted",
    "data": {
        "id": 1,
        "callerId": 1,
        "receiverId": 2,
        "status": "accepted",
        "createdAt": "2026-06-01T10:00:00Z"
    }
}
"""
@csrf_exempt
def update_call_status(request, call_id):
    if request.method == 'PUT':
        try:
            # Parse the incoming JSON request
            data = json.loads(request.body)
            status = data.get('status')
            
            # Validate status input
            if not status:
                return JsonResponse({"message": "status is required"}, status=400)
                
            # Fetch the call from the database
            call = Call.objects.get(id=call_id)
            
            # Update and save the new status
            call.status = status
            call.save()
            
            # Return success response
            return JsonResponse({
                "message": f"Call {status}",
                "data": call.to_dict()
            }, status=200)
            
        except Call.DoesNotExist:
            return JsonResponse({"message": "Call not found"}, status=404)
        except Exception as e:
            return JsonResponse({"message": "Error updating call", "error": str(e)}, status=500)
    return JsonResponse({"message": "Method not allowed"}, status=405)


# ==========================================
# Get user calls
# ==========================================
"""
Expected URL Request: GET /api/calls/user/<user_id>/

Expected JSON Response (200 OK):
[
    {
        "id": 1,
        "callerId": 1,
        "receiverId": 2,
        "status": "accepted",
        "createdAt": "2026-06-01T10:00:00Z",
        "caller": {
            "_id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "mobile": "1234567890"
        },
        "receiver": {
            "_id": 2,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "mobile": "0987654321"
        }
    }
]
"""
@csrf_exempt
def get_user_calls(request, user_id):
    if request.method == 'GET':
        try:
            # Fetch all calls where the user is either the caller or the receiver
            # Sorted by newest calls first
            calls = Call.objects.filter(Q(caller_id=user_id) | Q(receiver_id=user_id)).order_by('-created_at')
            
            calls_list = []
            for call in calls:
                # Convert basic call details to dictionary
                call_data = call.to_dict()
                # Attach public user details (name, email, etc.)
                call_data['caller'] = call.caller.public_dict()
                call_data['receiver'] = call.receiver.public_dict()
                calls_list.append(call_data)
                
            # Return JSON array of calls
            return JsonResponse(calls_list, safe=False, status=200)
            
        except Exception as e:
            return JsonResponse({"message": "Error fetching calls", "error": str(e)}, status=500)
    return JsonResponse({"message": "Method not allowed"}, status=405)
