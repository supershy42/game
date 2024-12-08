# test_views.py

import jwt
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from game.models import Reception

class CreateReceptionTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create-reception')

        # Generate a JWT token with a user_id
        self.user_id = 1  # You can set this to any integer
        self.token = jwt.encode({'user_id': self.user_id}, 'secret', algorithm='HS256')
        
        # Set the token in the client's headers
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_create_reception_without_password(self):
        data = {
            'name': 'Public Reception'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Public Reception')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        reception = Reception.objects.get(id=response.data['id'])
        self.assertIsNone(reception.password)

    def test_create_reception_with_password(self):
        data = {
            'name': 'Private Reception',
            'password': 'securepassword123'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Private Reception')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        reception = Reception.objects.get(id=response.data['id'])
        self.assertTrue(reception.check_password('securepassword123'))

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
        
    def test_create_reception_without_token(self):
        # Remove the credentials
        self.client.credentials()
        data = {
            'name': 'No Token Reception'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['error'], 'Authentication token missing.')
