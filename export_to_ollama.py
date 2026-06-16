from unsloth import FastLanguageModel

# Point this exactly to your completed training checkpoint folder
MODEL_PATH = "output/checkpoint-90" # Or "output/checkpoint-20" depending on your last run folder name
MAX_SEQ_LENGTH = 8192

print("🔄 Loading your local fine-tuned checkpoint...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_PATH,
    max_seq_length=MAX_SEQ_LENGTH,
    load_in_4bit=True,
)

print("\n⚡ Merging weights LOCALLY (Zero Downloads)...")
# This saves the model out as raw 16-bit layers directly onto your disk
model.save_pretrained_merged("my_ollama_model", tokenizer, save_method="merged_16bit")

print("\n🎉 Local Merge Complete! Ready for manual GGUF compilation.")