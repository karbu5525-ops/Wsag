from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

CATEGORIES = ['Research', 'Analyst', 'Scout', 'Content', 'Builder', 'Social Intelligence']

class Document(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str

class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    avatar: Literal['mint', 'coral', 'blue', 'gold', 'violet', 'white'] = 'mint'
    category: Literal['Research', 'Analyst', 'Scout', 'Content', 'Builder', 'Social Intelligence']
    brainConfig: str = 'OpenAI GPT-5.4'
    strategy: str = Field(default='Compare multiple sources, cross-check claims, and produce concise findings.', max_length=3000)
    tools: list[Literal['Public search', 'GitHub', 'Read websites']] = Field(default_factory=lambda: ['Public search', 'GitHub', 'Read websites'])
    dataSources: str = Field(default='Public websites and GitHub', max_length=2000)
    rules: str = Field(default='Cite sources. Separate facts from uncertainty. Never trade or spend funds.', max_length=3000)
    outputFormat: Literal['Structured report', 'Bullet points', 'Concise X post'] = 'Structured report'
    behavior: Literal['Careful & methodical', 'Curious & exploratory', 'Concise & direct'] = 'Careful & methodical'

class MissionCreate(BaseModel):
    agentId: str
    mission: str = Field(min_length=10, max_length=3000)
    mode: Literal['live', 'demo'] = 'live'

class ChatCreate(BaseModel):
    message: str = Field(min_length=1, max_length=500)

class HoldingsUpdate(BaseModel):
    balance: int = Field(ge=0, le=1000000)