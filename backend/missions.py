import asyncio, logging, time
from db import db, stamp
from providers import live_execute, demo_execute
from research_pipeline import execute_research
from economy import settle_mission, refresh_agent

logger=logging.getLogger(__name__)

async def run_mission(mid):
    m=await db.missions.find_one({'id':mid},{'_id':0})
    if not m or m['status'] in ['COMPLETED','FAILED']: return
    a=await db.agents.find_one({'id':m['agentId']},{'_id':0})
    current_stage=m['status']
    async def stage(status,detail='',artifacts=None):
        nonlocal current_stage
        fields={'status':status,'phaseDetail':detail}
        if artifacts:
            fields.update({f'artifacts.{k}':v for k,v in artifacts.items()})
        update={'$set':fields}
        if current_stage!=status:
            update['$push']={'events':{'status':status,'timestamp':stamp(),'detail':detail}}
            current_stage=status
        await db.missions.update_one({'id':mid},update)
    last_write=0
    last_source_count=-1
    async def output(text,sources):
        nonlocal last_write,last_source_count
        if time.monotonic()-last_write<.35 and len(sources)==last_source_count: return
        last_write=time.monotonic()
        last_source_count=len(sources)
        await db.missions.update_one({'id':mid},{'$set':{'output':text,'sources':sources}})
    try:
        if m['status']!='SETTLING':
            provider=execute_research if m['mode']=='live' else demo_execute
            if m['mode']!='live': await stage('PLANNING','Preparing an illustrative execution.')
            text,sources=await asyncio.wait_for(provider(m,a,stage,output),timeout=420)
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