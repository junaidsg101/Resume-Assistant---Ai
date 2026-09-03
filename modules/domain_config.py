"""
domain_config.py - Defines domain configs for scoring and keyword matching.
"""
from typing import Dict, List

DOMAINS: Dict[str, Dict[str, List[str]]] = {
    "Computer Science & Software Engineering": {
        "skills": ["algorithms", "data structures", "system design", "distributed systems", "OOP"],
        "tools": ["git", "docker", "kubernetes", "linux"],
        "certifications": ["CS Degree", "AWS Certified Developer"],
    },
    "Data Science & Data Analytics": {
        "skills": ["statistics", "data visualization", "sql", "feature engineering", "experiment design"],
        "tools": ["pandas", "numpy", "scikit-learn", "tableau"],
        "certifications": ["Certified Data Scientist", "Google Data Analytics Certificate"],
    },
    "Machine Learning Engineering": {
        "skills": ["model training", "model evaluation", "scaling ML", "MLOps"],
        "tools": ["tensorflow", "pytorch", "mlflow", "kubeflow"],
        "certifications": ["TensorFlow Developer Certificate"],
    },
    "Generative AI & LLM / Prompt Engineering": {
        "skills": ["prompt engineering", "LLM fine-tuning", "prompt injection mitigation", "evaluation metrics"],
        "tools": ["openai", "google generative ai", "langchain", "promptflow"],
        "certifications": ["LLM Engineering Certification"],
    },
    "Agentic AI & Autonomous Systems": {
        "skills": ["agent design", "planning", "multi-agent systems", "safety"],
        "tools": ["ray", "rllib", "docker"],
        "certifications": ["Autonomous Systems Specialization"],
    },
    "Computer Vision & Multimodal AI": {
        "skills": ["image processing", "transformers for CV", "multimodal embeddings"],
        "tools": ["opencv", "detectron2", "torchvision"],
        "certifications": ["Computer Vision Specialization"],
    },
    "Robotics & Physical AI (Embedded Intelligence)": {
        "skills": ["robot kinematics", "embedded systems", "sensor fusion", "real-time control"],
        "tools": ["ROS", "arduino", "raspberry pi"],
        "certifications": ["Robotics Nanodegree"],
    },
    "Cybersecurity & AI-Driven Threat Intelligence": {
        "skills": ["network security", "threat hunting", "incident response", "secure coding"],
        "tools": ["wireshark", "metasploit", "ossec"],
        "certifications": ["CISSP", "CEH"],
    },
    "Cloud Computing, DevOps & MLOps": {
        "skills": ["cloud architecture", "CI/CD", "infrastructure as code", "monitoring"],
        "tools": ["aws", "gcp", "terraform", "jenkins"],
        "certifications": ["AWS Certified Solutions Architect", "CKA"],
    },
    "Blockchain, Web3 & Quantum Computing": {
        "skills": ["cryptography", "smart contracts", "distributed ledgers", "quantum algorithms"],
        "tools": ["solidity", "ethereum", "qiskit"],
        "certifications": ["Blockchain Developer Certificate"],
    },
}
