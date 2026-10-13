"""
Command Line Interface for Peritoneal Dialysis Adequacy Agent.
"""
import argparse
import csv
import json
import sys
from peritoneal_dialysis_adequacy_agent.clinical import pet_creatinine, weekly_ktv
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger, SecurityException

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="peritoneal-dialysis-adequacy-agent", description="Peritoneal Dialysis Adequacy Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=28.5)
    p_audit.add_argument("--secondary", type=float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    # Clinically interpretable, numeric educational calculations
    p_pet = subparsers.add_parser("pet", help="Compute 4-hour D/P creatinine (historical descriptive band)")
    p_pet.add_argument("--dialysate-creatinine", type=float, required=True)
    p_pet.add_argument("--plasma-creatinine", type=float, required=True)

    p_ktv = subparsers.add_parser("ktv", help="Compute weekly peritoneal and residual renal urea Kt/V")
    p_ktv.add_argument("--serum-urea", type=float, required=True)
    p_ktv.add_argument("--dialysate-urea", type=float, required=True)
    p_ktv.add_argument("--daily-drain-volume-l", type=float, required=True)
    p_ktv.add_argument("--v-l", type=float, required=True)
    p_ktv.add_argument("--urine-urea", type=float)
    p_ktv.add_argument("--daily-urine-volume-l", type=float)

    args = parser.parse_args(argv)

    if args.command in ("pet", "ktv"):
        try:
            if args.command == "pet":
                result = pet_creatinine(args.dialysate_creatinine, args.plasma_creatinine)
            else:
                result = weekly_ktv(
                    args.serum_urea, args.dialysate_urea,
                    args.daily_drain_volume_l, args.v_l,
                    args.urine_urea, args.daily_urine_volume_l,
                )
        except ValueError as exc:
            print(f"Invalid input: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  PERITONEAL DIALYSIS ADEQUACY AGENT")
        print(f"  Domain: Nephrology & Dialysis Systems | Standard: KDIGO / KDOQI Clinical Practice Guidelines")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Peritoneal Dialysis Adequacy Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0

    if args.command == "batch":
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
            return 1
        if not input_path.is_file():
            print(f"Error: '{args.input}' is not a file.", file=sys.stderr)
            return 1

        try:
            with open(input_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except csv.Error as e:
            print(f"Error: Failed to parse CSV file: {e}", file=sys.stderr)
            return 1
        except UnicodeDecodeError as e:
            print(f"Error: File encoding issue: {e}", file=sys.stderr)
            return 1

        # Validate CSV structure
        if not fieldnames:
            print("Error: CSV file has no headers or is empty.", file=sys.stderr)
            return 1

        out_fields = fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_rows = []
        errors = 0
        for idx, r in enumerate(rows):
            try:
                payload = SystemTaskPayload(
                    task_id=r.get("task_id", f"TASK-{idx+1:04d}"),
                    target_identifier=r.get("target_identifier", "TARGET-01"),
                    primary_metric=float(r.get("primary_metric", 15.0)),
                    secondary_metric=float(r.get("secondary_metric", 5.0)),
                    status_descriptor=r.get("status_descriptor", "NOMINAL"),
                    is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
                )
                dossier = supervisor.process_task(payload)
                row_dict = dict(r)
                row_dict["overall_urgency"] = dossier.overall_urgency.value
                row_dict["integrity_status"] = dossier.integrity_status.value
                row_dict["total_alerts"] = dossier.total_alerts
                row_dict["audit_hash"] = dossier.audit_hash
                out_rows.append(row_dict)
            except (ValueError, SecurityException) as e:
                print(f"Warning: Skipping row {idx+1}: {e}", file=sys.stderr)
                errors += 1
                continue

        try:
            with open(args.output, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(out_rows)
        except OSError as e:
            print(f"Error: Failed to write output file: {e}", file=sys.stderr)
            return 1

        print(f"Processed {len(out_rows)} records -> {args.output} ({errors} skipped)")
        return 0

    if args.command == "serve":
        import uvicorn
        from agents.api import app
        print(f"Starting Peritoneal Dialysis Adequacy Agent API server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
