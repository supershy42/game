from arena.dto import BaseMatchDTO
from .models import TournamentMatch

class TournamentMatchDTO(BaseMatchDTO):
    def __init__(self, match: TournamentMatch, token):
        super().__init__(match, token)
        self.round = match.round.round_number
        self.match_number = match.match_number
        self.state = match.state

    def to_dict(self):
        base_dict = super().to_dict()
        return {
            **base_dict,
            "round": self.round,
            "match_number": self.match_number,
            "state": self.state,
        }