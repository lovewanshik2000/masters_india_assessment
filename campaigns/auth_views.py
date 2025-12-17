from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from campaigns.utils import api_response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name (optional)'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name (optional)'),
            }
        ),
        responses={
            201: 'User registered successfully',
            400: 'Bad Request - Validation error'
        }
    )
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not username:
            return api_response(success=False, message="username is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if not email:
            return api_response(success=False, message="email is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if not password:
            return api_response(success=False, message="password is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return api_response(success=False, message="Username already exists", status_code=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return api_response(success=False, message="Email already exists", status_code=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }
        
        return api_response(success=True, message="User registered successfully", data=response_data, status_code=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with username and password to get JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        ),
        responses={
            200: 'Login successful',
            401: 'Invalid credentials'
        }
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username:
            return api_response(success=False, message="username is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        if not password:
            return api_response(success=False, message="password is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return api_response(success=False, message="Invalid username or password", status_code=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return api_response(success=False, message="User account is disabled", status_code=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }
        
        return api_response(success=True, message="Login successful", data=response_data)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Refresh access token using refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token'),
            }
        ),
        responses={
            200: 'Token refreshed successfully',
            401: 'Invalid or expired refresh token'
        }
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return api_response(success=False, message="refresh token is required", status_code=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            response_data = {
                'access': str(refresh.access_token)
            }
            return api_response(success=True, message="Token refreshed successfully", data=response_data)
        except Exception as e:
            return api_response(success=False, message="Invalid or expired refresh token", status_code=status.HTTP_401_UNAUTHORIZED)
