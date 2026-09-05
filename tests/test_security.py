"""
Security-focused tests for Peritoneal Dialysis Adequacy Agent.
Tests PHI guard, audit trail integrity, and input validation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import os
from agents.base import (
    PHIGuard,
    AuditLogger,
    AuditTrail,
    SecurityException,
    assert_no_phi,
)
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor


class TestPHIGuard:
    """Test PHI detection and redaction."""

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_dob_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_john_doe_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient John Doe admitted")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task TASK-2026-001 processed successfully")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")
        PHIGuard.assert_no_phi(None)

    def test_phi_redaction(self):
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 has SSN 123-45-6789")
        assert "REDACTED_IDENTIFIER" in redacted
        assert "MRN-12345678" not in redacted
        assert "123-45-6789" not in redacted


class TestAuditTrail:
    """Test HMAC-SHA256 audit trail integrity."""

    def test_audit_trail_chaining(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_2", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor1", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT_2", {"data": "value2"})
        # Tamper with the first entry
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_trail_empty(self):
        trail = AuditTrail(secret_key="test-key-123")
        assert trail.verify_integrity() is True
        assert len(trail.get_trail()) == 0

    def test_audit_trail_with_phi_rejection(self):
        trail = AuditTrail(secret_key="test-key-123")
        with pytest.raises(SecurityException):
            trail.log("actor1", "tier1", "EVENT_1", {"patient": "MRN-12345678"})


class TestInputValidation:
    """Test input validation and error handling."""

    def test_invalid_csv_file_not_found(self):
        supervisor = SystemSupervisor(model_provider="mock")
        # This tests the CLI batch command error handling
        from cli import main
        result = main(["batch", "-i", "/nonexistent/path/file.csv"])
        assert result == 1  # Should return error code

    def test_payload_with_extreme_values(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TASK-EXTREME",
            target_identifier="KEY-01",
            primary_metric=float('1e10'),
            secondary_metric=float('-1e10'),
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ELEVATED

    def test_payload_with_zero_values(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TASK-ZERO",
            target_identifier="KEY-01",
            primary_metric=0.0,
            secondary_metric=0.0,
            status_descriptor="NOMINAL",
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE


class TestBatchProcessing:
    """Test batch CSV processing with error handling."""

    def test_batch_with_malformed_csv(self):
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid csv content\n,,,\n")
            temp_path = f.name
        try:
            result = main(["batch", "-i", temp_path])
            # Should handle gracefully (may succeed with warnings or fail gracefully)
            assert result == 0 or result == 1
        finally:
            os.unlink(temp_path)

    def test_batch_with_valid_csv(self):
        from cli import main
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("task_id,target_identifier,primary_metric,secondary_metric,status_descriptor\n")
            f.write("TASK-001,KEY-01,15.0,5.0,NOMINAL\n")
            f.write("TASK-002,KEY-02,35.0,15.0,DISCORDANT\n")
            temp_path = f.name

        output_path = temp_path.replace('.csv', '_output.csv')
        try:
            result = main(["batch", "-i", temp_path, "-o", output_path])
            assert result == 0
            assert os.path.exists(output_path)
        finally:
            os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
