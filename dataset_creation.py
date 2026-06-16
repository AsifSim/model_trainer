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
You are an expert data architect. Your sole task is to convert plain English business or functional requirements into a structured, clean JSON configuration payload following the target platform schema. 

Rules:
- Output ONLY valid, parsable JSON.
- Do not include markdown code block ticks (like ```json).
- Do not include conversational explanations, preambles, or notes.
- Ensure all keys, parameters, and entities from the text are accurately structured.
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