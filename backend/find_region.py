import asyncio
import asyncpg
import ssl

regions = [
    'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
    'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1',
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'ca-central-1', 'sa-east-1'
]

async def test():
    user = 'postgres.ajatrfdppielcynggwgx'
    pwd = 'SaiVenkataSandeep'
    
    for r in regions:
        for prefix in ['aws-0', 'aws-1']:
            host = f'{prefix}-{r}.pooler.supabase.com'
            for port in [6543, 5432]:
                try:
                    conn = await asyncpg.connect(f'postgresql://{user}:{pwd}@{host}:{port}/postgres', timeout=3)
                    print(f'FOUND! {host}:{port}')
                    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    print('Tables:', [t['table_name'] for t in tables])
                    await conn.close()
                    return host, port
                except Exception as e:
                    err = str(e)
                    if 'password authentication failed' in err:
                        print(f'TENANT FOUND at {host}:{port}, but bad password!')
                        return host, port
                    if 'not found' not in err and 'Name or service not known' not in err and 'timeout' not in err and 'No address' not in err:
                        print(f'{host}:{port} -> {err}')

if __name__ == '__main__':
    asyncio.run(test())
