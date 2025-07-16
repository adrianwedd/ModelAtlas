# Risk Heuristics for Model Catalog

## Categories
1. **License Risk**: Non-commercial vs. permissive vs. restrictive
2. **Jailbreak Risk**: Likelihood of adversarial prompt takeover
3. **Privacy Risk**: Training data provenance and PII exposure

## Scoring Guidelines
- **0.0–0.3**: High risk
- **0.3–0.7**: Medium risk
- **0.7–1.0**: Low risk

## Example Factors
- License (Apache‑2.0 → 0.9, CC BY‑NC → 0.4)
- Known exploits (none → +0.1, documented → −0.2)
- Community reviews (favorable → +0.1, mixed → 0)