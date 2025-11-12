from datetime import datetime

def discord_timestamp_from_id(snowflake_id: str) -> str:
    try:
        timestamp_ms = (int(snowflake_id) >> 22) + 1420070400000
        return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return "Desconhecido"
