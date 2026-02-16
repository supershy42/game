import jwt
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from unittest.mock import patch, AsyncMock
from .models import NormalMatch
from .services import ArenaService


def generate_jwt(user_id):
    """Generate JWT token using Django settings"""
    return jwt.encode({'user_id': user_id}, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


class NormalMatchModelTest(TestCase):
    """Tests for NormalMatch model"""

    def test_create_normal_match(self):
        """Test creating a normal match"""
        match = NormalMatch.objects.create(
            unique_id='test_match_123',
            reception_id=1,
            left_player=1,
            right_player=2,
            state=NormalMatch.State.PENDING
        )
        self.assertEqual(match.unique_id, 'test_match_123')
        self.assertEqual(match.left_player_score, 0)
        self.assertEqual(match.right_player_score, 0)
        self.assertEqual(match.state, NormalMatch.State.PENDING)

    def test_match_state_choices(self):
        """Test match state choices"""
        self.assertEqual(NormalMatch.State.PENDING, 'pending')
        self.assertEqual(NormalMatch.State.READY, 'ready')
        self.assertEqual(NormalMatch.State.FINISHED, 'finished')

    def test_match_team_choices(self):
        """Test team choices"""
        self.assertEqual(NormalMatch.Team.LEFT, 'left')
        self.assertEqual(NormalMatch.Team.RIGHT, 'right')

    def test_unique_id_is_unique(self):
        """Test that unique_id is enforced as unique"""
        NormalMatch.objects.create(unique_id='unique_123', reception_id=1)
        with self.assertRaises(Exception):
            NormalMatch.objects.create(unique_id='unique_123', reception_id=2)


class ArenaServiceTest(TestCase):
    """Tests for ArenaService"""

    def test_get_group_name(self):
        """Test group name generation"""
        group_name = ArenaService.get_group_name('arena_1')
        self.assertEqual(group_name, 'arena_group_arena_1')

    def test_arena_websocket_url(self):
        """Test websocket URL generation"""
        url = ArenaService.arena_websocket_url('arena_1')
        self.assertEqual(url, '/ws/arena/arena_1/')

    def test_generate_unique_id(self):
        """Test unique ID generation format"""
        unique_id = ArenaService.generate_unique_id()
        parts = unique_id.split('_')
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 8)  # uuid hex part
        self.assertEqual(len(parts[1]), 14)  # timestamp YYYYMMDDHHMMSS

    def test_generate_unique_id_is_unique(self):
        """Test that generated IDs are unique"""
        ids = [ArenaService.generate_unique_id() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100)

    def test_create_normal_match(self):
        """Test creating a normal match via service"""
        ArenaService.create_normal_match('test_unique_id', 1)
        match = NormalMatch.objects.get(unique_id='test_unique_id')
        self.assertEqual(match.reception_id, 1)
        self.assertEqual(match.state, NormalMatch.State.PENDING)

    def test_create_normal_match_duplicate(self):
        """Test that duplicate creation doesn't raise error"""
        ArenaService.create_normal_match('duplicate_id', 1)
        # Should not raise exception
        ArenaService.create_normal_match('duplicate_id', 2)
        # Only one match should exist
        self.assertEqual(NormalMatch.objects.filter(unique_id='duplicate_id').count(), 1)

    def test_save_normal_match(self):
        """Test saving match results"""
        match = NormalMatch.objects.create(unique_id='save_test', reception_id=1)
        result = {
            'arena_id': 'save_test',
            'left_player': 1,
            'right_player': 2,
            'left_player_score': 3,
            'right_player_score': 1,
            'winner': 1
        }
        ArenaService.save_normal_match(match, result)

        match.refresh_from_db()
        self.assertEqual(match.left_player, 1)
        self.assertEqual(match.right_player, 2)
        self.assertEqual(match.left_player_score, 3)
        self.assertEqual(match.right_player_score, 1)
        self.assertEqual(match.winner, 1)
        self.assertEqual(match.state, NormalMatch.State.FINISHED)

    def test_get_user_matches(self):
        """Test fetching user matches"""
        # Create matches for user 1
        NormalMatch.objects.create(
            unique_id='match_1', reception_id=1,
            left_player=1, right_player=2,
            state=NormalMatch.State.FINISHED
        )
        NormalMatch.objects.create(
            unique_id='match_2', reception_id=2,
            left_player=3, right_player=1,
            state=NormalMatch.State.FINISHED
        )
        # Pending match should not be returned
        NormalMatch.objects.create(
            unique_id='match_3', reception_id=3,
            left_player=1, right_player=4,
            state=NormalMatch.State.PENDING
        )

        matches = ArenaService.get_user_matches(1)
        self.assertEqual(len(matches), 2)

    def test_get_user_matches_no_matches(self):
        """Test fetching matches for user with no matches"""
        matches = ArenaService.get_user_matches(999)
        self.assertEqual(len(matches), 0)


class MatchHistoryViewTest(APITestCase):
    """Tests for MatchHistoryView"""

    def setUp(self):
        self.client = APIClient()
        self.user_id = 1
        self.token = generate_jwt(self.user_id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def get_url(self, user_id):
        return reverse('normal-matches', kwargs={'user_id': user_id})

    @patch('config.services.UserService.get_user', new_callable=AsyncMock)
    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    def test_get_match_history_success(self, mock_redis_user, mock_get_user):
        """Test successful match history retrieval"""
        mock_get_user.return_value = {'id': 1, 'nickname': 'TestUser'}
        mock_redis_user.return_value = {'id': 1, 'nickname': 'TestUser', 'avatar': '/media/default.png'}

        # Create a finished match
        NormalMatch.objects.create(
            unique_id='history_1', reception_id=1,
            left_player=1, right_player=2,
            left_player_score=3, right_player_score=1,
            winner=1, state=NormalMatch.State.FINISHED
        )

        url = self.get_url(1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('config.services.UserService.get_user', new_callable=AsyncMock)
    def test_get_match_history_user_not_found(self, mock_get_user):
        """Test match history for non-existent user"""
        mock_get_user.return_value = None

        url = self.get_url(999)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('config.services.UserService.get_user', new_callable=AsyncMock)
    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    def test_get_match_history_empty(self, mock_redis_user, mock_get_user):
        """Test match history with no matches"""
        mock_get_user.return_value = {'id': 1, 'nickname': 'TestUser'}
        mock_redis_user.return_value = {'id': 1, 'nickname': 'TestUser'}

        url = self.get_url(1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_match_history_no_auth(self):
        """Test match history without authentication"""
        self.client.credentials()  # Clear credentials
        url = self.get_url(1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
