"""
Automated Pytest for peritoneal-dialysis-adequacy-agent Enrichment Modules.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    FeaturesEngine,
    RealtimeEgfrTrendingDashboardEngine,
    DialysisAdequacyMonitoringEngine,
    FluidBalanceManagementEngine,
    MineralBoneDisorderMbdTracker,
    AnemiaManagementProtocolEngine,
    MulticenterCkdRegistryIntegrationEngine,
    NephrotoxicDrugAlertSystemEngine,
    PeritonealdialysisadequacyagentEnrichmentSuite,
    enrichment_suite,
)

def test_enrichment_suite_execution():
    suite = PeritonealdialysisadequacyagentEnrichmentSuite()
    res = suite.execute_all(primary_val=0.5, secondary_val=0.2)
    assert len(res) >= 1
    for k, v in res.items():
        assert v.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
        assert isinstance(v.recommendations, list)

def test_enrichment_threshold_escalation():
    suite = PeritonealdialysisadequacyagentEnrichmentSuite()
    res = suite.execute_all(primary_val=10.0, secondary_val=5.0)
    for k, v in res.items():
        assert v.status in ["WARNING", "CRITICAL_ALERT"]
        assert len(v.alerts) > 0
