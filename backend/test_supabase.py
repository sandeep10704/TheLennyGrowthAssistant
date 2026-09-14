import asyncio
import asyncpg

async def test():
    hosts = [
        'aws-1-ap-south-1.pooler.supabase.com',
        'aws-0-ap-south-1.pooler.supabase.com',
        'aws-1-ap-southeast-1.pooler.supabase.com',
        'aws-0-ap-southeast-1.pooler.supabase.com',
        'aws-1-us-east-1.pooler.supabase.com',
        'aws-0-us-east-1.pooler.supabase.com',
    ]
    ports = [6543, 5432]
    users = ['postgres.ajatrfdppielcynggwgx', 'postgres']
    pwd = 'SaiVenkataSandeep'
    
    for host in hosts:
        for port in ports:
            for user in users:
                try:
                    print(f'Trying {host}:{port} ({user})...')
                    conn = await asyncpg.connect(f'postgresql://{user}:{pwd}@{host}:{port}/postgres', timeout=4)
                    print(f'===> SUCCESS! Connected to {host}:{port} with user {user}')
                    val = await conn.fetchval('SELECT 1')
                    print(f'SELECT 1 result: {val}')
                    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    print('Tables in public schema:', [t['table_name'] for t in tables])
                    for t in tables:
                        tname = t['table_name']
                        cnt = await conn.fetchval(f'SELECT count(*) FROM "{tname}"')
                        print(f'  Table {tname}: {cnt} rows')
                    await conn.close()
                    return host, port, user
                except Exception as e:
                    print(f'  Failed: {e}')

if __name__ == '__main__':
    res = asyncio.run(test())
    print('Final result:', res)
