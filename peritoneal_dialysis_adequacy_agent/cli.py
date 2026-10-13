"""
Command-Line Interface for PD-Sentinel: Peritoneal Equilibration Test (PET) & Transport Status Classifier.
"""
import argparse
import csv
import json
import sys
from .clinical import pet_creatinine, weekly_ktv
from .models import ClinicalCasePayload
from .agents import PDCoordinator

coordinator = PDCoordinator()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="peritoneal-dialysis-adequacy-agent", description="PD-Sentinel: Peritoneal Equilibration Test (PET) & Transport Status Classifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single case clinical audit")
    p_audit.add_argument("--case-id", default="CASE-2026-001")
    p_audit.add_argument("--primary", type=float, default=26.2)
    p_audit.add_argument("--secondary", type=float, default=12.5)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

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
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTH-PT-881",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        dossier = coordinator.process_case(case)
        print("=" * 80)
        print(f"  PD-SENTINEL: PERITONEAL EQUILIBRATION TEST (PET) & TRANSPORT STATUS CLASSIFIER")
        print(f"  Domain: Nephrology | Standard: KDOQI Hemodialysis Adequacy & KDIGO CKD 2024")
        print(f"  Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] | Total Alerts: {dossier['total_alerts']}")
        print("=" * 80)
        for a in dossier["alerts"]:
            print(f"\n  [{a['urgency']}] from {a['sub_agent']}:")
            print(f"  Title: {a['title']}")
            print(f"  Finding: {a['clinical_finding']}")
            print(f"  Action: {a['actionable_recommendation']}")
        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_supervisory_chat(" ".join(args.query))
        print(f"\n[PDCoordinator]:\n{ans}\n")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + ["overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"]
        out_rows = []
        for r in rows:
            case = ClinicalCasePayload(
                case_id=r.get("case_id", "CASE-01"),
                patient_synthetic_id=r.get("patient_synthetic_id", "SYNTH-01"),
                primary_metric=float(r.get("metric_primary", r.get("primary_metric", 15.0))),
                secondary_metric=float(r.get("metric_secondary", r.get("secondary_metric", 5.0))),
                status_flag=r.get("status_flag", r.get("status_text", "NORMAL")),
                is_stat=bool(r.get("is_stat", r.get("critical_flag", False))),
            )
            dossier = coordinator.process_case(case)
            row_dict = dict(r)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["stat_critical_alerts"] = dossier["stat_critical_alerts"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        with open(args.output, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
            app = create_app()
            if app:
                print(f"Starting PD-Sentinel: Peritoneal Equilibration Test (PET) & Transport Status Classifier on http://{args.host}:{args.port}")
                uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
