import redis
import json
import os

from sqlalchemy.orm import Session
from sqlalchemy import text
# Import necessary components from your application
from src.db.database import SessionLocal
from src.db import crud, models
from src.utils.coreData import CoreData as CoreDataSchema
import redis
import json
import os

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# --- Redis Connection ---
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT_NAISPILOT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWD', '')

# --- Redis Keys and Hashes to Migrate ---
# This list should be comprehensive. Add any other keys if necessary.
SIMPLE_KEYS_TO_SETTINGS = {
    "settings:jira-modules": ("settings", "jira-modules"),
    "settings:llm-monitoring": ("settings", "llm-monitoring"),
    "settings:bert": ("settings", "bert"),
    "settings:jira": ("settings", "jira"),
    "settings:ollama": ("settings", "ollama"),
    "settings:samba": ("settings", "samba"),
}

HASHES_TO_SETTINGS = {
    "HH_TO_SY_JIRA_HASH": "hh_to_sy_jira_hash",
    "jira:custom_fields": "jira_custom_fields",
    # Add other hashes here that should be migrated to the KeyValue table
}

CORE_DATA_HASH = "core_data"

# ==============================================================================
# MIGRATION LOGIC
# ==============================================================================

def migrate_core_data(redis_client: redis.Redis):
    """Migrates all CoreData objects from a Redis hash to the PG table."""
    print("Starting CoreData migration...")
    all_core_data_json = redis_client.hgetall(CORE_DATA_HASH)
    
    print(f"  - Found {len(all_core_data_json)} items in Redis hash '{CORE_DATA_HASH}'.")

    if not all_core_data_json:
        print("No CoreData found in Redis. Skipping.")
        return

    migrated_count = 0
    for key, data_json in all_core_data_json.items():        
        db = None
        try:
            db = SessionLocal()
            # Validate with Pydantic model
            pydantic_obj = CoreDataSchema.model_validate_json(data_json)
            
            # Check if data already exists
            existing_record = crud.get_core_data(db, id=pydantic_obj.id)
            if existing_record:
                update_data = pydantic_obj.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(existing_record, field, value)
                crud.update_core_data(db, core_data=existing_record)
            else:
                new_record = models.CoreData(**pydantic_obj.model_dump())
                crud.create_core_data(db, core_data=new_record)
            
            migrated_count += 1
        except Exception as e:
            print(f"  - ERROR migrating key '{key}': {e}")
            if db:
                db.rollback() # Rollback on error for this specific item
        finally:
            if db:
                db.close() # Close the session for this specific item
    
    print(f"CoreData migration finished. {migrated_count} records processed.")

def migrate_simple_keys(redis_client: redis.Redis):
    """Migrates simple Redis keys to the KeyValue table."""
    print("\nStarting simple key settings migration...")
    migrated_count = 0
    for redis_key, (category, pg_key) in SIMPLE_KEYS_TO_SETTINGS.items():
        db = None
        try:
            db = SessionLocal()
            value = redis_client.get(redis_key)
            if value is not None:
                crud.set_key_value(db, category=category, key=pg_key, value=value.decode('utf-8'))
                print(f"  - Migrated '{redis_key}' to category='{category}', key='{pg_key}'")
                migrated_count += 1
        except Exception as e:
            print(f"  - ERROR migrating key '{redis_key}': {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    print(f"Simple key migration finished. {migrated_count} keys processed.")

def migrate_hashes(redis_client: redis.Redis):
    """Migrates Redis hashes to the KeyValue table."""
    print("\nStarting hash settings migration...")
    migrated_count = 0
    for redis_hash, category in HASHES_TO_SETTINGS.items():
        all_fields = redis_client.hgetall(redis_hash)
        if all_fields:
            for field, value in all_fields.items():
                db = None
                try:
                    db = SessionLocal()
                    crud.set_key_value(db, category=category, key=field.decode('utf-8'), value=value.decode('utf-8'))
                    migrated_count += 1
                except Exception as e:
                    print(f"  - ERROR migrating hash field '{redis_hash} -> {field.decode()}': {e}")
                    if db:
                        db.rollback()
                finally:
                    if db:
                        db.close()
            print(f"  - Migrated {len(all_fields)} fields from hash '{redis_hash}' to category='{category}'")
    print(f"Hash migration finished. {migrated_count} fields processed.")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    print("--- Starting Redis to PostgreSQL Data Migration ---")
    
    redis_client = None
    try:
        print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        redis_client.ping() # Test connection
        print("Redis connection successful.")

        # Test PG connection by creating a temporary session
        print("Connecting to PostgreSQL...")
        db_test = SessionLocal()
        db_test.execute(text("SELECT 1"))
        db_test.close()
        print("PostgreSQL connection successful.")

        # --- Run Migration Tasks ---
        migrate_core_data(redis_client)
        migrate_simple_keys(redis_client)
        migrate_hashes(redis_client)

        print("\n--- Data Migration Complete! ---")

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
        print("Migration failed. Please check your database connections and settings.")
    finally:
        # --- Close Connections ---
        if redis_client:
            redis_client.close()
            print("Redis connection closed.")

