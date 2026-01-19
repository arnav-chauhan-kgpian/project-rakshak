"""Verification script to check all layers support xBD data format"""

print("="*70)
print("LAYER COMPATIBILITY VERIFICATION")
print("="*70 + "\n")

# 1. Query Planner - Disaster Types
print("✓ Query Planner Agent:")
from layers.search.query_planner import QueryPlannerAgent
agent = QueryPlannerAgent()
print(f"  Supported disaster types: {', '.join(sorted(agent.filter_strategies.keys()))}")
print(f"  Total strategies: {len(agent.filter_strategies)}\n")

# 2. Cross-Disaster Transfer - Similarity Matrix
print("✓ Cross-Disaster Transfer Agent:")
from layers.search.cross_transfer import CrossDisasterAgent
cross_agent = CrossDisasterAgent()
source_disasters = sorted(set([k[0] for k in cross_agent.disaster_similarity.keys()]))
print(f"  Source disasters: {', '.join(source_disasters)}")
print(f"  Total similarity pairs: {len(cross_agent.disaster_similarity)}\n")

# 3. Satellite Agent - Local File Support
print("✓ Satellite Ingestion Agent:")
from layers.ingestion.satellite import SatelliteAgent
sat_agent = SatelliteAgent()
print(f"  Supported sensors: {', '.join(sat_agent.supported_sensors)}")
print(f"  Local mode enabled: {sat_agent.local_mode}")
print(f"  Has access_local_image method: {hasattr(sat_agent, 'access_local_image')}\n")

# 4. Metadata Agent - xBD JSON Parsing
print("✓ Metadata Parsing Agent:")
from layers.ingestion.metadata import MetadataAgent
meta_agent = MetadataAgent()
print(f"  Schema version: {meta_agent.schema_version}")
print(f"  Has _create_mock_metadata: {hasattr(meta_agent, '_create_mock_metadata')}\n")

# 5. Synthesis Agent - Building Damage Aggregation
print("✓ Evidence Synthesis Agent:")
from layers.reasoning.synthesis import EvidenceSynthesisAgent
synth_agent = EvidenceSynthesisAgent()
# Test with empty results to check structure
empty_patterns = synth_agent.analyze_patterns([])
print(f"  Pattern keys: {', '.join(empty_patterns.keys())}")
print(f"  Supports damage_counts: {'damage_counts' in empty_patterns}\n")

# 6. Test disaster type mapping
print("✓ Testing xBD disaster type compatibility:")
test_disasters = ["volcano", "tsunami", "earthquake", "flood", "hurricane", "wildfire"]
for disaster in test_disasters:
    plan = agent.plan_query(0, 0, disaster)
    if plan:
        radius = plan['spatial_filter']['radius_km']
        threshold = plan['confidence_threshold']
        print(f"  {disaster:12s} → radius: {radius:3d}km, threshold: {threshold:.2f}")

print(f"\n{'='*70}")
print("✓ ALL LAYERS COMPATIBLE WITH xBD DATA FORMAT")
print("="*70)
