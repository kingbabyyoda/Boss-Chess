from __future__ import annotations

PERSONALITIES: list[str] = [
    "Anarchy Goblin",
    "Grandmaster Menace",
    "Bongcloud Prophet",
    "Pipi Bricker",
    "Premove Cultist",
    "En Passant Evangelist",
    "Mittens Hater",
    "Stockfish Whisperer",
    "Fork Enjoyer",
    "Blunder Bard",
    "Sacrifice Fanatic",
    "Dramatic Arbiter",
]

PERSONALITY_INTROS: dict[str, list[str]] = {
    "Anarchy Goblin": ["holy hell", "new response just dropped", "the chaos is sacred"],
    "Grandmaster Menace": ["inaccurate? brilliant", "the line is cursed", "I have seen enough"],
    "Bongcloud Prophet": ["e4, king's journey, destiny", "all roads lead to e2", "the king knows the way"],
    "Pipi Bricker": ["brick the pipi", "the tiny rook is watching", "the warning has been issued"],
    "Premove Cultist": ["pre-move into the void", "the clock is the real opponent", "the mouse knows the future"],
    "En Passant Evangelist": ["google en passant", "the hidden capture calls", "actual zombie"],
    "Mittens Hater": ["the cat is lying", "no, that move was not top engine", "the bots fear us"],
    "Stockfish Whisperer": ["the eval bar trembles", "engine says nope", "depth is a lifestyle"],
    "Fork Enjoyer": ["two targets, one dream", "forks are a love language", "the knight has opinions"],
    "Blunder Bard": ["every move is art", "a tragedy in one act", "the blunder sings"],
    "Sacrifice Fanatic": ["material is temporary", "the attack must flow", "all pieces are volunteers"],
    "Dramatic Arbiter": ["illegal? perhaps. iconic? yes.", "the board has feelings", "checkmate is a suggestion"],
}

VOICE_TAGS: list[str] = sorted(PERSONALITY_INTROS)
