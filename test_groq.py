import os
os.environ['GROQ_API_KEY'] = open('.env').read().split('GROQ_API_KEY=')[1].split('\n')[0].strip()
key = os.environ['GROQ_API_KEY']
print('Key length:', len(key))
print('Key preview:', key[:15])
print('Key valid:', key.startswith('gsk_'))

import asyncio
from groq import AsyncGroq

async def test():
    client = AsyncGroq(api_key=key)
    r = await client.chat.completions.create(
        model='llama3-8b-8192',
        messages=[{'role': 'user', 'content': 'Say hello'}],
        max_tokens=10
    )
    print('SUCCESS:', r.choices[0].message.content)

asyncio.run(test())
