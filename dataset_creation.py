# import json
# import logging
# from pathlib import Path

# from docx import Document

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)s %(message)s"
# )

# logger = logging.getLogger(__name__)

# ROOT = Path("TBRD_CONVERSION")
# OUTPUT = "dataset.jsonl"

# SYSTEM_PROMPT = """
# You are an expert Java developer. Your task is to convert the provided TBRD requirement document into a clean, syntactically correct, and executable Java method.

# Rules:
# - Generate ONLY valid Java code inside the markdown code block.
# - Do not include conversational explanations, preambles, or notes.
# - Ensure all fields, parameters, and entities from the requirement text are preserved in the method signature or logic.
# - Do not hallucinate fields or logic not present in the requirement text.
# - Use clean formatting, logical naming, and standard Java code conventions.
# """


# def extract_docx_content(
#         path: Path
# ) -> str:

#     document = Document(path)

#     content = []

#     extract_paragraphs(
#         document,
#         content
#     )

#     extract_tables(
#         document,
#         content
#     )

#     return "\n".join(content)


# def extract_paragraphs(
#         document,
#         content: list[str]
# ) -> None:

#     for paragraph in document.paragraphs:

#         text = paragraph.text.strip()

#         if text:

#             content.append(text)


# def extract_tables(
#         document,
#         content: list[str]
# ) -> None:

#     for table in document.tables:

#         content.append("[TABLE]")

#         for row in table.rows:

#             values = [
#                 cell.text.strip()
#                 for cell in row.cells
#             ]

#             content.append(
#                 " | ".join(values)
#             )

#         content.append("[/TABLE]")


# def read_target_text(
#         path: Path
# ) -> str:

#     return path.read_text(
#         encoding="utf-8",
#         errors="ignore"
#     ).strip()


# def create_record(
#         source_text: str,
#         target_text: str
# ) -> dict:

#     return {
#         "messages": [
#             {
#                 "role": "system",
#                 "content": SYSTEM_PROMPT
#             },
#             {
#                 "role": "user",
#                 "content":
#                     "Input TBRD Document:\n\n"
#                     + source_text
#             },
#             {
#                 "role": "assistant",
#                 "content": target_text
#             }
#         ]
#     }


# def process_document_pair(
#         docx_file: Path
# ) -> dict | None:

#     txt_file = (
#             ROOT /
#             f"{docx_file.stem}.txt"
#     )

#     if not txt_file.exists():

#         logger.warning(
#             "Missing target file %s",
#             txt_file.name
#         )

#         return None

#     logger.info(
#         "Processing %s",
#         docx_file.stem
#     )

#     source_text = extract_docx_content(
#         docx_file
#     )

#     target_text = read_target_text(
#         txt_file
#     )

#     return create_record(
#         source_text,
#         target_text
#     )


# def build_dataset():

#     with open(
#             OUTPUT,
#             "w",
#             encoding="utf-8"
#     ) as writer:

#         for docx_file in ROOT.glob("*.docx"):

#             record = process_document_pair(
#                 docx_file
#             )

#             if record is None:
#                 continue

#             writer.write(
#                 json.dumps(
#                     record,
#                     ensure_ascii=False
#                 )
#                 + "\n"
#             )

#     logger.info(
#         "Dataset written to %s",
#         OUTPUT
#     )


# if __name__ == "__main__":
#     build_dataset()
import json
import logging
from pathlib import Path
from docx import Document

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

# --- Configuration ---
ROOT = Path("JSON_CREATION")        # Folder containing your .docx and .json pairs
OUTPUT = "dataset_json.jsonl"      # Final output dataset file

SYSTEM_PROMPT = """
You are a deterministic JSON compiler. Convert English business rules into a single, valid JSON object matching the target schema. 

OUTPUT RULES:
- Output ONLY valid JSON. 
- No markdown code blocks (do NOT use ```json).
- No explanations, notes, or commentary.
- Start with '{' and end with '}'.

TARGET SCHEMA TEMPLATE:
{
  "microservice_name": "String (exact name from doc)",
  "service_version": "v1",
  "is_platform_triggered": true,
  "method_signature": "public TransactionData execute(PlatformContext context, TransactionData data)",
  "associated_workflow": "String (e.g., cu_wf_...) ",
  "request_data_extractions": [
    {
      "field_name": "String",
      "data_type": "String",
      "extraction_path": "String (Java extraction statement)",
      "purpose": "String"
    }
  ],
  "eligibility_criteria": {
    "rule_name": "String",
    "expression": "String (logical gate)",
    "on_failure": "HALT_PROCESS"
  },
  "workflow_steps": [
    {
      "step_number": 1,
      "type": "DATABASE_STREAM|DATABASE_LOOKUP|APPLICATION_STREAM_JOIN|APPLICATION_LOGIC_VALIDATION",
      "target_entity": "String (snake_case table)",
      "filter_name": "String",
      "where_clause_parameters": ["String"],
      "columns_to_fetch": ["String"],
      "code_snippet": "String (Java pseudo-code)",
      "purpose": "String"
    }
  ],
  "conditional_routing": [
    {
      "condition": "String (English business rule)",
      "trigger_microservice": "SELF_INTERNAL_PERSISTENCE|ExternalServiceName",
      "target_version": "v1",
      "persistence_actions": [
        {
          "entity": "String",
          "operation": "update|insert|delete",
          "source_of_uuid": "String",
          "fields": { "field_name": "Source.value" }
        }
      ]
    }
  ],
  "test_specification_matrix": {
    "mock_dependencies": [
      {
        "step_reference": 1,
        "mock_target": "DATABASE_STREAM:table_name",
        "mock_outputs": { "profile_name": [{}] }
      }
    ],
    "scenarios": [
      {
        "scenario_id": "TC_001_UPPERCASE_NAME",
        "description": "String",
        "given_request_data": {},
        "simulated_profiles": ["profile_name"],
        "assertions": {
          "persistence_verifications": [{"target_entity": "String", "expected_operation": "String", "expected_fields": {}}],
          "external_system_calls": []
        }
      }
    ]
  }
}

INSTRUCTIONS:
1. Extract inputs into request_data_extractions.
2. Map entry-gating logic (e.g., checking region) to eligibility_criteria. 
3. Map table queries to sequential workflow_steps using snake_case table names.
4. Translate business outcomes into conditional_routing persistence actions.
5. Generate a matching test matrix tracking happy path and error branch scenarios.
"""

def extract_docx_content(path: Path) -> str:
    """Extracts all text paragraphs and tables from a .docx file."""
    document = Document(path)
    content = []

    # 1. Pull paragraphs
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            content.append(text)

    # 2. Pull tables (if any exist in your requirements)
    for table in document.tables:
        content.append("[TABLE]")
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells]
            content.append(" | ".join(values))
        content.append("[/TABLE]")

    return "\n".join(content)

def read_target_json(path: Path) -> str:
    """Reads the expected target JSON payload file."""
    return path.read_text(encoding="utf-8", errors="ignore").strip()

def create_record(source_text: str, target_json: str) -> dict:
    """Structures data into standard ChatML format for Unsloth training."""
    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": "Convert this requirement into a clean JSON structure:\n\n" + source_text
            },
            {
                "role": "assistant",
                "content": target_json
            }
        ]
    }

def process_document_pair(docx_file: Path) -> dict | None:
    """Pairs a .docx file with its matching .json file based on the file name."""
    json_file = ROOT / f"{docx_file.stem}.json"

    if not json_file.exists():
        logger.warning(
            "Missing matching target file: %s (Expected based on %s)",
            json_file.name, docx_file.name
        )
        return None

    logger.info("Processing pair: %s", docx_file.stem)
    
    source_text = extract_docx_content(docx_file)
    target_json = read_target_json(json_file)

    return create_record(source_text, target_json)

def build_dataset():
    if not ROOT.exists():
        logger.error("Directory '%s' not found. Please create it and add your file pairs.", ROOT)
        return

    counter = 0
    with open(OUTPUT, "w", encoding="utf-8") as writer:
        # Loop over all Word files instead of text files
        for docx_file in ROOT.glob("*.docx"):
            record = process_document_pair(docx_file)

            if record is None:
                continue

            writer.write(json.dumps(record, ensure_ascii=False) + "\n")
            counter += 1

    logger.info("🎉 Dataset successfully written to %s with %d records!", OUTPUT, counter)

if __name__ == "__main__":
    build_dataset()