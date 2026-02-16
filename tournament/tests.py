import jwt
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, AsyncMock
from .models import Tournament, TournamentParticipant
from .services import TournamentService


def generate_jwt(user_id):
    """Generate JWT token (signature not verified by game service)"""
    return jwt.encode({'user_id': user_id}, 'secret', algorithm='HS256')


class TournamentModelTest(TestCase):
    """Tests for Tournament model"""

    def test_create_tournament(self):
        """Test creating a tournament"""
        tournament = Tournament.objects.create(
            name='Test Tournament',
            creator=1,
            max_participants=4
        )
        self.assertEqual(tournament.name, 'Test Tournament')
        self.assertEqual(tournament.max_participants, 4)
        self.assertEqual(tournament.state, Tournament.State.WAITING)

    def test_tournament_state_choices(self):
        """Test tournament state choices"""
        self.assertEqual(Tournament.State.WAITING, 'waiting')
        self.assertEqual(Tournament.State.IN_PROGRESS, 'in_progress')
        self.assertEqual(Tournament.State.FINISHED, 'finished')

    def test_valid_participants(self):
        """Test valid participant counts"""
        self.assertTrue(Tournament.is_valid_participants(4))
        self.assertTrue(Tournament.is_valid_participants(8))
        self.assertTrue(Tournament.is_valid_participants(16))
        self.assertFalse(Tournament.is_valid_participants(3))
        self.assertFalse(Tournament.is_valid_participants(5))

    def test_total_rounds(self):
        """Test total rounds calculation"""
        tournament_4 = Tournament.objects.create(name='T4', creator=1, max_participants=4)
        tournament_8 = Tournament.objects.create(name='T8', creator=1, max_participants=8)
        tournament_16 = Tournament.objects.create(name='T16', creator=1, max_participants=16)

        self.assertEqual(tournament_4.total_rounds, 2)  # log2(4) = 2
        self.assertEqual(tournament_8.total_rounds, 3)  # log2(8) = 3
        self.assertEqual(tournament_16.total_rounds, 4)  # log2(16) = 4

    def test_current_participants(self):
        """Test current participants count"""
        tournament = Tournament.objects.create(name='Test', creator=1, max_participants=4)
        self.assertEqual(tournament.current_participants, 0)

        TournamentParticipant.objects.create(tournament=tournament, user_id=1)
        TournamentParticipant.objects.create(tournament=tournament, user_id=2)

        self.assertEqual(tournament.current_participants, 2)

    def test_is_full(self):
        """Test tournament is_full method"""
        tournament = Tournament.objects.create(name='Test', creator=1, max_participants=4)
        self.assertFalse(tournament.is_full())

        for i in range(4):
            TournamentParticipant.objects.create(tournament=tournament, user_id=i+1)

        self.assertTrue(tournament.is_full())


class TournamentParticipantModelTest(TestCase):
    """Tests for TournamentParticipant model"""

    def setUp(self):
        self.tournament = Tournament.objects.create(name='Test', creator=1, max_participants=4)

    def test_create_participant(self):
        """Test creating a participant"""
        participant = TournamentParticipant.objects.create(
            tournament=self.tournament,
            user_id=1
        )
        self.assertEqual(participant.user_id, 1)

    def test_unique_together(self):
        """Test unique constraint on tournament + user_id"""
        TournamentParticipant.objects.create(tournament=self.tournament, user_id=1)
        with self.assertRaises(Exception):
            TournamentParticipant.objects.create(tournament=self.tournament, user_id=1)


class TournamentServiceTest(TestCase):
    """Tests for TournamentService"""

    def setUp(self):
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            creator=1,
            max_participants=4
        )

    def test_get_websocket_url(self):
        """Test websocket URL generation"""
        url = TournamentService.get_websocket_url(1)
        self.assertEqual(url, 'ws/tournament/1/')

    def test_get_group_name(self):
        """Test group name generation"""
        group_name = TournamentService.get_group_name(1)
        self.assertEqual(group_name, 'tournament_group_1')

    def test_get_arena_id(self):
        """Test arena ID generation"""
        arena_id = TournamentService.get_arena_id(1, 2)
        self.assertEqual(arena_id, 'tournament1_match2')

    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    @patch('tournament.services.TournamentService.start')
    def test_join_tournament(self, _mock_start, mock_redis_user):
        """Test joining a tournament"""
        mock_redis_user.return_value = {'id': 1, 'nickname': 'User1'}

        TournamentService.join(self.tournament.id, 1, 'token')

        self.assertEqual(TournamentParticipant.objects.count(), 1)
        self.assertEqual(
            TournamentParticipant.objects.first().user_id, 1
        )

    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    @patch('tournament.services.TournamentService.start')
    def test_join_triggers_start_when_full(self, mock_start, mock_redis_user):
        """Test that start is called when tournament is full"""
        mock_redis_user.return_value = {'id': 1, 'nickname': 'User'}

        for i in range(4):
            TournamentService.join(self.tournament.id, i+1, 'token')

        mock_start.assert_called_once()

    def test_get_user_match(self):
        """Test getting user's current match"""
        # Create participants BEFORE setting up tournament
        for i in range(4):
            TournamentParticipant.objects.create(tournament=self.tournament, user_id=i+1)

        # set_tournament creates matches and assigns players
        TournamentService.set_tournament(self.tournament)

        # User 1 should have a match assigned
        user_match = TournamentService.get_user_match(self.tournament, 1)
        self.assertIsNotNone(user_match)


class TournamentCreateViewTest(APITestCase):
    """Tests for TournamentCreateView"""

    def setUp(self):
        self.client = APIClient()
        self.user_id = 1
        self.token = generate_jwt(self.user_id)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.url = reverse('create-tournament')

    def test_create_tournament_invalid_participants(self):
        """Test tournament creation with invalid participant count"""
        data = {'name': 'My Tournament', 'max_participants': 5}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tournament_missing_name(self):
        """Test tournament creation without name"""
        data = {'max_participants': 4}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tournament_no_auth(self):
        """Test tournament creation without auth"""
        self.client.credentials()
        data = {'name': 'My Tournament', 'max_participants': 4}
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TournamentListViewTest(APITestCase):
    """Tests for TournamentListView"""

    def setUp(self):
        self.client = APIClient()
        self.token = generate_jwt(1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.url = reverse('tournaments')

    def test_list_tournaments_requires_auth(self):
        """Test that listing requires authentication"""
        self.client.credentials()  # Clear auth
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TournamentJoinViewTest(APITestCase):
    """Tests for TournamentJoinView"""

    def setUp(self):
        self.client = APIClient()
        self.token = generate_jwt(1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.tournament = Tournament.objects.create(
            name='Test', creator=2, max_participants=4
        )

    def get_url(self, tournament_id):
        return reverse('join-tournament', kwargs={'tournament_id': tournament_id})

    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    @patch('tournament.services.TournamentService.start')
    def test_join_tournament_success(self, _mock_start, mock_redis_user):
        """Test successful tournament join"""
        mock_redis_user.return_value = {'id': 1, 'nickname': 'User'}

        url = self.get_url(self.tournament.id)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TournamentParticipant.objects.count(), 1)

    @patch('config.redis_services.UserRedisService.get_or_fetch_user_exclude_email', new_callable=AsyncMock)
    @patch('tournament.services.TournamentService.start')
    def test_join_tournament_already_joined(self, _mock_start, mock_redis_user):
        """Test joining tournament twice"""
        mock_redis_user.return_value = {'id': 1, 'nickname': 'User'}

        TournamentParticipant.objects.create(tournament=self.tournament, user_id=1)

        url = self.get_url(self.tournament.id)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TournamentDetailViewTest(APITestCase):
    """Tests for TournamentDetailView"""

    def setUp(self):
        self.client = APIClient()
        self.token = generate_jwt(1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.tournament = Tournament.objects.create(
            name='Test', creator=1, max_participants=4
        )

    def get_url(self, tournament_id):
        return reverse('tournament-detail', kwargs={'tournament_id': tournament_id})

    def test_get_tournament_detail_requires_auth(self):
        """Test that detail view requires authentication"""
        self.client.credentials()  # Clear auth
        url = self.get_url(self.tournament.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_tournament_detail_not_found(self):
        """Test getting non-existent tournament"""
        url = self.get_url(9999)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
