from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from .models import Reception

class CreateReceptionTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('create-reception')

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

    def test_create_reception_with_empty_password(self):
        data = {
            'name': 'Empty Password reception',
            'password': ''
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Empty Password reception')
        self.assertIn('id', response.data)
        self.assertNotIn('password', response.data)
        
        reception = Reception.objects.get(id=response.data['id'])
        self.assertTrue(reception.check_password(''))

    def test_create_reception_without_name(self):
        data = {}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0], 'This field is required.')
