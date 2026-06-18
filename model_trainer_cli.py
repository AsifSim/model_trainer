from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import logging
sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.DEBUG,  # 👈 THIS enables debug logs
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger("model_trainer_cli")
logger.debug("Logger initialized")

APP_ROOT = Path(__file__).parent.resolve()
try:
    os.chdir(APP_ROOT)
except Exception:
    pass

def _resolve_fsm_path(query: str) -> Path:
    q = "" if query is None else str(query).strip()
    if not q:
        raise ValueError("Empty query. Pass FSM path as query or JSON {'fsmPath':'...'}")

    raw_path = q
    if q.startswith("{") and q.endswith("}"):
        payload = json.loads(q)
        if not isinstance(payload, dict):
            raise ValueError("Query JSON must be an object")
        raw_path = (
                payload.get("fsmPath")
                or payload.get("fsm_path")
                or payload.get("path")
                or payload.get("inputPath")
                or payload.get("input_path")
                or ""
        )

    if not raw_path:
        raise ValueError("FSM path missing in query")

    candidate = Path(str(raw_path)).expanduser()
    if not candidate.is_absolute():
        from_app = (APP_ROOT / candidate).resolve()
        from_repo = (APP_ROOT.parent / candidate).resolve()
        if from_app.exists():
            candidate = from_app
        elif from_repo.exists():
            candidate = from_repo
        else:
            candidate = from_app

    if not candidate.exists():
        raise FileNotFoundError(f"FSM file not found: {candidate}")

    return candidate


def handle_query(query: str) -> dict:
    start_ns = time.perf_counter_ns()
    try:
        # from deam_generator import generate_deam
        # from utility import extract_relevant_fsm_section

        # from sample_generator import main
        # logger.debug("Sample generation process is starting now")
        # main()
        # logger.debug("Samples have been generated successfully")

        # from dataset_creation import build_dataset
        # logger.debug("Starting dataset creation")
        # build_dataset()
        # logger.debug("Dataset created")
        logger.debug("Starting the training process")
        from model_trainer_tbrd import train_model
        logger.debug("Starting the model training")
        train_model()
        logger.debug("Model training done")

        total_ms = max(1, int((time.perf_counter_ns() - start_ns) / 1_000_000))
        return {
            "pid": "",
            "response": "done",
            "response_payload": {
                "generated_files": "done",
            },
            "error": "",
            "timings_ms": {
                "request_read": 0,
                "python_startup": 0,
                "agent": total_ms,
                "response_write": 0,
                "python_shutdown": 0,
                "total": total_ms,
            },
        }
    except Exception as exc:
        total_ms = max(1, int((time.perf_counter_ns() - start_ns) / 1_000_000))
        return {
            "pid": "",
            "response": "",
            "response_payload": None,
            "error": f"{type(exc).__name__}: {exc}",
            "timings_ms": {
                "request_read": 0,
                "python_startup": 0,
                "agent": total_ms,
                "response_write": 0,
                "python_shutdown": 0,
                "total": total_ms,
            },
        }


def _handle_file_mode(request_path: Path, response_path: Path) -> int:
    request_payload = json.loads(request_path.read_text(encoding="utf-8"))
    pid = str(request_payload.get("pid", ""))
    query = str(request_payload.get("query", "")).strip()
    result = handle_query(query)
    logger.debug(f"handle_query result = {result}")
    result["pid"] = pid
    result = _make_json_safe(result)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"result = {result}")
    response_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"response_file={response_path}")
    return 0 if not str(result.get("error", "")).strip() else 1


def main() -> int:
    if len(sys.argv) >= 3:
        req = Path(sys.argv[1])
        resp = Path(sys.argv[2])
        if req.suffix.lower() == ".json":
            return _handle_file_mode(req, resp)

    query = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not query:
        print(
            "Usage:\n"
            "  python AgentDev/deam_generate_cli.py \"AgentDev/out/<fsm>.json\"\n"
            "  python AgentDev/deam_generate_cli.py <request.json> <response.json>\n"
        )
        return 1
    print(json.dumps(handle_query(query), ensure_ascii=True))
    return 0


from pathlib import Path

def _make_json_safe(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    return obj



if __name__ == "__main__":
    raise SystemExit(handle_query("abcd"))
