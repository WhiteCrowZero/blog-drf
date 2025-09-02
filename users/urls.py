from django.urls import path
from .views import RegisterView, LoginView, OauthLoginView, UserInfoView, UserContactView, \
    UserInfoDetailView, UserContactDetailView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('oauth/login/', OauthLoginView.as_view(), name='oauth-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('info/', UserInfoView.as_view(), name='info'),
    path('info/detial/', UserInfoDetailView.as_view(), name='info-detail'),
    path('contact/', UserContactView.as_view(), name='contact'),
    path('contact/<str:type>/', UserContactDetailView.as_view(), name='contact-detail'),
]
