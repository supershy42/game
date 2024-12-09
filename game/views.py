from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ReceptionSerializer
from rest_framework.generics import ListAPIView
from .models import Reception

class CreateReceptionView(APIView):
    def post(self, request):
        serializer = ReceptionSerializer(data=request.data)
        if serializer.is_valid():
            reception = serializer.save()
            response_serializer = ReceptionSerializer(reception)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
        
class ReceptionsView(ListAPIView):
    queryset = Reception.objects.order_by('id')
    serializer_class = ReceptionSerializer