# LLM Prompts for Enrichment

## Summarization Prompt Template
Summarize **{model_name}** for developers:

* **Overview**: Brief description of architecture and capabilities.
* **Strengths**: List top 3 strengths.
* **Use Cases**: At least 3 practical use cases.
* **Similar Models**: Mention 2–3 comparable models on Hugging Face or arXiv.

## Hallucination Check Prompt
Verify the above summary against the official {model_name} documentation and list any discrepancies.

## Trust Heuristics Prompt
Evaluate **{model_name}** for potential risks:

* License compatibility (commercial vs. non-commercial)
* Data provenance concerns
* "Jailbreak" vulnerability indicators
Provide a trust score between 0.0 and 1.0, with justification.
