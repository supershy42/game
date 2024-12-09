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
        
    def test_create_reception(self):
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
        
    def test_create_reception_without_password(self):
        data = {
            'name': 'Public Reception'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0].code, 'required')

    def test_create_room_with_name_exceeding_max_length(self):
        data = {
            'name': 'A' * 21,  # 최대 길이 20을 초과
            'password': 'password123'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0].code, 'max_length')
        
    def test_create_room_with_name_below_min_length(self):
        data = {
            'name': '',  # 최소 길이 1을 만족하지 않음
            'password': 'password123'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0].code, 'blank')

    def test_create_room_with_password_exceeding_max_length(self):
        data = {
            'name': 'Valid Room Name',
            'password': 'A' * 21  # 최대 길이 20을 초과
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0].code, 'max_length')
        
    def test_create_reception_without_token(self):
        # Remove the credentials
        self.client.credentials()
        data = {
            'name': 'No Token Reception'
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['error'], 'Authentication token missing.')


class TestReceptionsView(APITestCase):
    def setUp(self):
        # 테스트 데이터 생성
        for i in range(15):
            Reception.objects.create(name=f"Room {i + 1}", password="password")

        # Receptions API URL
        self.receptions_url = reverse("receptions")
        
        # Generate a JWT token with a user_id
        self.user_id = 1  # You can set this to any integer
        self.token = jwt.encode({'user_id': self.user_id}, 'secret', algorithm='HS256')
        
        # Set the token in the client's headers
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_receptions_list(self):
        """
        Reception 목록 API가 모든 Reception 데이터를 반환하는지 테스트.
        """
        # GET 요청
        response = self.client.get(self.receptions_url)

        # 상태 코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 데이터 검증
        self.assertEqual(len(response.data["results"]), 10)  # Reception 개수 확인
        self.assertEqual(response.data["results"][0]["name"], "Room 1")
        self.assertEqual(response.data["results"][1]["name"], "Room 2")

    def test_receptions_pagination(self):
        """
        페이지네이션이 지정된 크기(10)에 따라 동작하는지 테스트.
        """
        # 첫 번째 페이지 요청
        response = self.client.get(self.receptions_url, {"page": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 첫 페이지 결과 확인
        self.assertEqual(len(response.data["results"]), 10)  # 한 페이지에 5개
        self.assertEqual(response.data["results"][0]["name"], "Room 1")
        self.assertEqual(response.data["results"][-1]["name"], "Room 10")

        # 두 번째 페이지 요청
        response = self.client.get(self.receptions_url, {"page": 2})
        self.assertEqual(len(response.data["results"]), 5)  # 또 다른 5개
        self.assertEqual(response.data["results"][0]["name"], "Room 11")

        # 잘못된 페이지 요청 (총 페이지를 벗어남)
        response = self.client.get(self.receptions_url, {"page": 3})
        self.assertEqual(response.status_code, 404)  # Invalid page 처리 확인
        self.assertEqual(response.data["detail"], "Invalid page.")

    def test_receptions_empty_list(self):
        """
        Reception 데이터가 없을 때 빈 목록 반환 테스트.
        """
        # 모든 데이터를 삭제
        Reception.objects.all().delete()

        # GET 요청
        response = self.client.get(self.receptions_url)

        # 상태 코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 빈 결과 확인
        self.assertEqual(len(response.data["results"]), 0)