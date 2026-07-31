# Datasheet AI extraction optimization

## Pipeline

1. Extract layout text with one-based PDF page markers.
2. For long text PDFs, retain:
   - the first configured pages;
   - the highest-scoring specification pages;
   - pages containing the target-model identifier;
   - the best page for each requested specification field.
3. Send the reduced context and the product-form template to the local Ollama
   model.
4. Reject the whole response unless the target model is supported by source
   evidence.
5. Accept a specification only when:
   - confidence meets the configured threshold;
   - the returned type and unit match the database definition;
   - the page number exists;
   - the exact excerpt, or a strict token/numeric match, is supported by that
     page.
6. In product-family tables, require the model to use only the target row or
   column and to include the target identifier in the evidence excerpt.

Image-only PDFs use the same structured extraction but render no more than the
configured vision-page limit at reduced DPI and JPEG quality.

## Default tuning

```text
AI_DATASHEET_MAX_TEXT_CHARS=180000
AI_DATASHEET_TEXT_PAGE_LIMIT=10
AI_DATASHEET_HEAD_PAGES=6
AI_DATASHEET_VISION_PAGE_LIMIT=12
AI_DATASHEET_RENDER_DPI=96
```

## Reviewed benchmark

The benchmark is stored under `datasets/datasheet-benchmark` and contains 24
products and 381 approved field-level answers.

Run:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_datasheet_context.py `
  --output ..\datasets\datasheet-benchmark\context_benchmark_report.json
```

Current text-PDF result:

- 22 text PDFs evaluated;
- 68 reviewed evidence pages;
- 100% evidence-page retention;
- 28.98% fewer input characters.

This measures context selection, not model precision or wall-clock inference
time. End-to-end timing requires the local Ollama service to be running.
