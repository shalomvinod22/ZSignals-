from dotenv import load_dotenv
load_dotenv()

import os
import json
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
actor = client.actor("harvestapi/linkedin-post-search").get()

print("=" * 60)
print("ACTOR INFO")
print("=" * 60)
print(f"Name: {actor.get('name')}")
print(f"Title: {actor.get('title')}")
print(f"Username: {actor.get('username')}")
print()
print("=" * 60)
print("DESCRIPTION (first 500 chars)")
print("=" * 60)
print(actor.get("description", "")[:500])
print()
print("=" * 60)
print("EXAMPLE RUN INPUT (this is what we need!)")
print("=" * 60)
example = actor.get("exampleRunInput", {})
if example:
    print(json.dumps(example, indent=2))
else:
    print("No example provided in metadata")
print()
print("=" * 60)
print("INPUT SCHEMA KEYS")
print("=" * 60)
schema = actor.get("inputSchema", {})
if isinstance(schema, dict) and "properties" in schema:
    for key, details in schema.get("properties", {}).items():
        print(f"- {key}: {details.get('type', 'unknown')} - {details.get('title', details.get('description', ''))[:80]}")
elif isinstance(schema, str):
    # Sometimes it's a JSON string
    try:
        parsed = json.loads(schema)
        for key, details in parsed.get("properties", {}).items():
            print(f"- {key}: {details.get('type', 'unknown')} - {details.get('title', '')[:80]}")
    except Exception:
        print("Schema is string but not parseable JSON, raw:")
        print(schema[:1000])
else:
    print(f"Schema type: {type(schema)}, value: {str(schema)[:500]}")