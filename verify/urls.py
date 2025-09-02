from django.urls import path
from verify import views

urlpatterns = [
    path('email/activate/', views.EmailActivateView.as_view(), name='email-activate'),
    path('email/verify/', views.EmailVerifyView.as_view(), name='email-verify'),
    path('email/send/', views.EmailSendVerifyView.as_view(), name='email-send'),
    path('captcha/', views.ImageCaptchaView.as_view(), name='image-captcha'),
]
