import asyncio, logging, time
from db import db, stamp
from providers import live_execute, demo_execute
from economy import settle_mission, refresh_agent

logger=logging.getLogger(__name__)

async def run_mission(mid):
    m=await db.missions.find_one({'id':mid},{'_id':0})
    if not m or m['status'] in ['COMPLETED','FAILED']: return
    a=await db.agents.find_one({'id':m['agentId']},{'_id':0})
    async def stage(status):
        await db.missions.update_one({'id':mid},{'$set':{'status':status},'$push':{'events':{'status':status,'timestamp':stamp()}}})
    last_write=0
    async def output(text,sources):
        nonlocal last_write
        if time.monotonic()-last_write<.35: return
        last_write=time.monotonic()
        await db.missions.update_one({'id':mid},{'$set':{'output':text,'sources':sources}})
    try:
        if m['status']!='SETTLING':
            await stage('PLANNING')
            provider=live_execute if m['mode']=='live' else demo_execute
            text,sources=await asyncio.wait_for(provider(m,a,stage,output),timeout=180)
            await db.missions.update_one({'id':mid},{'$set':{'output':text,'sources':sources,'status':'SETTLING'}})
        await settle_mission(await db.missions.find_one({'id':mid},{'_id':0}),a)
    except asyncio.CancelledError:
        raise # Preserve unfinished state for startup recovery.
    except Exception as exc:
        logger.exception('Mission %s failed',mid)
        current=await db.missions.find_one({'id':mid},{'_id':0})
        if current and current['status']=='SETTLING':
            # Economic settlement is recoverable and idempotent; do not mark as failed.
            return
        await db.missions.update_one({'id':mid},{'$set':{'status':'FAILED','error':'Execution could not complete. '+str(exc)[:220], 'completedAt':stamp()}})
        await db.agents.update_one({'id':a['id'],'workingMissionId':mid},{'$set':{'workingMissionId':None}})
        await refresh_agent(await db.agents.find_one({'id':a['id']},{'_id':0}))