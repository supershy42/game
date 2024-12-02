from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from .models import GameRoom

class CreateGameRoomTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create-room')

    def test_create_room_without_password(self):
        data = {
            'name': 'Public Room'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Public Room')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        room = GameRoom.objects.get(id=response.data['id'])
        self.assertIsNone(room.password)

    def test_create_room_with_password(self):
        data = {
            'name': 'Private Room',
            'password': 'securepassword123'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Private Room')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        room = GameRoom.objects.get(id=response.data['id'])
        self.assertTrue(room.check_password('securepassword123'))

    def test_create_room_with_empty_password(self):
        data = {
            'name': 'Empty Password Room',
            'password': ''
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Empty Password Room')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        room = GameRoom.objects.get(id=response.data['id'])
        self.assertTrue(room.check_password(''))

    def test_create_room_without_name(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0], 'This field is required.')
