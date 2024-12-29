from unittest.mock import patch, AsyncMock
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from reception.models import Reception
from reception.services import ReceptionService
from config.custom_validation_error import CustomValidationError
from config.error_type import ErrorType
from unittest import IsolatedAsyncioTestCase

# 서비스 함수 테스트
class TestServiceFunctions(IsolatedAsyncioTestCase):
    async def test_validate_join_valid(self):
        reception = await Reception.objects.acreate(name="Test Room", max_players=2)

        with patch("reception.services.get_participants_count", return_value=1), \
             patch("reception.services.is_invited", return_value=True):
            try:
                await ReceptionService.validate_join(reception.id, user_id=1, password=None)
            except CustomValidationError:
                self.fail("validate_join raised CustomValidationError unexpectedly")

    async def test_validate_join_invalid_password(self):
        reception = await Reception.objects.acreate(name="Test Room", max_players=2, password="secret")

        with patch("reception.services.get_participants_count", return_value=1), \
             patch("reception.services.is_invited", return_value=False):
            with self.assertRaises(CustomValidationError) as exc:
                await ReceptionService.validate_join(reception.id, user_id=1, password="wrongpassword")
            self.assertEqual(exc.exception.error_type, ErrorType.INVALID_PASSWORD)

    async def test_invite_valid(self):
        with patch("reception.services.get_current_reception", return_value=1), \
             patch("reception.services.set_invitation"), \
             patch("config.services.UserService.send_notification", return_value=AsyncMock()):
            try:
                await ReceptionService.invite(from_user_id=1, to_user_id=2, from_user_name="TestUser")
            except CustomValidationError:
                self.fail("invite raised CustomValidationError unexpectedly")

    async def test_invite_no_reception(self):
        with patch("reception.services.get_current_reception", return_value=None):
            with self.assertRaises(CustomValidationError) as exc:
                await ReceptionService.invite(from_user_id=1, to_user_id=2, from_user_name="TestUser")
            self.assertEqual(exc.exception.error_type, ErrorType.NO_RECEPTION)

# 전체 기능 통합 테스트
class TestReceptionViews(APITestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.reception = Reception.objects.create(name="Test Room", max_players=2, password="secret")
        self.user_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM0MTg1NDM5LCJpYXQiOjE3MzQxODUxMzksImp0aSI6IjkxODQ5ODdkODI5NjQ0MzVhZDZkNGFjYTZlODAxYTgxIiwidXNlcl9pZCI6MX0.kqOvvPqz4LiYbNGtCO4uqd2H_h3Xr6pN_DLe5lmm0T4"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.user_token}")

    def test_join_reception_success(self):
        with patch("reception.views.validate_join", return_value=None), \
             patch("config.redis_utils.redis_client", autospec=True) as mock_redis_client:

            mock_redis_client.sismember = AsyncMock(return_value=0)
            url = f"/api/reception/{self.reception.id}/join/"
            data = {"password": "secret"}

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("url", response.data)
            self.assertEqual(response.data["token"], "ws_token")

    def test_join_reception_invalid_password(self):
        with patch("reception.views.validate_join", side_effect=CustomValidationError(ErrorType.INVALID_PASSWORD)), \
             patch("config.redis_utils.redis_client", autospec=True) as mock_redis_client:

            mock_redis_client.sismember = AsyncMock(return_value=0)
            url = f"/api/reception/{self.reception.id}/join/"
            data = {"password": "wrongpassword"}

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            self.assertEqual(response.data["message"], ErrorType.INVALID_PASSWORD.message)

    def test_invite_success(self):
        with patch("reception.views.invite", return_value=None), \
             patch("reception.views.UserService.get_user_name", return_value="MockedUserName"), \
             patch("reception.serializers.ReceptionInvitationSerializer.validate_to_user_id", return_value=True):

            url = "/api/reception/invite/"
            data = {"to_user_id": 2}

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["message"], "ok")

    def test_invite_no_reception(self):
        with patch("reception.views.invite", side_effect=CustomValidationError(ErrorType.NO_RECEPTION)), \
             patch("reception.views.UserService.get_user_name", return_value="MockedUserName"), \
             patch("reception.serializers.ReceptionInvitationSerializer.validate_to_user_id", return_value=True):

            url = "/api/reception/invite/"
            data = {"to_user_id": 2}

            response = self.client.post(url, data, format="json")

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(response.data["message"], ErrorType.NO_RECEPTION.message)

    def test_invited_user_join_without_password(self):
        with patch("reception.views.validate_join", return_value=None), \
             patch("reception.services.is_invited", return_value=True), \
             patch("reception.views.UserService.get_user_name", return_value="MockedUserName"), \
             patch("reception.services.UserService.send_notification", return_value=None), \
             patch("reception.serializers.ReceptionInvitationSerializer.validate_to_user_id", return_value=True), \
             patch("config.redis_utils.redis_client", autospec=True) as mock_redis_client:

            mock_redis_client.get = AsyncMock(return_value=b"1")
            mock_redis_client.hgetall = AsyncMock(return_value={"1": b"1"})
            mock_redis_client.setex = AsyncMock(return_value=True)
            mock_redis_client.sadd = AsyncMock(return_value=1)
            mock_redis_client.expire = AsyncMock(return_value=True)
            mock_redis_client.sismember = AsyncMock(return_value=1)

            # 초대자가 초대
            invite_url = "/api/reception/invite/"
            invite_data = {"to_user_id": 2}
            response = self.client.post(invite_url, invite_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # 초대받은 사용자가 비밀번호 없이 입장
            self.client.credentials(HTTP_AUTHORIZATION="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzM0MTg1NTgyLCJpYXQiOjE3MzQxODUyODIsImp0aSI6ImVhNmM0OGJjYWI1NTQ4MWZiYjE1NThmNzMwODhlN2Q2IiwidXNlcl9pZCI6Mn0.-B50k5zAKfbQUi_Winrtdeqe8W5TJSnVK5-74F7zzKg")
            join_url = f"/api/reception/{self.reception.id}/join/"
            join_data = {}  # 비밀번호 없이

            response = self.client.post(join_url, join_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("url", response.data)
            self.assertEqual(response.data["token"], "ws_token")