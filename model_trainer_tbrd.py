import logging
import traceback
import torch

# =====================================================================
# CRITICAL IMPORT ORDER FIX: Unsloth must be imported BEFORE TRL
# =====================================================================
from unsloth import FastLanguageModel
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer, SFTConfig

# =====================================================================
# MONKEY-PATCH: Bypass TRL's internal Entropy Logging crash
# =====================================================================
import trl.trainer.utils

def patched_entropy_from_logits(logits):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.tensor(0.0, device=device)

trl.trainer.utils.entropy_from_logits = patched_entropy_from_logits
# =====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

MODEL_NAME = "unsloth/Llama-3.2-3B-Instruct-bnb-4bit"
# MODEL_NAME = "unsloth/Llama-3.2-1B-Instruct-bnb-4bit"
# "unsloth/Llama-3.2-1B-Instruct-bnb-4bit"
MAX_SEQ_LENGTH = 8192


def load_model():
    logger.info("Loading base model %s", MODEL_NAME)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True
    )

    # Force vocabulary alignment
    tokenizer.eos_token = "<|end_of_text|>"
    tokenizer.pad_token = "<|end_of_text|>"
    
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.pad_token_id = tokenizer.eos_token_id
    
    if hasattr(model, "generation_config") and model.generation_config is not None:
        model.generation_config.eos_token_id = tokenizer.eos_token_id
        model.generation_config.pad_token_id = tokenizer.eos_token_id

    logger.info("Applying LoRA adapters")
    model = FastLanguageModel.get_peft_model(
        model,
        r=32,
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]
    )

    # Initialize Unsloth backend training optimization
    FastLanguageModel.for_training(model)

    logger.info("Model loaded successfully")
    return model, tokenizer


def load_training_dataset(tokenizer):
    logger.info("Loading dataset_json.jsonl")
    dataset = load_dataset(
        "json",
        data_files="dataset_json.jsonl",
        split="train"
    )

    logger.info("Dataset loaded. Records = %s", len(dataset))

    dataset = dataset.map(
        lambda example: {
            "text": tokenizer.apply_chat_template(
                example["messages"],
                tokenize=False
            )
        }
    )

    logger.info("Dataset formatting completed")
    return dataset


def build_trainer(model, tokenizer, dataset):
    logger.info("Building trainer")

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        processing_class=tokenizer,
        args=SFTConfig(
            output_dir="output",
            dataset_text_field="text",
            packing=False,  
            num_train_epochs=5,
            learning_rate=1e-4,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=16,
            logging_steps=10,
            save_steps=100,
            max_length=MAX_SEQ_LENGTH,
            bf16=True
        )
    )

    logger.info("Trainer initialized successfully")
    return trainer


def save_model(model, tokenizer):
    logger.info("Saving LoRA adapter to tbrd_converter_lora")
    model.save_pretrained("tbrd_converter_lora")
    tokenizer.save_pretrained("tbrd_converter_lora")
    logger.info("Model and tokenizer saved successfully")


def train_model():
    logger.info("Training started")

    model, tokenizer = load_model()
    dataset = load_training_dataset(tokenizer)
    trainer = build_trainer(model, tokenizer, dataset)

    logger.info("Starting trainer.train()")
    try:
        trainer.train()
    except Exception:
        logger.error(traceback.format_exc())
        raise

    logger.info("Training completed")
    save_model(model, tokenizer)
    logger.info("Training workflow completed successfully")


if __name__ == "__main__":
    train_model()