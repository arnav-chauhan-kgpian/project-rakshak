class LLMReasoningAgent:
    """Agent 10: Citation LLM Reasoning - Generates damage reports with source citations"""
    
    def __init__(self):
        self.report_template = """
        DAMAGE ASSESSMENT REPORT
        ========================
        Incident ID: {incident_id}
        Assessment Time: {timestamp}
        Disaster Type: {disaster_type}
        
        SEVERITY ASSESSMENT:
        - Primary Damage Level: {primary_damage}
        - Affected Area: ~{affected_area_km2} km²
        - Geographic Center: Lat {lat:.4f}, Lon {lon:.4f}
        
        ANALYSIS:
        {analysis}
        
        EVIDENCE SOURCES:
        {citations}
        
        CONFIDENCE SCORE: {confidence:.2%}
        """
    
    def generate_report(self, incident_id, search_results):
        """
        Generates damage assessment report with citations.
        
        Args:
            incident_id: Unique incident identifier
            search_results: List of evidence from search results
            
        Returns:
            Formatted report string
        """
        try:
            if not search_results:
                return "No evidence available for report generation."
            
            # Extract key information
            primary_result = search_results[0]
            # Prefer full_metadata if present; otherwise fall back to payload fields
            metadata = primary_result["payload"].get("full_metadata") or primary_result["payload"]
            
            # Generate analysis text
            analysis = f"""
            Multiple satellite images analyzed showing significant damage patterns.
            Primary evidence source indicates {metadata.get('disaster_type', 'unknown').title()} 
            damage with approximately {len(search_results)} correlated incidents identified.
            Vector similarity analysis shows strong matching (score: {primary_result['score']:.2f}).
            """
            
            # Generate citations
            citations = ""
            for i, result in enumerate(search_results[:5], 1):
                payload = result["payload"]
                citations += f"[{i}] Incident {payload.get('incident_id')} - "
                citations += f"Timestamp: {payload.get('timestamp')}, "
                citations += f"Match Score: {result['score']:.2f}\n"
            
            # Format report
            report = self.report_template.format(
                incident_id=incident_id,
                timestamp=metadata.get("timestamp", "Unknown"),
                disaster_type=metadata.get("disaster_type", "Unknown"),
                primary_damage=primary_result["payload"].get("damage_severity", "Medium"),
                affected_area_km2=int(len(search_results) * 15),
                lat=primary_result["payload"].get("latitude", 0),
                lon=primary_result["payload"].get("longitude", 0),
                analysis=analysis,
                citations=citations,
                confidence=primary_result["score"]
            )
            return report
        except Exception as e:
            print(f"LLM Reasoning Error: {e}")
            return f"Error generating report: {str(e)}"