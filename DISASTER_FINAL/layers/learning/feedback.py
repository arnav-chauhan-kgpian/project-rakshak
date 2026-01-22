import datetime

class FeedbackAgent:
    """
    Agent 16: Feedback Learning Loop (RLHF)
    Captures user interaction/corrections and persists them to long-term memory.
    This enables the system to learn patterns of "what went wrong" or "what was helpful".
    """
    def __init__(self, memory_agent):
        self.memory = memory_agent

    def process_feedback(self, incident_id: str, score: int, comment: str, 
                         context_id: str = None) -> bool:
        """
        Process user feedback.
        
        Args:
            incident_id: ID of the incident
            score: 1-5 rating (1=Bad, 5=Perfect)
            comment: Text explanation
            context_id: (Optional) ID of the memory context to reinforce directly
        
        Returns:
            Success status
        """
        try:
            timestamp = datetime.datetime.utcnow().isoformat()
            
            # 1. RLHF: Reinforcement
            # If high score, reinforce the context memory (increase access count/weight)
            if score >= 4 and context_id:
                print(f"  [RLHF] Positive reinforcement for context {context_id}")
                self.memory.reinforce(context_id)
            
            # 2. Store Feedback Record
            # We treat feedback as "Knowledge" so it persists and is searchable
            feedback_content = f"Review for {incident_id}: {comment} (Rating: {score}/5)"
            
            # Note: We use a zero-vector for dense since MemoryStore requires an embedding.
            # This relies on sparse/BM25 search for retrieval (content-based).
            # Future: Support sparse-only upsert when Qdrant enables it.
            dummy_vector = [0.0] * 768
            
            self.memory.store(
                memory_type="knowledge",
                content=feedback_content,
                embedding=dummy_vector,  # Placeholder - retrieval uses sparse text matching 
                metadata={
                    "type": "feedback",
                    "target_incident": incident_id,
                    "score": score,
                    "timestamp": timestamp
                },
                tags=["feedback", "rlhf", f"score_{score}"]
            )
            
            print(f"  [Feedback] Stored review for {incident_id} (Score {score})")
            return True
            
        except Exception as e:
            print(f"Feedback Agent Error: {e}")
            return False
