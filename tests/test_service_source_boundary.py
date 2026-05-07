from pathlib import Path


SERVICE_DIR = Path("app/services")
SOURCE_REPOSITORY_MODULES = (
    "spotify_track_repository",
    "spotify_audio_feature_repository",
    "spotify_lyrics_repository",
    "spotify_emotion_repository",
    "kkbox_user_feature_repository",
    "user_music_profile_repository",
)


def test_service_layer_does_not_import_source_repositories_directly():
    service_files = sorted(SERVICE_DIR.glob("*.py"))
    assert service_files

    violations = []
    for service_file in service_files:
        source = service_file.read_text(encoding="utf-8")
        for module_name in SOURCE_REPOSITORY_MODULES:
            if module_name in source:
                violations.append(f"{service_file}:{module_name}")

    assert violations == []
