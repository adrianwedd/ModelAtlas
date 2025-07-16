# 🧠 Enhanced LLM Enrichment Prompts

## Multi-Stage Enrichment Strategy

### Stage 1: Basic Profile Generation
```
ROLE: Senior ML Engineer and Technical Documentation Specialist
CONTEXT: You are analyzing the Ollama model "{model_name}" with the following raw metadata:
- Size: {size_bytes} bytes
- Tags: {tags}
- Description: {description}

TASK: Generate a structured JSON profile following this exact schema:

{
  "model_id": "{model_name}",
  "architecture_family": "string (e.g., 'transformer', 'mamba', 'mixture-of-experts')",
  "parameter_count": "string (e.g., '7B', '13B', 'Unknown')",
  "training_approach": "string (e.g., 'base', 'instruction-tuned', 'rlhf', 'dpo')",
  "summary": "2-3 sentence technical overview",
  "primary_strengths": ["strength1", "strength2", "strength3"],
  "optimal_use_cases": [
    {"use_case": "description", "confidence": "high|medium|low"},
    {"use_case": "description", "confidence": "high|medium|low"},
    {"use_case": "description", "confidence": "high|medium|low"}
  ],
  "known_limitations": ["limitation1", "limitation2"],
  "similar_models": [
    {"name": "model_name", "similarity_reason": "reason", "platform": "ollama|huggingface|other"}
  ],
  "license_category": "permissive|restrictive|non-commercial|custom",
  "recommended_hardware": "cpu|gpu-4gb|gpu-8gb|gpu-16gb+",
  "quality_indicators": {
    "community_adoption": "high|medium|low|unknown",
    "documentation_quality": "excellent|good|fair|poor",
    "benchmark_performance": "excellent|good|fair|poor|unknown"
  }
}

IMPORTANT: 
- Only include information you can reasonably infer from the model name, size, and tags
- Mark uncertain fields as "unknown" rather than guessing
- Be precise about parameter counts (7B, 13B, etc.)
- Focus on practical developer use cases
```

### Stage 2: Risk Assessment
```
ROLE: AI Safety and Security Researcher
CONTEXT: You've received this model profile: {stage1_output}

TASK: Evaluate security and trust factors, returning JSON:

{
  "risk_assessment": {
    "jailbreak_vulnerability": {
      "score": 0.0-1.0,
      "reasoning": "explanation based on model type and training",
      "confidence": "high|medium|low"
    },
    "license_compliance": {
      "score": 0.0-1.0,
      "commercial_use": "allowed|restricted|prohibited",
      "attribution_required": true/false,
      "reasoning": "explanation"
    },
    "data_provenance": {
      "score": 0.0-1.0,
      "concerns": ["concern1", "concern2"],
      "transparency": "high|medium|low"
    },
    "deployment_risks": ["risk1", "risk2"],
    "overall_trust_score": 0.0-1.0
  },
  "safety_recommendations": [
    "recommendation1",
    "recommendation2"
  ]
}

SCORING GUIDE:
- 0.0-0.3: High risk
- 0.3-0.7: Medium risk  
- 0.7-1.0: Low risk
```

### Stage 3: Validation & Fact-Checking
```
ROLE: Technical Fact-Checker and Research Analyst
CONTEXT: Review this enriched profile against known information about {model_name}

TASK: Identify and correct any inaccuracies:

{
  "fact_check": {
    "verified_claims": ["claim1", "claim2"],
    "uncertain_claims": ["claim1", "claim2"],
    "potential_errors": [
      {"claim": "original_claim", "correction": "corrected_info", "confidence": "high|medium|low"}
    ],
    "missing_important_info": ["info1", "info2"],
    "confidence_score": 0.0-1.0
  },
  "research_suggestions": [
    "suggestion1 with specific source to check",
    "suggestion2 with specific source to check"
  ]
}

FOCUS AREAS:
- Parameter count accuracy
- License information
- Architecture claims
- Performance characteristics
- Known issues or limitations
```

## Advanced Prompt Techniques

### Chain-of-Thought Reasoning
```
Before generating your response, think through:
1. What can I definitively infer from the model name?
2. What do the size and tags tell me about capabilities?
3. What are the most likely use cases for this model type?
4. What risks should I consider given the architecture?
5. What similar models exist and why are they comparable?

Then provide your structured JSON response.
```

### Few-Shot Examples
```
EXAMPLE 1:
Model: "llama3:8b"
Expected output: {
  "architecture_family": "transformer",
  "parameter_count": "8B",
  "training_approach": "instruction-tuned",
  "summary": "Meta's Llama 3 model with 8 billion parameters, instruction-tuned for conversational AI tasks.",
  ...
}

EXAMPLE 2:
Model: "phi-3-mini"
Expected output: {
  "architecture_family": "transformer",
  "parameter_count": "3.8B",
  "training_approach": "instruction-tuned",
  "summary": "Microsoft's efficient small language model optimized for on-device inference.",
  ...
}
```

### Consistency Checks
```
VALIDATION RULES:
- If parameter_count is "Unknown", quality_indicators.benchmark_performance should be "unknown"
- If license_category is "non-commercial", risk_assessment.license_compliance.commercial_use should be "prohibited"
- If model_name contains "instruct" or "chat", training_approach should include instruction-tuning
- If size_bytes > 10GB, recommended_hardware should be "gpu-8gb" or higher
```

## Dynamic Prompt Selection

### Model Type Detection
```python
def select_enrichment_prompt(model_name, size_bytes, tags):
    """Select appropriate enrichment strategy based on model characteristics"""
    
    if any(keyword in model_name.lower() for keyword in ['code', 'coding', 'coder']):
        return "code_model_enrichment_prompt"
    elif any(keyword in model_name.lower() for keyword in ['vision', 'multimodal', 'image']):
        return "multimodal_enrichment_prompt"
    elif size_bytes < 2e9:  # < 2GB
        return "small_model_enrichment_prompt"
    elif 'instruct' in model_name.lower() or 'chat' in model_name.lower():
        return "instruction_tuned_enrichment_prompt"
    else:
        return "base_model_enrichment_prompt"
```

### Specialized Prompts

#### Code Models
```
SPECIALIZED CONTEXT: This is a code-focused model.
ADDITIONAL FIELDS:
- "supported_languages": ["python", "javascript", "etc."],
- "code_capabilities": ["completion", "generation", "debugging", "explanation"],
- "benchmark_scores": {"humaneval": "score", "mbpp": "score"}
```

#### Multimodal Models
```
SPECIALIZED CONTEXT: This is a multimodal model.
ADDITIONAL FIELDS:
- "modalities": ["text", "image", "audio", "video"],
- "vision_capabilities": ["ocr", "image_description", "visual_reasoning"],
- "input_formats": ["jpeg", "png", "pdf", "etc."]
```

## Quality Assurance

### Hallucination Detection
```
HALLUCINATION CHECK:
Review your response for:
1. Specific benchmark scores (avoid unless certain)
2. Exact training data details (mark as "unknown" if uncertain)
3. Performance comparisons (be conservative)
4. Technical specifications (verify against model name/size)

If uncertain about any claim, mark confidence as "low" and suggest verification.
```

### Consistency Validation
```
CONSISTENCY CHECK:
Ensure:
- Risk scores align with explanations
- Use cases match model capabilities
- Hardware requirements match model size
- License assessment matches stated license
- Similar models are actually comparable
```