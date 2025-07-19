"""
Model Similarity Engine for Ollama Intelligence Trace
Calculates semantic similarity between models using multiple approaches
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from common.logging import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

@dataclass
class ModelSimilarity:
    model_a: str
    model_b: str
    similarity_score: float
    similarity_reasons: List[str]
    confidence: str

class ModelSimilarityEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        self.models_data = {}
        self.similarity_cache = {}
        
    def load_models(self, models_file: str):
        """Load enriched models data"""
        with open(models_file, 'r', encoding='utf-8') as f:
            self.models_data = {model['id']: model for model in json.load(f)}
    
    def normalize_architecture(self, arch: str) -> str:
        """Normalize architecture names for better matching"""
        arch_map = {
            'llama': 'llama',
            'mistral': 'mistral', 
            'phi': 'phi',
            'gemma': 'gemma',
            'qwen': 'qwen',
            'codellama': 'llama',
            'vicuna': 'llama',
            'wizardlm': 'llama',
            'orca': 'llama'
        }
        
        arch_lower = arch.lower()
        for key, normalized in arch_map.items():
            if key in arch_lower:
                return normalized
        return arch_lower
    
    def extract_parameter_count(self, model_name: str) -> Optional[float]:
        """Extract parameter count in billions"""
        patterns = [
            r'(\d+\.?\d*)b',  # 7b, 13b, 1.5b
            r'(\d+)billion',
            r'(\d+\.?\d*)B'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_name.lower())
            if match:
                return float(match.group(1))
        return None
    
    def calculate_name_similarity(self, name1: str, name2: str) -> Tuple[float, List[str]]:
        """Calculate similarity based on model names"""
        reasons = []
        score = 0.0
        
        # Exact base model match
        base1 = name1.split(':')[0].lower()
        base2 = name2.split(':')[0].lower()
        
        if base1 == base2:
            score += 0.8
            reasons.append(f"Same base model ({base1})")
        
        # Architecture family similarity
        arch1 = self.normalize_architecture(base1)
        arch2 = self.normalize_architecture(base2)
        
        if arch1 == arch2 and base1 != base2:
            score += 0.4
            reasons.append(f"Same architecture family ({arch1})")
        
        # Parameter count similarity
        params1 = self.extract_parameter_count(name1)
        params2 = self.extract_parameter_count(name2)
        
        if params1 and params2:
            param_diff = abs(params1 - params2)
            if param_diff == 0:
                score += 0.3
                reasons.append(f"Same parameter count ({params1}B)")
            elif param_diff <= 1:
                score += 0.2
                reasons.append(f"Similar parameter count ({params1}B vs {params2}B)")
        
        # Variant detection (instruct, chat, etc.)
        variants1 = set(re.findall(r'(instruct|chat|code|vision|uncensored)', name1.lower()))
        variants2 = set(re.findall(r'(instruct|chat|code|vision|uncensored)', name2.lower()))
        
        common_variants = variants1 & variants2
        if common_variants:
            score += 0.2
            reasons.append(f"Common variants: {', '.join(common_variants)}")
        
        return min(score, 1.0), reasons
    
    def calculate_metadata_similarity(self, model1: Dict, model2: Dict) -> Tuple[float, List[str]]:
        """Calculate similarity based on enriched metadata"""
        reasons = []
        score = 0.0
        
        # Architecture similarity
        if model1.get('architecture_family') == model2.get('architecture_family'):
            score += 0.3
            reasons.append(f"Same architecture: {model1.get('architecture_family')}")
        
        # Training approach similarity
        if model1.get('training_approach') == model2.get('training_approach'):
            score += 0.2
            reasons.append(f"Same training approach: {model1.get('training_approach')}")
        
        # Use case overlap
        use_cases1 = set(uc.get('use_case', '') for uc in model1.get('optimal_use_cases', []))
        use_cases2 = set(uc.get('use_case', '') for uc in model2.get('optimal_use_cases', []))
        
        overlap = use_cases1 & use_cases2
        if overlap:
            overlap_score = len(overlap) / max(len(use_cases1), len(use_cases2))
            score += overlap_score * 0.3
            reasons.append(f"Common use cases: {', '.join(list(overlap)[:2])}")
        
        # License similarity
        if model1.get('license_category') == model2.get('license_category'):
            score += 0.1
            reasons.append(f"Same license category: {model1.get('license_category')}")
        
        # Hardware requirements
        if model1.get('recommended_hardware') == model2.get('recommended_hardware'):
            score += 0.1
            reasons.append(f"Similar hardware needs: {model1.get('recommended_hardware')}")
        
        return min(score, 1.0), reasons
    
    def calculate_semantic_similarity(self, model1: Dict, model2: Dict) -> Tuple[float, List[str]]:
        """Calculate semantic similarity using text embeddings"""
        reasons = []
        
        # Combine text fields for semantic analysis
        def get_text_repr(model):
            parts = [
                model.get('summary', ''),
                ' '.join(model.get('primary_strengths', [])),
                ' '.join(model.get('known_limitations', [])),
                ' '.join(model.get('tags', []))
            ]
            return ' '.join(parts)
        
        text1 = get_text_repr(model1)
        text2 = get_text_repr(model2)
        
        if not text1 or not text2:
            return 0.0, reasons
        
        # Use TF-IDF for simple semantic similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            if similarity > 0.3:
                reasons.append(f"Similar descriptions (semantic: {similarity:.2f})")
            
            return similarity, reasons
        except:
            return 0.0, reasons
    
    def find_similar_models(self, target_model: str, top_k: int = 5) -> List[ModelSimilarity]:
        """Find most similar models to target"""
        if target_model not in self.models_data:
            return []
        
        target_data = self.models_data[target_model]
        similarities = []
        
        for model_id, model_data in self.models_data.items():
            if model_id == target_model:
                continue
            
            # Calculate different similarity components
            name_sim, name_reasons = self.calculate_name_similarity(target_model, model_id)
            meta_sim, meta_reasons = self.calculate_metadata_similarity(target_data, model_data)
            semantic_sim, semantic_reasons = self.calculate_semantic_similarity(target_data, model_data)
            
            # Weighted combination
            total_score = (
                name_sim * 0.5 +
                meta_sim * 0.3 +
                semantic_sim * 0.2
            )
            
            all_reasons = name_reasons + meta_reasons + semantic_reasons
            
            # Determine confidence
            if total_score > 0.7:
                confidence = "high"
            elif total_score > 0.4:
                confidence = "medium"
            else:
                confidence = "low"
            
            if total_score > 0.1:  # Only include meaningful similarities
                similarities.append(ModelSimilarity(
                    model_a=target_model,
                    model_b=model_id,
                    similarity_score=total_score,
                    similarity_reasons=all_reasons,
                    confidence=confidence
                ))
        
        # Sort by similarity score and return top k
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities[:top_k]
    
    def detect_duplicates(self, threshold: float = 0.8) -> List[Tuple[str, str, float]]:
        """Detect near-duplicate models"""
        duplicates = []
        processed = set()
        
        for model_id in self.models_data:
            if model_id in processed:
                continue
            
            similar = self.find_similar_models(model_id, top_k=3)
            for sim in similar:
                if sim.similarity_score >= threshold:
                    pair = tuple(sorted([sim.model_a, sim.model_b]))
                    if pair not in processed:
                        duplicates.append((sim.model_a, sim.model_b, sim.similarity_score))
                        processed.add(pair)
        
        return duplicates
    
    def generate_similarity_graph(self) -> Dict:
        """Generate graph data for visualization"""
        nodes = []
        edges = []
        
        for model_id, model_data in self.models_data.items():
            nodes.append({
                'id': model_id,
                'name': model_id,
                'architecture': model_data.get('architecture_family', 'unknown'),
                'size': model_data.get('parameter_count', 'unknown'),
                'license': model_data.get('license_category', 'unknown')
            })
        
        # Add edges for similar models
        for model_id in self.models_data:
            similar = self.find_similar_models(model_id, top_k=3)
            for sim in similar:
                if sim.similarity_score > 0.3:
                    edges.append({
                        'source': sim.model_a,
                        'target': sim.model_b,
                        'weight': sim.similarity_score,
                        'reasons': sim.similarity_reasons
                    })
        
        return {'nodes': nodes, 'edges': edges}

# Usage example
if __name__ == "__main__":
    engine = ModelSimilarityEngine()
    engine.load_models('models_enriched.json')
    
    # Find similar models
    similar = engine.find_similar_models('llama3:8b')
    for sim in similar:
        logger.info("%s: %.3f (%s)", sim.model_b, sim.similarity_score, sim.confidence)
        logger.info("  Reasons: %s", ', '.join(sim.similarity_reasons))
    
    # Detect duplicates
    duplicates = engine.detect_duplicates()
    logger.info("Found %s potential duplicates", len(duplicates))
    
    # Generate graph data
    graph = engine.generate_similarity_graph()
    with open('similarity_graph.json', 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)