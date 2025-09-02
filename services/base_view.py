from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView

class PublicView(GenericAPIView):
    permission_classes = [AllowAny]
