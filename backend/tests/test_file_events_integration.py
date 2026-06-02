import os
import sys
from io import BytesIO

# Add backend to path so we can import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bucket_harbour.infrastructure.database import init_db, SessionLocal
from bucket_harbour.application.file_application_service import FileApplicationService
from bucket_harbour.infrastructure.file_service import FileService
from bucket_harbour.domain.models import FileAggregate, FileState

def test_file_events_integration():
    # Initialize database
    init_db()

    db = SessionLocal()
    file_service = FileService()
    app_service = FileApplicationService(db, file_service)

    # Create a mock file stream
    mock_data = b"This is some mock log content to test stable hashing!"
    file_stream = BytesIO(mock_data)

    print("Staging mock file...")
    file_agg = app_service.stage_file("test_logs.jsonl", "text/plain", file_stream)

    print("File staged successfully!")
    print("ID:", file_agg.id)
    print("State:", file_agg.current_state)
    print("Metadata:", file_agg.metadata_json)

    # Check if sha256 is present
    sha256 = file_agg.metadata_json.get("sha256")
    print("Staged SHA-256:", sha256)
    assert sha256 is not None, "SHA-256 should be populated upon staging!"

    # Replay events to reconstruct state
    print("\nReplaying events from history...")
    reconstructed = app_service.reconstruct_from_history(file_agg.id)
    print("Reconstructed State:", reconstructed.current_state)
    print("Reconstructed Metadata:", reconstructed.metadata_json)
    assert reconstructed.metadata_json.get("sha256") == sha256, "Reconstructed SHA-256 must match!"

    # Discard mock file
    print("\nDiscarding file...")
    discarded = app_service.discard_file(file_agg.id)
    print("State after discard:", discarded.current_state)

    # Replay events after discard to ensure it reconstructs DISCARDED state
    print("\nReplaying events after discard...")
    reconstructed_discarded = app_service.reconstruct_from_history(file_agg.id)
    print("Reconstructed Post-Discard State:", reconstructed_discarded.current_state)
    assert reconstructed_discarded.current_state == FileState.DISCARDED, "Reconstructed state after discard must be DISCARDED!"

    db.close()
    print("\nAll integration checks passed successfully!")

if __name__ == "__main__":
    test_file_events_integration()
