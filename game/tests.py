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

    def test_create_room_without_name(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0].code, 'required')

    def test_create_room_with_name_exceeding_max_length(self):
        data = {
            'name': 'A' * 21,  # 최대 길이 20을 초과
            'password': 'password123'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0].code, 'max_length')

    def test_create_room_with_password_exceeding_max_length(self):
        data = {
            'name': 'Valid Room Name',
            'password': 'A' * 21  # 최대 길이 20을 초과
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0].code, 'max_length')
        
    def test_create_room_with_name_below_min_length(self):
        data = {
            'name': '',  # 최소 길이 1을 만족하지 않음
            'password': 'password123'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0].code, 'blank')

    def test_create_room_with_password_below_min_length(self):
        data = {
            'name': 'Valid Room Name',
            'password': ''  # 최소 길이 1을 만족하지 않음
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0].code, 'blank')