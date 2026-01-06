import redis
import json
import os
from sqlalchemy import text
from src.db.database import SessionLocal
from src.db import models

# ==============================================================================
# CONFIGURATION
# ==============================================================================

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT_NAISPILOT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWD', '')

# ==============================================================================
# MIGRATION LOGIC
# ==============================================================================

def migrate_statistics(redis_client: redis.Redis):
    print("Starting Statistics migration...")
    db = SessionLocal()
    try:
        # 1. analyze_effective_table -> StatisticsEffectiveIp
        print("Migrating analyze_effective_table...")
        data = redis_client.hgetall("analyze_effective_table")
        count = 0
        for k, v in data.items():
            try:
                obj = json.loads(v)
                # Ensure compatibility with model
                # Model fields: TicketID, created_at, bert_component, ai_first_ana_start, ...
                # JSON keys match mostly.
                
                db_obj = models.StatisticsEffectiveIp(
                    TicketID=obj.get("TicketID"),
                    created_at=str(obj.get("created_at", "")),
                    bert_component=obj.get("bert_component"),
                    ai_first_ana_start=float(obj.get("ai_first_ana_start", 0)),
                    create_at_to_ai_ana=float(obj.get("create_at_to_ai_ana", 0)),
                    manually_first_ana_start=float(obj.get("manually_first_ana_start", 0)),
                    create_at_to_manually_ana=float(obj.get("create_at_to_manually_ana", 0)),
                    integration=str(obj.get("integration", "")),
                    create_at_to_integration=float(obj.get("create_at_to_integration", 0)),
                    reject=str(obj.get("reject", "")),
                    create_at_to_reject=float(obj.get("create_at_to_reject", 0)),
                    resovled=str(obj.get("resovled", "")),
                    create_at_to_resovled=float(obj.get("create_at_to_resovled", 0)),
                    tool_name=obj.get("tool_name"),
                    hmi_tag=obj.get("hmi_tag")
                )
                db.merge(db_obj)
                count += 1
            except Exception as e:
                print(f"Error processing item {k}: {e}")
        print(f"Migrated {count} records to StatisticsEffectiveIp.")

        # 2. FIRST_ANALYZE_HASH -> StatisticsManualEfficiency
        print("Migrating FIRST_ANALYZE_HASH...")
        data = redis_client.hgetall("FIRST_ANALYZE_HASH")
        count = 0
        for k, v in data.items():
            try:
                obj = json.loads(v)
                db_obj = models.StatisticsManualEfficiency(
                    TicketID=obj.get("TicketID"),
                    created_at=str(obj.get("created_at", "")),
                    author=obj.get("author"),
                    manually_first_ana_start=float(obj.get("manually_first_ana_start", 0)),
                    create_at_to_manually_ana=float(obj.get("create_at_to_manually_ana", 0)),
                    integration=str(obj.get("integration", "")),
                    create_at_to_integration=float(obj.get("create_at_to_integration", 0)),
                    reject=str(obj.get("reject", "")),
                    create_at_to_reject=float(obj.get("create_at_to_reject", 0)),
                    resovled=str(obj.get("resovled", "")),
                    create_at_to_resovled=float(obj.get("create_at_to_resovled", 0))
                )
                db.merge(db_obj)
                count += 1
            except Exception as e:
                print(f"Error processing item {k}: {e}")
        print(f"Migrated {count} records to StatisticsManualEfficiency.")

        # 3. bert_correct_table -> StatisticsBertCorrect
        print("Migrating bert_correct_table...")
        data = redis_client.hgetall("bert_correct_table")
        count = 0
        for k, v in data.items():
            try:
                obj = json.loads(v)
                # Mapping keys with spaces
                db_obj = models.StatisticsBertCorrect(
                    id=obj.get("id"),
                    bert_component=obj.get("bert component", ""),
                    analyze_component=obj.get("analyze component", ""),
                    correct=bool(obj.get("correct")),
                    manually_analyze=bool(obj.get("manually analyze"))
                )
                db.merge(db_obj)
                count += 1
            except Exception as e:
                print(f"Error processing item {k}: {e}")
        print(f"Migrated {count} records to StatisticsBertCorrect.")

        # 4. BERT_CORRECT_STATS_HISTORY -> StatisticsBertHistory
        print("Migrating BERT_CORRECT_STATS_HISTORY...")
        data = redis_client.lrange("BERT_CORRECT_STATS_HISTORY", 0, -1)
        # Clear existing history to avoid duplicates if re-running
        db.query(models.StatisticsBertHistory).delete()
        count = 0
        for v in data:
            try:
                obj = json.loads(v)
                db_obj = models.StatisticsBertHistory(
                    timestamp=int(obj.get("timestamp", 0)),
                    daily_correct=int(obj.get("daily_correct", 0)),
                    daily_error=int(obj.get("daily_error", 0)),
                    daily_rate=float(obj.get("daily_rate", 0)),
                    cumulative_correct=int(obj.get("cumulative_correct", 0)),
                    cumulative_error=int(obj.get("cumulative_error", 0)),
                    cumulative_rate=float(obj.get("cumulative_rate", 0))
                )
                db.add(db_obj)
                count += 1
            except Exception as e:
                print(f"Error processing history item: {e}")
        print(f"Migrated {count} records to StatisticsBertHistory.")
        
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    print("--- Starting Redis to PostgreSQL Data Migration ---")
    
    redis_client = None
    try:
        print(f"Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
        redis_client.ping()
        print("Redis connection successful.")

        print("Connecting to PostgreSQL...")
        db_test = SessionLocal()
        db_test.execute(text("SELECT 1"))
        db_test.close()
        print("PostgreSQL connection successful.")

        migrate_statistics(redis_client)

        print("\n--- Data Migration Complete! ---")

    except Exception as e:
        print(f"\nAN ERROR OCCURRED: {e}")
    finally:
        if redis_client:
            redis_client.close()
            print("Redis connection closed.")

if __name__ == "__main__":
    main()