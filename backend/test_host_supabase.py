import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect('postgresql://postgres:SaiVenkataSandeep@db.ajatrfdppielcynggwgx.supabase.co:5432/postgres', timeout=10)
    rows = await conn.fetch("""
        SELECT table_schema, table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name IN ('sessions', 'messages', 'chat_sessions', 'chat_messages')
        ORDER BY table_schema, table_name, ordinal_position
    """)
    for r in rows:
        print(f"{r['table_schema']}.{r['table_name']}.{r['column_name']} ({r['data_type']}, nullable={r['is_nullable']})")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(test())
