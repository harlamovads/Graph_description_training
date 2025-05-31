import os
import traceback
from transformers import T5Tokenizer, T5ForConditionalGeneration, ElectraTokenizer, ElectraForTokenClassification

print('Setting up model cache directory...')

print('Downloading T5 model and tokenizer...')
try:
    tokenizer = T5Tokenizer.from_pretrained('Zlovoblachko/REAlEC_2step_model_testing')
    model = T5ForConditionalGeneration.from_pretrained('Zlovoblachko/REAlEC_2step_model_testing')
    print('T5 model downloaded successfully')
except Exception as e:
    print(f'Error downloading T5 model: {e}')
    traceback.print_exc()

print('Downloading ELECTRA GED model and tokenizer...')
try:
    ged_tokenizer = ElectraTokenizer.from_pretrained('Zlovoblachko/11tag-electra-grammar-stage2')
    ged_model = ElectraForTokenClassification.from_pretrained('Zlovoblachko/11tag-electra-grammar-stage2')
    print('ELECTRA GED model downloaded successfully')
except Exception as e:
    print(f'Error downloading ELECTRA model: {e}')
    traceback.print_exc()
    # Try alternative model if the main one fails
    try:
        print('Trying alternative GED model...')
        ged_tokenizer = ElectraTokenizer.from_pretrained('Zlovoblachko/4tag-electra-grammar-error-detection')
        ged_model = ElectraForTokenClassification.from_pretrained('Zlovoblachko/4tag-electra-grammar-error-detection')
        print('Alternative GED model downloaded successfully')
    except Exception as e2:
        print(f'Error downloading alternative model: {e2}')

print('Model download process completed')