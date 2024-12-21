from rest_framework.views import APIView
from .serializers import TournamentSerializer
from rest_framework.response import Response
from rest_framework import status

class TournamentCreateView(APIView):
    def post(self, request):
        serializer = TournamentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Tournament created.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        
# class TournamentDetailView(APIView):
    
        
# class TournamentListView(APIView):
    

# class TournamentJoinView(APIView):
    

# class TournamentStartView(APIView):