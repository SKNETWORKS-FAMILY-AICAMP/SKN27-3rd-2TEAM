from app.repositories.negative_preference_repository import NegativePreferenceRepository


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, row=None):
        self.cursor_obj = FakeCursor(row=row)
        self.committed = False

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def commit(self):
        self.committed = True


def test_negative_preference_repository_upserts_and_reads_profile():
    conn = FakeConnection(
        row={
            "user_id": "user_001",
            "disliked_artists_json": ["Billie Eilish"],
            "disliked_tracks_json": ["track_999"],
        }
    )
    repo = NegativePreferenceRepository(conn)

    repo.upsert(
        user_id="user_001",
        disliked_artists=["Billie Eilish"],
        disliked_tracks=["track_999"],
    )
    profile = repo.find_by_user_id("user_001")

    assert conn.committed
    assert profile["disliked_artists_json"] == ["Billie Eilish"]
    assert profile["disliked_tracks_json"] == ["track_999"]
