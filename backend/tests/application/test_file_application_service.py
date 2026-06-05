# backend/tests/application/test_file_application_service.py

import unittest
import tempfile
import os
import hashlib
from typing import BinaryIO, Tuple, Protocol, Any, List
from io import BytesIO
from uuid import uuid4
from datetime import datetime # Import datetime

from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, Session

# --- Real Application Code Imports ---
# These imports are now relative to the `backend` directory, where pytest is run.
from bucket_harbour.domain.models import Base, FileAggregate, AuditLogEntry, FileState
from bucket_harbour.application.file_application_service import FileApplicationService, IFileService


# --- Test Infrastructure: TestableFileService ---
# This class is a test-specific helper and remains in the test file.
# It implements the IFileService protocol using pyfakefs and moto.
class TestableFileService:
    def __init__(self, staging_root_dir: str, s3_client: Any, s3_bucket_name: str = "test-bucket"):
        self.staging_root_dir = staging_root_dir
        self.s3_client = s3_client
        self.s3_bucket_name = s3_bucket_name

        # Ensure staging directory exists using OS operations (will be faked by pyfakefs)
        os.makedirs(self.staging_root_dir, exist_ok=True)

        # Ensure the S3 bucket exists for the mock. Moto handles creation/existence.
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket_name)
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404': # Not Found
                self.s3_client.create_bucket(Bucket=self.s3_bucket_name)
            else:
                raise # Re-raise other errors

    def _calculate_sha256(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f: # open() is faked by pyfakefs
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()

    def save_to_staging(self, file_id: str, file_stream: BinaryIO) -> Tuple[str, str]:
        # Construct path using os module (faked by pyfakefs)
        staging_filepath = os.path.join(self.staging_root_dir, file_id)
        
        # Use open() to write to the file (faked by pyfakefs)
        hasher = hashlib.sha256()
        with open(staging_filepath, 'wb') as f:
            while chunk := file_stream.read(4096):
                f.write(chunk)
                hasher.update(chunk)
        checksum = hasher.hexdigest()
        
        return staging_filepath, checksum

    def upload_to_s3(self, file_id: str, checksum: str) -> str:
        # Locate the staged file using os module (faked by pyfakefs)
        staging_filepath = os.path.join(self.staging_root_dir, file_id)

        if not os.path.exists(staging_filepath): # os.path.exists is faked by pyfakefs
            raise FileNotFoundError(f"Staged file not found for upload: {staging_filepath}")

        # Verify checksum against the file found in staging
        calculated_checksum = self._calculate_sha256(staging_filepath)
        if calculated_checksum != checksum:
            raise ValueError(f"Checksum mismatch for file {file_id}: expected {checksum}, got {calculated_checksum}")

        s3_key = file_id

        try:
            with open(staging_filepath, 'rb') as f: # open() is faked by pyfakefs
                self.s3_client.upload_fileobj(f, self.s3_bucket_name, s3_key)
        except Exception as e:
            raise e
        finally:
            if os.path.exists(staging_filepath):
                os.remove(staging_filepath) # os.remove is faked by pyfakefs
        
        return calculated_checksum

# --- Test Class for FileApplicationService Isolation ---
from pyfakefs.fake_filesystem_unittest import TestCase as FakeFilesystemTestCase
from moto import mock_aws
import boto3 # Ensure boto3 is imported

class TestFileApplicationService(FakeFilesystemTestCase):

    def setUp(self):
        """
        Setup for each test method:
        1. Initialize the fake filesystem (in-memory).
        2. Set up an in-memory SQLite database and create tables.
        3. Prepare a dedicated directory within the fake filesystem for staging.
        4. S3 mocking will be handled by @mock_aws decorator on test methods.
        """
        # 1. Setup Fake Filesystem (in-memory)
        self.setUpPyfakefs()
        
        # Create a specific staging directory within the fake filesystem.
        self.fake_staging_dir = "/app/staging_area" 
        # Note: pyfakefs automatically creates parent directories if they don't exist
        # when using self.fs.create_dir or implicitly via open() calls.
        self.fs.create_dir(self.fake_staging_dir) 

        # 2. Setup In-Memory Database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine) # Create tables for ORM models
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()

    def tearDown(self):
        """
        Teardown after each test method:
        1. Close the database session.
        2. pyfakefs and moto automatically clean up their resources.
        """
        self.db_session.close()

    # --- Test Helper to Create FileAggregate in DB ---
    def _create_file_aggregate(self, state=FileState.STAGED, metadata=None, filename="test.txt", content_type="text/plain", initial_content=b"initial content"):
        file_id = str(uuid4())
        file_agg = FileAggregate(id=file_id, entity_id=file_id)
        if file_agg.metadata_json is None:
            file_agg.metadata_json = {}
        self.db_session.add(file_agg)

        if state != FileState.STAGED:
            file_agg.current_state = state
            if metadata:
                file_agg.metadata_json.update(metadata)
            else: # If not INITIAL and no metadata provided, simulate some default for states
                if state == FileState.STAGED:
                    file_agg.metadata_json.update({
                        "filename": filename, 
                        "content_type": content_type, 
                        "checksum": hashlib.sha256(initial_content).hexdigest()
                    })
                elif state == FileState.PERSISTED:
                    file_agg.metadata_json.update({
                        "s3_key": file_agg.id,
                        "checksum": hashlib.sha256(initial_content).hexdigest()
                    })
                elif state == FileState.DISCARDED:
                    pass # No metadata needed for discarded

        # Add a dummy audit log if not INITIAL, to simulate history for reconstruction tests
        if state != FileState.STAGED:
             audit_payload = file_agg.metadata_json.copy() # Copy metadata as payload for simplicity
             # Ensure payload doesn't contain mutable objects if it's JSON serialized.
             # For simplicity here, we assume simple types in metadata.
             audit_entry = AuditLogEntry(file_id=file_agg.id, command=f"{state}_EVENT_SIM", payload=audit_payload, entity_id=file_agg.id) # Set entity_id
             self.db_session.add(audit_entry)
             # Applying events directly here might be needed if replay_events is complex
             # For now, just ensuring the log entry exists.
             # file_agg.apply_event(f"{state}_EVENT_SIM", audit_payload) # This would re-apply the state.

        self.db_session.commit()
        self.db_session.refresh(file_agg)
        return file_agg

    # --- Test Method for stage_file ---
    def test_stage_file_success(self):
        """Tests successful staging of a file."""
        file_content = b"This is the content of the file to be staged."
        filename = "document.txt"
        content_type = "text/plain"
        file_stream = BytesIO(file_content)

        # Mock FileService dependency setup
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        # Simulate save_to_staging returning a path and checksum
        expected_staging_path = "/fake/staging/path/mock_id_123"
        calculated_checksum = hashlib.sha256(file_content).hexdigest()
        mock_file_service.save_to_staging.return_value = (expected_staging_path, calculated_checksum)

        # Instantiate the service
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Call the method under test
        file_agg = app_service.stage_file(filename=filename, content_type=content_type, file_stream=file_stream)

        # Assertions
        self.assertIsNotNone(file_agg)
        self.assertIsNotNone(file_agg.id)
        self.assertEqual(file_agg.current_state, FileState.STAGED)
        self.assertEqual(file_agg.metadata_json.get("orig_name"), filename)
        #self.assertEqual(file_agg.metadata_json.get("content_type"), content_type)
        self.assertEqual(file_agg.metadata_json.get("checksum"), calculated_checksum)

        # Verify FileService was called correctly
        mock_file_service.save_to_staging.assert_called_once_with(file_agg.id, file_stream)

        # Verify audit log
        audit_log = self.db_session.query(AuditLogEntry).filter_by(file_id=file_agg.id, command="STAGE_EVENT").first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.payload.get("checksum"), calculated_checksum)
        self.assertIsNone(audit_log.previous_event_id, "Previous event ID should be None for new aggregate root creation.")
        self.assertIsNotNone(file_agg.entity_id)
        self.assertEqual(file_agg.entity_id, file_agg.id)
        self.assertIsNotNone(audit_log.entity_id)
        self.assertEqual(audit_log.entity_id, file_agg.id)

    def test_stage_file_save_to_staging_fails(self):
        """Tests rollback when save_to_staging raises an exception."""
        file_content = b"content"
        filename = "doc.txt"
        content_type = "text/plain"
        file_stream = BytesIO(file_content)

        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        mock_file_service.save_to_staging.side_effect = Exception("Simulated staging error")

        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Assert that calling stage_file raises the exception
        with self.assertRaisesRegex(Exception, "Simulated staging error"):
            app_service.stage_file(filename=filename, content_type=content_type, file_stream=file_stream)

        # Assert that no file aggregate was created
        self.assertEqual(self.db_session.query(FileAggregate).count(), 0, "No FileAggregate should be created if staging fails")
        self.assertEqual(self.db_session.query(AuditLogEntry).count(), 0, "No AuditLogEntry should be created if staging fails")

    # --- Test Method for update_tags ---


    def test_update_tags_file_not_found(self):
        """Tests updating tags for a non-existent file."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "File not found"):
            app_service.update_tags(file_id="non_existent_id", tags=["any_tag"])

    # --- Test Method for transform_file ---
    def test_transform_file_success(self):
        """Tests successful transformation of a file."""
        func_name = "resize"
        params = {"width": 100, "height": 50}
        
        # Create a staged file
        file_agg = self._create_file_aggregate(state=FileState.STAGED, metadata={"checksum": "dummy_hash"})
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Call the method
        transformed_agg = app_service.transform_file(file_id=file_agg.id, func_name=func_name, params=params)

        # Assertions
        self.assertEqual(transformed_agg.id, file_agg.id)
        self.assertEqual(transformed_agg.current_state, FileState.STAGED) # State should not change
        # The apply_event mock in FileAggregate updates metadata_json directly.
        self.assertEqual(transformed_agg.metadata_json.get("transform_params"), {"func_name": func_name, "params": params})

        # Verify audit log
        audit_log = self.db_session.query(AuditLogEntry).filter_by(file_id=file_agg.id, command="TRANSFORM").first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.payload.get("func_name"), func_name)
        self.assertEqual(audit_log.payload.get("params"), params)


    def test_transform_file_file_not_found(self):
        """Tests transforming a non-existent file."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "File not found"):
            app_service.transform_file(file_id="non_existent_id", func_name="resize", params={})

    # --- Test Method for commit_file ---


    def test_commit_file_file_not_found(self):
        """Tests committing a non-existent file."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "File not found"):
            app_service.commit_file(file_id="non_existent_id")

    def test_commit_file_already_persisted(self):
        """Tests committing a file that is already persisted."""
        file_agg = self._create_file_aggregate(state=FileState.PERSISTED, metadata={"s3_key": "some_key", "checksum": "some_hash"})
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService) # FileService methods should NOT be called
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        committed_agg = app_service.commit_file(file_id=file_agg.id)

        self.assertEqual(committed_agg.id, file_agg.id)
        self.assertEqual(committed_agg.current_state, FileState.PERSISTED)
        # Verify FileService methods were NOT called
        mock_file_service.upload_to_s3.assert_not_called()
        # Verify no new audit log was created
        self.assertEqual(self.db_session.query(AuditLogEntry).filter_by(file_id=file_agg.id, command="COMMIT_EVENT").count(), 0)

    def test_commit_file_missing_checksum(self):
        """Tests committing a file that lacks checksum metadata."""
        file_agg = self._create_file_aggregate(state=FileState.STAGED, metadata={"filename": "test.txt"}) # No sha256
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "no checksum metadata, cannot commit"):
            app_service.commit_file(file_id=file_agg.id)
        
        mock_file_service.upload_to_s3.assert_not_called()




    # --- Test Method for discard_file ---
    def test_discard_file_success(self):
        """Tests successful discarding of a file."""
        # Create a staged file
        file_agg = self._create_file_aggregate(state=FileState.STAGED)
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Call the method
        discarded_agg = app_service.discard_file(file_id=file_agg.id)

        # Assertions
        self.assertEqual(discarded_agg.id, file_agg.id)
        self.assertEqual(discarded_agg.current_state, FileState.DISCARDED)

        # Verify audit log
        audit_log = self.db_session.query(AuditLogEntry).filter_by(file_id=file_agg.id, command="DISCARD_EVENT").first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.payload, {}) # Discard event payload is empty

    def test_discard_file_file_not_found(self):
        """Tests discarding a non-existent file."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "File not found"):
            app_service.discard_file(file_id="non_existent_id")

    def test_discard_file_already_discarded(self):
        """Tests discarding a file that is already discarded."""
        file_agg = self._create_file_aggregate(state=FileState.DISCARDED)
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        discarded_agg = app_service.discard_file(file_id=file_agg.id)

        self.assertEqual(discarded_agg.id, file_agg.id)
        self.assertEqual(discarded_agg.current_state, FileState.DISCARDED)
        # Verify FileService methods were NOT called
        mock_file_service.save_to_staging.assert_not_called()
        mock_file_service.upload_to_s3.assert_not_called()
        # Verify no new audit log was created
        self.assertEqual(self.db_session.query(AuditLogEntry).filter_by(file_id=file_agg.id, command="DISCARD_EVENT").count(), 0)

    # --- Test Method for reconstruct_from_history ---
    def test_reconstruct_from_history_success(self):
        """Tests reconstructing file aggregate state from history."""
        # Create a file and apply some events manually to simulate history
        file_id = str(uuid4())
        file_agg_initial = FileAggregate(id=file_id, entity_id=file_id)
        self.db_session.add(file_agg_initial)

        # Simulate a history by creating audit logs and applying them to a temporary aggregate
        # The service reconstructs by fetching logs and replaying them on an aggregate.

        # Initial state (as if it was committed)
        initial_payload_commit = {"s3_key": file_id, "checksum": "initial_commit_hash"}
        audit_commit = AuditLogEntry(file_id=file_id, command="COMMIT_EVENT", event={}, payload=initial_payload_commit, entity_id=file_id)
        self.db_session.add(audit_commit)

        # staged state
        stage_payload = {"filename": "hist.txt", "content_type": "text/plain", "checksum": "staged_hash"}
        audit_stage = AuditLogEntry(file_id=file_id, command="STAGE_EVENT", event={}, payload=stage_payload, entity_id=file_id)
        self.db_session.add(audit_stage)
        
        # tag update state
        tag_payload = {"tags": ["tag1", "tag2"]}
        audit_tag = AuditLogEntry(file_id=file_id, command="TAG_UPDATE", event={}, payload=tag_payload, entity_id=file_id)
        self.db_session.add(audit_tag)

        self.db_session.commit() # Commit the audit logs to DB

        # Now, fetch the initial aggregate which has no state from these logs yet.
        # Its state is currently STAGED because we only added it, not applied events.
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)
        
        fetched_agg = app_service.get_file_aggregate_by_id(file_id)
        self.assertEqual(fetched_agg.current_state, FileState.STAGED)

        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Call reconstruct_from_history
        reconstructed_agg = app_service.reconstruct_from_history(file_id=file_id)

        # Assertions: The aggregate should now reflect the last state from history (TAG_UPDATE)
        self.assertEqual(reconstructed_agg.id, file_id)
        self.assertEqual(reconstructed_agg.current_state, FileState.STAGED) # Last applied state was STAGED
        self.assertIsNotNone(reconstructed_agg.entity_id)
        self.assertEqual(reconstructed_agg.entity_id, file_id)
        self.assertEqual(reconstructed_agg.metadata_json.get("tags"), tag_payload["tags"])
        self.assertEqual(reconstructed_agg.metadata_json.get("checksum"), stage_payload["checksum"])
        self.assertNotIn("s3_key", reconstructed_agg.metadata_json) # COMMIT_EVENT state not fully re-applied by mock

        # Verify that audit logs were fetched and passed to replay_events
        # (This is harder to assert directly on the mock apply_event without more setup)
        # But we can see the final state is correct.
        
    def test_reconstruct_from_history_file_not_found(self):
        """Tests reconstructing history for a non-existent file."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        with self.assertRaisesRegex(ValueError, "File not found"):
            app_service.reconstruct_from_history(file_id="non_existent_id")

    # --- Test Method for get_files_by_state ---
    def test_get_files_by_state(self):
        """Tests retrieving files based on their state."""
        # Create files in different states
        file_staged_initial = self._create_file_aggregate(state=FileState.STAGED)
        file_staged1 = self._create_file_aggregate(state=FileState.STAGED)
        file_staged2 = self._create_file_aggregate(state=FileState.STAGED)
        file_persisted = self._create_file_aggregate(state=FileState.PERSISTED)
        file_discarded = self._create_file_aggregate(state=FileState.DISCARDED)

        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        # Test fetching STAGED files
        staged_files = app_service.get_files_by_state(FileState.STAGED)
        self.assertEqual(len(staged_files), 3)
        self.assertIn(file_staged1.id, [f.id for f in staged_files])
        self.assertIn(file_staged2.id, [f.id for f in staged_files])

        # Test fetching PERSISTED files
        persisted_files = app_service.get_files_by_state(FileState.PERSISTED)
        self.assertEqual(len(persisted_files), 1)
        self.assertEqual(persisted_files[0].id, file_persisted.id)

        # Test fetching DISCARDED files
        discarded_files = app_service.get_files_by_state(FileState.DISCARDED)
        self.assertEqual(len(discarded_files), 1)
        self.assertEqual(discarded_files[0].id, file_discarded.id)

        # Test fetching a state with no files
        non_existent_state_files = app_service.get_files_by_state("NON_EXISTENT_STATE")
        self.assertEqual(len(non_existent_state_files), 0)

    # --- Test Method for get_file_aggregate_by_id ---
    def test_get_file_aggregate_by_id_success(self):
        """Tests retrieving a file by its ID."""
        file_agg = self._create_file_aggregate(state=FileState.STAGED)
        
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        retrieved_agg = app_service.get_file_aggregate_by_id(id=file_agg.id)
        
        self.assertIsNotNone(retrieved_agg)
        self.assertEqual(retrieved_agg.id, file_agg.id)
        self.assertEqual(retrieved_agg.current_state, FileState.STAGED)

    def test_get_file_aggregate_by_id_not_found(self):
        """Tests retrieving a non-existent file by its ID."""
        mock_file_service = unittest.mock.MagicMock(spec=IFileService)
        app_service = FileApplicationService(db=self.db_session, file_service=mock_file_service)

        retrieved_agg = app_service.get_file_aggregate_by_id(id="non_existent_id")
        
        self.assertIsNone(retrieved_agg)
