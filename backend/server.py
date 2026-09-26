import os, uuid, secrets, hashlib, asyncio
from datetime import timedelta, datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, BackgroundTasks
from starlette.middleware.cors import CORSMiddleware
from db import db, client, now, stamp
from models import AgentCreate, MissionCreate, ChatCreate, HoldingsUpdate, Document
from economy import refresh_agent, HOLDING_REQUIREMENT
from seed import initialize

@asynccontextmanager
async def lifespan(app):
    await initialize()
    # Recovery is request-work recovery, not a scheduled timer. Never roll rewards twice.
    from missions import run_mission
    pending = await db.missions.find({'status': {'$nin': ['COMPLETED', 'FAILED']}}, {'_id':0}).to_list(100)
    tasks = [asyncio.create_task(run_mission(m['id'])) for m in pending]
    yield
    for t in tasks: t.cancel()
    client.close()

app = FastAPI(title='Agent.ws Civilization', lifespan=lifespan)
api = APIRouter(prefix='/api')
app.add_middleware(CORSMiddleware, allow_origins=os.environ['CORS_ORIGINS'].split(','), allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

async def identity(authorization: str = Header(default='')):
    token = authorization.removeprefix('Bearer ')
    session = await db.sessions.find_one({'tokenHash': hashlib.sha256(token.encode()).hexdigest()}, {'_id':0})
    if not session or datetime.fromisoformat(session['expiresAt']) <= now():
        raise HTTPException(401, 'Connect your identity to continue.')
    return await db.wallets.find_one({'id': session['walletId']}, {'_id':0})

async def owned(aid, user):
    agent = await db.agents.find_one({'id': aid}, {'_id':0})
    if not agent: raise HTTPException(404, 'Agent not found.')
    if agent['creatorWallet'] != user['id']: raise HTTPException(403, 'Only the creator can access this private workspace.')
    return await refresh_agent(agent)

def public_agent(a):
    return {k:v for k,v in a.items() if k not in ['settledMissionIds', 'workingMissionId']}

@api.get('/')
async def health():
    return {'name':'Agent.ws', 'status':'online', 'walletMode':'demo', 'rewardsMode':'demo', 'liveAI': bool(os.environ.get('EMERGENT_LLM_KEY'))}

@api.post('/session')
async def connect():
    if os.environ['WALLET_MODE'] != 'demo': raise HTTPException(503, 'Live wallet verification is not configured.')
    token = secrets.token_urlsafe(40)
    wallet = {'id': 'ws_' + secrets.token_hex(20), 'balance':150000, 'mode':'demo', 'createdAt':stamp()}
    await db.wallets.insert_one(wallet.copy())
    await db.sessions.insert_one({'id':str(uuid.uuid4()), 'walletId':wallet['id'], 'tokenHash':hashlib.sha256(token.encode()).hexdigest(), 'expiresAt':(now()+timedelta(days=30)).isoformat()})
    return {'token':token, 'wallet':wallet}

@api.get('/session', response_model=Document)
async def session(user=Depends(identity)): return user

@api.patch('/session/holdings', response_model=Document)
async def holdings(data: HoldingsUpdate, user=Depends(identity)):
    if os.environ['WALLET_MODE'] != 'demo' or user['mode'] != 'demo': raise HTTPException(403, 'Demo only.')
    await db.wallets.update_one({'id':user['id']}, {'$set':{'balance':data.balance}})
    agents = await db.agents.find({'creatorWallet':user['id']}, {'_id':0}).to_list(100)
    for a in agents: await refresh_agent(a)
    return {**user, 'balance':data.balance}

@api.get('/world')
async def world():
    agents = await db.agents.find({}, {'_id':0}).to_list(500)
    agents = [await refresh_agent(a) for a in agents]
    pool = await db.pool.find_one({'id':'main'}, {'_id':0})
    return {'agents':[public_agent(a) for a in agents], 'population':len(agents), 'active':sum(a['status'] in ['ACTIVE','WORKING'] for a in agents), 'jobsCompleted':sum(a['jobsCompleted'] for a in agents), 'pool':{'balanceUSDC':pool['balanceCents']/100, 'distributedUSDC':(pool['initialCents']-pool['balanceCents'])/100, 'mode':'demo'}, 'liveAI':bool(os.environ.get('EMERGENT_LLM_KEY'))}

@api.get('/agents', response_model=list[Document])
async def agents(category: str = '', sort: str = 'recent', mine: bool = False, authorization: str = Header(default='')):
    query = {'category':category} if category else {}
    if mine: query['creatorWallet'] = (await identity(authorization))['id']
    rows = await db.agents.find(query, {'_id':0}).sort('jobsCompleted' if sort == 'active' else 'createdAt', -1).to_list(500)
    return [public_agent(await refresh_agent(a)) for a in rows]

@api.post('/agents', response_model=Document)
async def create_agent(data: AgentCreate, user=Depends(identity)):
    if user['balance'] < HOLDING_REQUIREMENT: raise HTTPException(403, 'Hold at least 100,000 $AGENTWS to create an agent. No tokens are spent.')
    if len(data.name.strip()) < 2: raise HTTPException(422, 'Give your agent a name of at least two characters.')
    if await db.agents.count_documents({'creatorWallet':user['id']}) >= 10: raise HTTPException(409, 'Early civilization limit: 10 agents per creator.')
    agent = data.model_dump()
    agent.update(id=str(uuid.uuid4()), name=data.name.strip(), creatorWallet=user['id'], energy=100, energyResetAt=None, treasuryCents=0, jobsCompleted=0, status='ACTIVE', reputation='New resident', createdAt=stamp(), demoResident=False, history=[{'event':'Agent created', 'timestamp':stamp()}], settledMissionIds=[], workingMissionId=None)
    await db.agents.insert_one(agent.copy())
    return public_agent(agent)

@api.get('/agents/{aid}', response_model=Document)
async def profile(aid: str):
    a = await db.agents.find_one({'id':aid}, {'_id':0})
    if not a: raise HTTPException(404, 'Agent not found.')
    return public_agent(await refresh_agent(a))

@api.get('/agents/{aid}/missions', response_model=list[Document])
async def agent_missions(aid: str, user=Depends(identity)):
    await owned(aid, user)
    return await db.missions.find({'agentId':aid, 'creatorWallet':user['id']}, {'_id':0}).sort('startedAt',-1).to_list(100)

@api.get('/missions', response_model=list[Document])
async def feed(user=Depends(identity)):
    return await db.missions.find({'creatorWallet':user['id']}, {'_id':0}).sort('startedAt',-1).to_list(100)

@api.post('/missions', response_model=Document, status_code=202)
async def start(data: MissionCreate, background: BackgroundTasks, user=Depends(identity)):
    from missions import run_mission
    if len(data.mission.strip()) < 10: raise HTTPException(422, 'Describe your objective in at least ten characters.')
    a = await owned(data.agentId, user)
    if user['balance'] < HOLDING_REQUIREMENT: raise HTTPException(403, 'Agent is sleeping. Restore the 100,000 $AGENTWS holding requirement.')
    if a['energy'] < 10: raise HTTPException(409, 'Agent is resting. Energy restores five hours after the first completed mission in this cycle.')
    if data.mode == 'live' and not os.environ.get('EMERGENT_LLM_KEY'): raise HTTPException(503, 'The research engine is temporarily unavailable.')
    mid = str(uuid.uuid4())
    lock = await db.agents.update_one({'id':a['id'], 'workingMissionId':None, 'energy':{'$gte':10}}, {'$set':{'workingMissionId':mid, 'status':'WORKING'}})
    if not lock.modified_count: raise HTTPException(409, 'This agent already has a mission in progress.')
    m = {'id':mid, 'agentId':a['id'], 'agentName':a['name'], 'creatorWallet':user['id'], 'mission':data.mission, 'mode':data.mode, 'status':'MISSION RECEIVED', 'startedAt':stamp(), 'completedAt':None, 'output':'', 'sources':[], 'events':[{'status':'MISSION RECEIVED', 'timestamp':stamp()}], 'keepPrivate':True}
    await db.missions.insert_one(m.copy())
    background.add_task(run_mission, mid)
    return m

@api.get('/missions/{mid}', response_model=Document)
async def mission(mid: str, user=Depends(identity)):
    m = await db.missions.find_one({'id':mid, 'creatorWallet':user['id']}, {'_id':0})
    if not m: raise HTTPException(404, 'Private mission not found.')
    return m

@api.post('/missions/{mid}/keep-private')
async def keep_private(mid: str, user=Depends(identity)):
    m = await mission(mid, user)
    await db.missions.update_one({'id':m['id']}, {'$set':{'keepPrivate':True, 'reviewedAt':stamp()}})
    return {'private':True, 'message':'This report remains private.'}

@api.get('/chat', response_model=list[Document])
async def chat():
    rows = await db.chat.find({}, {'_id':0}).sort('timestamp',-1).limit(50).to_list(50)
    return list(reversed(rows))

@api.post('/chat', response_model=Document)
async def send_chat(data: ChatCreate, user=Depends(identity)):
    if not data.message.strip(): raise HTTPException(422, 'Write a message first.')
    recent = await db.chat.count_documents({'walletId':user['id'], 'timestamp':{'$gte':(now()-timedelta(seconds=30)).isoformat()}})
    if recent >= 5: raise HTTPException(429, 'Take a breath. You can send five messages every 30 seconds.')
    message = {'id':str(uuid.uuid4()), 'walletId':user['id'], 'author':'Explorer · '+user['id'][-4:], 'message':data.message.strip(), 'timestamp':stamp()}
    await db.chat.insert_one(message.copy())
    return message

app.include_router(api)