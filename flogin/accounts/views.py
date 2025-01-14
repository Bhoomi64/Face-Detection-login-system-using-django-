from django.shortcuts import render
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from .models import User, UserImages
import face_recognition


@csrf_exempt
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        face_image_data = request.POST.get('face_image')

        # Basic validation
        if not username or not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Username or face image is missing'
            }, status=400)

        try:
            # Decode Base64
            if ',' in face_image_data:
                face_image_data = face_image_data.split(",")[1]
            face_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}_face.jpg')

            # Save user and image
            user, created = User.objects.get_or_create(username=username)
            UserImages.objects.create(user=user, face_image=face_image)

            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully'
            })

        except Exception as e:
            import traceback
            print(f"ERROR: {traceback.format_exc()}")
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=500)

    return render(request, 'register.html')


def login_user(request):
    if request.method == "POST":
        username = request.POST.get('username')
        face_image_data = request.POST.get('face_image')

        if not username or not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Username or face image is missing'
            }, status=400)

        try:
            # Fetch user
            user = User.objects.get(username=username)

            # Decode and process uploaded image
            if ',' in face_image_data:
                face_image_data = face_image_data.split(",")[1]

            uploaded_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}_face.jpg')
            uploaded_face_image = face_recognition.load_image_file(uploaded_image)

            # Debugging face recognition process
            print("DEBUG: Detecting faces in the uploaded image")
            uploaded_face_encoding = face_recognition.face_encodings(uploaded_face_image)

            if not uploaded_face_encoding:
                print("DEBUG: No faces detected")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the uploaded image'
                }, status=400)

            uploaded_face_encoding = uploaded_face_encoding[0]

            # Compare with stored encoding
            user_image = UserImages.objects.filter(user=user).last()
            print(f"DEBUG: Stored face image path: {user_image.face_image.path}")
            stored_face_image = face_recognition.load_image_file(user_image.face_image.path)
            stored_face_encoding = face_recognition.face_encodings(stored_face_image)

            if not stored_face_encoding:
                print("DEBUG: No face encoding found for the user")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face encoding found for the user'
                }, status=500)

            match = face_recognition.compare_faces([stored_face_encoding[0]], uploaded_face_encoding)
            if match[0]:
                return JsonResponse({
                    'status': 'success',
                    'message': 'User logged in successfully'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Face does not match'
                }, status=401)

        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'User does not exist'
            }, status=404)
        except Exception as e:
            print(f"Error during login: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred during login'
            }, status=500)


    return render(request, 'login.html')
