from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from threading import Thread
from django.core.mail import send_mail
import re
from twilio.rest import Client
from django.conf import settings

# Thread decorator definition
def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@api_view(['POST'])
def post_alert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        identify_email_sms(serializer)
    else:
        return JsonResponse({'error': 'Unable to process data'}, status=400)
    
    return Response(request.META.get('HTTP_AUTHORIZATION'))

def identify_email_sms(serializer):
    alert_receiver = serializer.data['alert_receiver']
    email_pattern = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    pakistani_number_pattern = r'^\+92[3-9][0-9]{9}$'
    
    if re.match(email_pattern, alert_receiver):  
        print("Valid Email")
        send_email(serializer)
    elif re.match(pakistani_number_pattern, alert_receiver):
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")

# Sends SMS
@start_new_thread
def send_sms(serializer):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=prepare_alert_message(serializer),
            from_=settings.TWILIO_NUMBER,
            to=serializer.data['alert_receiver']
        )
        print("SMS sent successfully.")
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")

# Sends email
@start_new_thread
def send_email(serializer):
    try:
        send_mail(
            'Anomally Detected!', 
            prepare_alert_message(serializer), 
            'sameerriaz910@gmail.com',
            [serializer.data['alert_receiver']],
            fail_silently=True,
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

# Prepares the alert message
def prepare_alert_message(serializer):
    try:
        # Assuming `image` is the field in the serializer that contains the image URL or path
        image_url = serializer.data['image']
        print(f"Received image URL: {image_url}")  # Debug print

        # Split the URL by '/' to extract components
        uuid_with_slashes = split(image_url, "/")
        
        # Ensure the split list has the expected structure
        if len(uuid_with_slashes) < 2:
            raise ValueError("Image URL format is incorrect or missing parts.")
        
        # Extract the UUID part (assuming the last part of the URL is the UUID with extension)
        uuid_with_extension = uuid_with_slashes[-1]
        uuid = uuid_with_extension.split(".")[0]  # Extract the UUID part before the extension
        print(f"Extracted UUID: {uuid}")  # Debug print
        
        # Construct the alert URL using the extracted UUID
        url = f'http://127.0.0.1:8000/alert/{uuid}'
        print(url)
        return f'Anomally Detected! View alert at {url}'
    except Exception as e:
        print(f"Error preparing alert message: {str(e)}")
        return 'Anomally Detected! Error generating alert URL.'

# Splits string into a list
def split(value, key):
    return str(value).split(key)
