import { useCallback, useEffect, useRef, useState } from 'react';
import { BrowserRouter, useNavigate, useLocation } from 'react-router-dom';
import { Toaster, toast } from 'sonner';
import { World } from './components/World';
import { Hud } from './components/Hud';
import { api } from './lib/api';
import CreateAgent from './pages/CreateAgent';
import Discover from './pages/Discover';
import Profile from './pages/Profile';
import { NewMission,MissionReport,WorkFeed } from './pages/Missions';
import { WalletPanel,TreasuryPanel,ExchangePanel,SkillsPanel,ChatPanel } from './pages/WorldSystems';
import './App.css';
import './layout-refinements.css';
import './world/label-safety.css';

function Civilization(){
 const navigate=useNavigate(),location=useLocation();const engineRef=useRef();
 const [world,setWorld]=useState({agents:[],pool:{},liveAI:false}),[wallet,setWallet]=useState(null),[connectionError,setConnectionError]=useState(false);
 const refresh=useCallback(async()=>{try{const {data}=await api.get('/world');setWorld(data);setConnectionError(false);if(localStorage.getItem('agentws-session')){try{const r=await api.get('/session');setWallet(r.data);}catch(e){if(e.response?.status===401){localStorage.removeItem('agentws-session');setWallet(null);}}}}catch(e){setConnectionError(true);}},[]);
 useEffect(()=>{refresh();const interval=setInterval(refresh,5000);return()=>clearInterval(interval);},[refresh]);
 async function connect(){let token=localStorage.getItem('agentws-demo-identity');if(token){localStorage.setItem('agentws-session',token);try{const {data}=await api.get('/session');setWallet(data);await refresh();return;}catch{localStorage.removeItem('agentws-demo-identity');localStorage.removeItem('agentws-session');}}const {data}=await api.post('/session');localStorage.setItem('agentws-session',data.token);localStorage.setItem('agentws-demo-identity',data.token);setWallet(data.wallet);await refresh();}
 function disconnect(){localStorage.removeItem('agentws-session');setWallet(null);toast.success('Disconnected. Your demo identity is saved on this browser.');}
 const path=location.pathname;const parts=path.split('/').filter(Boolean);const props={world,wallet,navigate,refresh};
 return <main className="civilization-app"><World agents={world.agents} engineRef={engineRef} onInteract={e=>navigate(e.type==='agent'?'/agents/'+e.id:'/'+e.id)}/><Hud {...props} route={path} engineRef={engineRef}/>{connectionError&&<button className="connection-error" data-testid="connection-error" onClick={refresh}>Connection interrupted. Click to reconnect.</button>}{path==='/create'&&<CreateAgent {...props}/>} {path==='/agents'&&<Discover {...props}/>} {parts[0]==='agents'&&parts[1]&&!parts[2]&&<Profile {...props} id={parts[1]}/>} {parts[0]==='agents'&&parts[2]==='mission'&&<NewMission {...props} id={parts[1]}/>} {parts[0]==='missions'&&parts[1]&&<MissionReport {...props} id={parts[1]}/>} {path==='/work-feed'&&<WorkFeed {...props}/>} {path==='/wallet'&&<WalletPanel {...props} connect={connect} disconnect={disconnect}/>} {path==='/treasury'&&<TreasuryPanel {...props}/>} {path==='/exchange'&&<ExchangePanel {...props}/>} {path==='/skills'&&<SkillsPanel {...props}/>} {path==='/chat'&&<ChatPanel {...props}/>}<Toaster theme="dark" position="top-center" richColors/></main>;
}
export default function App(){return <BrowserRouter><Civilization/></BrowserRouter>;}