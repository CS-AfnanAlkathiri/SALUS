import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, NavLink, Route, Routes, Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import { Activity, ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, Brain, CalendarDays, ChevronDown, ChevronRight, CircleHelp, ClipboardCheck, Cross, HeartPulse, History as HistoryIcon, Moon, ScanLine, Search, ShieldPlus, Siren, Sparkles, Thermometer, X } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import '@fontsource/space-grotesk/latin-500.css';
import '@fontsource/space-grotesk/latin-700.css';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import './style.css';
import { Anatomy } from './Anatomy';
import { api, format, readings, type Schemas as S } from './api';

type CrewContext = { crew: string; day: number; setCrew: (id: string) => void; setDay: (day: number) => void };
type Status = { baseline_status: string; available: boolean };
const regionIcons = { general_health: Activity, head_brain: Brain, chest_heart: HeartPulse, abdomen: ScanLine, musculoskeletal: Cross };
const nav = [['/', 'Explore', ScanLine], ['/assess', 'Assess', ClipboardCheck], ['/history', 'Health history', HistoryIcon], ['/knowledge', 'Knowledge', BookOpen]] as const;
const names = (key: string) => readings[key] || [key.replaceAll('_',' '), ''];
const readable = (value: string) => value.replaceAll('_', ' ').replace(/^./, l => l.toUpperCase());
const errorText = (err: unknown) => err instanceof Error ? err.message : 'Something went wrong. Please try again.';
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 30_000 } } });

function ErrorNote({ error }: { error: unknown }) {
  return error ? <p className="error" role="alert">{errorText(error)}</p> : null;
}

function useHistory(crew: string, day: number) {
  return useQuery({queryKey: ['history', crew, day], queryFn: () => api<S['History']>(`/astronauts/${crew}/history?through_day=${day}`)});
}

function useRegions() {
  return useQuery({queryKey: ['regions'], queryFn: () => api<S['Region'][]>('/body-regions')});
}

function EvidenceCard({ source }: { source: S['Evidence'] }) {
  return <article className="evidence-card"><div className="eyebrow"><BookOpen size={14}/> NASA research</div><h3>{source.section}</h3><p>{source.passage}</p><a href={source.url} target="_blank" rel="noreferrer">{source.title} <ArrowUpRight size={14}/></a></article>;
}

function PageTitle({ label, title, children }: { label: string; title: string; children?: ReactNode }) {
  return <header className="page-title"><p className="eyebrow">{label}</p><h1>{title}</h1>{children && <p>{children}</p>}</header>;
}

function Sparkline({ data, color }: { data: (number | undefined)[]; color: string }) {
  const values = data.filter((v): v is number => v != null);
  if (values.length < 2) return null;
  const min = Math.min(...values), range = Math.max(...values) - min || 1;
  let path = '', move = true;
  data.forEach((value, index) => {
    if (value == null) { move = true; return; }
    path += `${move ? 'M' : 'L'}${index / (data.length-1)*106},${29 - (value-min)/range*22} `;
    move = false;
  });
  return <svg className="sparkline" viewBox="0 0 106 34" aria-hidden="true"><path d={path} stroke={color} strokeWidth="2" fill="none" vectorEffect="non-scaling-stroke"/></svg>;
}

function Explore({ ctx }: { ctx: CrewContext }) {
  const [selected, setSelected] = useState('general_health');
  const history = useHistory(ctx.crew, ctx.day), regions = useRegions();
  const baseline = useQuery({queryKey: ['baseline', ctx.crew, ctx.day], queryFn: () => api<Status>(`/ml/status/${ctx.crew}?mission_day=${ctx.day}`)});
  const region = regions.data?.find(r => r.id === selected);
  const latest = history.data?.records.find(point => point.mission_day === ctx.day);
  const trend = history.data?.records.slice(-12) || [];
  const metrics = [
    {key:'resting_hr_bpm', icon:HeartPulse, color:'#7466bb', tint:'violet'},
    {key:'sleep_hours', icon:Moon, color:'#5296ab', tint:'blue'},
    {key:'body_temp_c', icon:Thermometer, color:'#588e92', tint:'teal'},
  ];
  const RegionIcon = regionIcons[selected as keyof typeof regionIcons] || Activity;
  return <>
    <div className="explore-top"><PageTitle label="MISSION HEALTH WORKSTATION" title="Health overview">Explore body systems and assess changes in your mission health.</PageTitle>
      <div className="day-chip"><CalendarDays size={17}/><span>Mission day</span><strong>{String(ctx.day).padStart(2,'0')}</strong></div></div>
    <div className="workspace">
      <section className="overview" aria-label="Latest readings">
        <div className="section-title"><h2>Latest readings</h2><span>Day {ctx.day}</span></div>
        <ErrorNote error={history.error}/>
        {metrics.map(({key,icon:Icon,color,tint}) => <article className="metric-card" key={key}>
          <div className="metric-title"><span className={'metric-icon '+tint}><Icon size={17}/></span>{names(key)[0]}</div>
          <div className="metric-value">{history.isPending ? '…' : format(latest?.readings[key])} <small>{names(key)[1]}</small></div>
          <Sparkline color={color} data={trend.map(p => p.readings[key])}/>
        </article>)}
        <div className="baseline"><span className="baseline-icon"><Activity size={16}/></span><div><strong>Personal baseline</strong><p>{baseline.isPending ? 'Checking…' : baseline.error || !baseline.data?.available ? 'Unavailable' : baseline.data.baseline_status === 'ready' ? 'Ready for comparison' : 'Collecting mission history'}</p></div></div>
        <Link className="text-link" to="/history">View health history <ArrowRight size={16}/></Link>
      </section>
      <Anatomy selected={selected} select={setSelected}/>
      <section className="context" aria-label="Selected body region">
        <div className="section-title"><h2>Self-assessment</h2><ClipboardCheck size={17}/></div>
        <ErrorNote error={regions.error}/>
        {region ? <div className="context-card">
          <span className="context-icon"><RegionIcon size={25}/></span>
          <h2>{region.title}</h2><p>{region.description}</p>
          {region.concerns.length > 0 ? <>
            <div className="path-label">Available assessments</div>
            <div className="path-links">{region.concerns.map(concern => <Link key={concern}
              to={'/assess?' + new URLSearchParams({region:selected,concern})}>{concern}<ChevronRight size={15}/></Link>)}</div>
            <Link className="button primary" to={'/assess?region='+selected}>Start assessment <ArrowRight size={17}/></Link>
          </> : <Link className="button primary" to={'/knowledge?'+new URLSearchParams({topic:region.evidence_topic})}>Explore NASA research <ArrowRight size={16}/></Link>}
        </div> : !regions.error && <p className="muted">Loading body region…</p>}
        <Link className="knowledge-link" to="/knowledge"><span className="knowledge-icon"><BookOpen size={18}/></span><span><strong>NASA Knowledge</strong><small>Spaceflight research and measurement guides</small></span><ArrowUpRight size={17}/></Link>
      </section>
    </div>
  </>;
}

function StartAssessment({ ctx }: { ctx: CrewContext }) {
  const navTo = useNavigate(), {search} = useLocation(), params = new URLSearchParams(search);
  const regions = useRegions();
  const history = useHistory(ctx.crew, ctx.day);
  const [regionId, setRegion] = useState(params.get('region') || 'general_health');
  const [concern, setConcern] = useState(params.get('concern') || '');
  const [busy, setBusy] = useState(false), [error, setError] = useState<unknown>(null);
  const region = regions.data?.find(item => item.id === regionId);
  const activeConcern = region?.concerns.includes(concern) ? concern : region?.concerns[0];
  const draft = history.data?.assessments.find(s => s.status === 'in_progress');
  async function start(e: FormEvent) {
    e.preventDefault();
    if (!activeConcern || busy) return;
    setBusy(true); setError(null);
    try {
      const data = await api<S['Progress']>('/assessments', {astronaut_id:ctx.crew, mission_day:ctx.day, body_region:regionId, concern:activeConcern} satisfies S['Start']);
      await queryClient.invalidateQueries({queryKey:['history',ctx.crew]});
      navTo('/assess/'+data.session.assessment_id);
    } catch (err) { setError(err); } finally { setBusy(false); }
  }
  return <div className="subpage"><PageTitle label={`${ctx.crew} · MISSION DAY ${ctx.day}`} title="Start an assessment">Choose the concern you want to record and review.</PageTitle>
    <ErrorNote error={error || regions.error}/>
    {draft && <div className="resume-note"><span>In progress · {draft.concern} · Day {draft.mission_day}</span><Link to={'/assess/'+draft.assessment_id}>Resume <ArrowRight size={15}/></Link></div>}
    <form className="surface form-card" onSubmit={start}>
      <label>Body region<select value={regionId} onChange={e=>{setRegion(e.target.value);setConcern('');}}>
        {regions.data?.filter(r=>r.concerns.length).map(r=><option key={r.id} value={r.id}>{r.title}</option>)}</select></label>
      <label>Health concern<select value={activeConcern || ''} onChange={e=>setConcern(e.target.value)}>
        {region?.concerns.map(item=><option key={item}>{item}</option>)}</select></label>
      <button className="button primary" disabled={!activeConcern || busy}>{busy ? 'Starting…' : 'Begin assessment'}<ArrowRight size={17}/></button>
    </form>
  </div>;
}

function AssessmentPage() {
  const {id} = useParams();
  const navigate = useNavigate();
  const state = useQuery({queryKey:['assessment',id], queryFn:()=>api<S['Progress']>(`/assessments/${id}/question`)});
  const question = state.data?.question;
  const guide = useQuery({queryKey:['guide',question?.guide_id], queryFn:()=>api<S['Guide']>('/measurements/guides/'+question?.guide_id),enabled:!!question?.guide_id});
  const [value,setValue] = useState(''), [error,setError] = useState<unknown>(null), [busy,setBusy] = useState(false);
  useEffect(()=>{setValue('');setError(null);},[question?.id]);
  useEffect(()=>{
    if (state.data?.session.status === 'escalated') navigate('/emergency?assessment='+id,{replace:true});
    if (state.data?.session.status === 'completed') navigate('/results/'+id,{replace:true});
  },[id,navigate,state.data?.session.status]);
  async function send(e: FormEvent, skip = false) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);setError(null);
    try {
      if (!question) {
        await api<S['Result']>(`/assessments/${id}/complete`,{});
        await queryClient.invalidateQueries({queryKey:['history']});
        navigate('/results/'+id);
      } else {
        const payload = skip || value === '' ? null : question.type === 'number' ? Number(value) : value;
        const data = await api<S['Progress']>(`/assessments/${id}/answers`,{question_id:question.id,value:payload} satisfies S['Submission']);
        queryClient.setQueryData(['assessment',id], data);
        if(data.session.status === 'escalated') {
          void queryClient.invalidateQueries({queryKey:['history']});
          navigate('/emergency?assessment='+id,{replace:true});
        }
      }
    } catch(err) {setError(err);} finally {setBusy(false);}
  }
  if (state.error) return <div className="subpage"><ErrorNote error={state.error}/></div>;
  if (!state.data) return <p className="muted">Loading assessment…</p>;
  const {session,answered,total} = state.data;
  return <div className="subpage">
    <Link className="text-link" to="/assess"><ArrowLeft size={15}/> Assessments</Link>
    <PageTitle label={`${session.astronaut_id} · MISSION DAY ${session.mission_day}`} title={session.concern}/>
    <form className="surface form-card question-card" onSubmit={e=>void send(e)}>
      <div className="question-progress"><span>{question ? `Question ${answered+1} of ${total}` : 'Ready to complete'}</span><progress value={answered} max={total}/></div>
      <h2 id="question-title">{question?.prompt || 'Review your results'}</h2>
      {question?.description && <p>{question.description}</p>}
      {question?.type === 'choice' && <fieldset className="choice-list" aria-labelledby="question-title">{question.options?.map(option=>
        <label key={option} className={option===value?'checked':''}><input type="radio" name="answer" value={option} checked={option===value} onChange={()=>setValue(option)}/>{option}</label>)}</fieldset>}
      {question?.type === 'number' && <label className="measurement-input"><span>Reading in {question.unit}</span><input aria-labelledby="question-title" type="number" inputMode="decimal" step="any" min={question.minimum ?? undefined} max={question.maximum ?? undefined} value={value} onChange={e=>setValue(e.target.value)}/></label>}
      {question?.type === 'text' && <textarea aria-labelledby="question-title" rows={4} maxLength={500} value={value} onChange={e=>setValue(e.target.value)}/>}
      {guide.data && <details className="guide"><summary><CircleHelp size={16}/> How to measure</summary><p>{guide.data.instructions}</p><p>{guide.data.equipment}</p><p>{guide.data.limitations}</p><a href={guide.data.source} target="_blank" rel="noreferrer">Source <ArrowUpRight size={14}/></a></details>}
      <ErrorNote error={error || guide.error}/>
      <div className="actions">
        <button className="button primary" disabled={busy || Boolean(question && !question.optional && !value)}>{busy?'Saving…':question?'Continue':'View results'}<ArrowRight size={16}/></button>
        {question?.optional && <button className="button secondary" type="button" disabled={busy} onClick={e=>void send(e,true)}>Skip</button>}
        <Link className="text-link save-exit" to="/history" onClick={()=>void queryClient.invalidateQueries({queryKey:['history']})}>Save & exit</Link>
      </div>
    </form>
  </div>;
}

function ResultPage() {
  const {id} = useParams();
  const result = useQuery({queryKey:['result',id],queryFn:()=>api<S['Result']>(`/assessments/${id}/results`)});
  if (result.error) return <ErrorNote error={result.error}/>;
  if (!result.data) return <p className="muted">Loading results…</p>;
  const r = result.data, ml = r.ml;
  if (r.urgent) return <div className="subpage"><PageTitle label="ASSESSMENT ESCALATED" title={readable(r.session.concern)}/><Link className="button emergency-button" to="/emergency">Open Emergency Assistance <ArrowRight size={16}/></Link></div>;
  return <div className="subpage wide">
    <Link className="text-link" to="/history"><ArrowLeft size={15}/> Health history</Link>
    <PageTitle label={`${r.session.astronaut_id} · MISSION DAY ${r.session.mission_day}`} title={readable(r.session.concern)}>{r.imported ? 'Imported synthetic assessment' : 'Assessment results'}</PageTitle>
    <div className="results-grid">
      <section className="surface result-card"><h2><ClipboardCheck size={19}/> Assessment summary</h2>
        {r.symptom_onset && <p>Onset · {readable(r.symptom_onset)}</p>}
        {Object.entries(r.measurements || {}).map(([key,value])=><div className="reading-row" key={key}><span>{names(key)[0]}</span><strong>{format(value)} {names(key)[1]}</strong></div>)}
        {!Object.keys(r.measurements || {}).length && <p>No readings were entered.</p>}
      </section>
      <section className="surface result-card"><h2><Sparkles size={19}/> Personal comparison</h2>
        {ml?.baseline_status === 'ready' ? <>
          <p className={ml.anomaly_flag ? 'flag' : 'plain-status'}>{ml.anomaly_flag ? 'Unusual pattern flagged' : 'No unusual pattern flagged'}</p>
          {ml.top_deviating_indicators.map(key=><div key={key} className="comparison"><strong>{names(key)[0]}</strong><p>{format(ml.current_values[key])} {names(key)[1]} entered · {format(ml.baseline_values[key])} {names(key)[1]} baseline</p></div>)}
          <p className="muted">Model {ml.model_version} · Score {format(ml.anomaly_score)} · Statistical comparison</p>
        </> : <p>{ml?.baseline_status === 'baseline_not_ready' ? 'Personal baseline is not ready.' : 'No compatible model comparison available.'}</p>}
        {ml?.limitations.map(l=><p className="muted" key={l}>{l}</p>)}
      </section>
      {r.guidance && <section className="surface result-card"><h2><ShieldPlus size={19}/> Next steps</h2><h3>{r.guidance.title}</h3><ul>{r.guidance.steps.map(step=><li key={step}>{step}</li>)}</ul>{r.guidance.sources.map(url=><a key={url} href={url} target="_blank" rel="noreferrer">Guidance reference <ArrowUpRight size={14}/></a>)}</section>}
      <section className="surface result-card"><h2><BookOpen size={19}/> NASA scientific context</h2>{r.evidence?.length ? r.evidence.map(source=><EvidenceCard key={source.source_id} source={source}/>) : <p>No retrieved evidence for this record.</p>}</section>
    </div>
    {!!r.limitations?.length && <section className="surface result-card limitations"><h2>Assessment limitations</h2><ul>{r.limitations.map(item=><li key={item}>{item}</li>)}</ul></section>}
  </div>;
}

function HistoryPage({ctx}:{ctx:CrewContext}) {
  const history = useHistory(ctx.crew,ctx.day);
  const [range,setRange] = useState(30), [indicator,setIndicator] = useState('resting_hr_bpm');
  const points = (history.data?.records || []).filter(p=>p.mission_day>ctx.day-range).map(p=>({day:p.mission_day,value:p.readings[indicator]??null}));
  const assessments = history.data?.assessments || [];
  return <div className="subpage wide">
    <PageTitle label={`${ctx.crew} · THROUGH MISSION DAY ${ctx.day}`} title="Health history">Review mission readings and saved assessments.</PageTitle>
    <ErrorNote error={history.error}/>
    <section className="surface result-card">
      <div className="chart-header"><h2>{names(indicator)[0]} <small>({names(indicator)[1]})</small></h2>
        <label><span className="sr-only">Indicator</span><select value={indicator} onChange={e=>setIndicator(e.target.value)}>{Object.keys(readings).map(key=><option key={key} value={key}>{names(key)[0]}</option>)}</select></label>
        <label><span className="sr-only">Time range</span><select value={range} onChange={e=>setRange(Number(e.target.value))}>{[7,14,30,60,3000].map(n=><option key={n} value={n}>{n===3000?'All days':`Last ${n} days`}</option>)}</select></label>
      </div>
      {points.some(p=>p.value!==null) ? <div className="chart"><ResponsiveContainer width="100%" height={250}><LineChart data={points} margin={{top:15,right:22,left:0,bottom:10}}>
        <CartesianGrid vertical={false} stroke="#e9e7f2"/><XAxis dataKey="day" tickFormatter={day=>'D'+day}/><YAxis domain={['auto','auto']} width={48}/>
        <Tooltip labelFormatter={day=>'Mission Day '+day} formatter={value=>[format(Number(value))+' '+names(indicator)[1],names(indicator)[0]]}/>
        <Line type="linear" dataKey="value" stroke="#7466bb" strokeWidth={2.4} connectNulls={false} dot={points.length<15} isAnimationActive={false}/></LineChart></ResponsiveContainer></div> : <p>{history.isPending?'Loading records…':'No readings in this range.'}</p>}
    </section>
    <section className="surface result-card history-list"><h2>Assessment log</h2>{assessments.map(s=><Link key={s.assessment_id} to={(s.status==='in_progress'?'/assess/':'/results/')+s.assessment_id}>
      <div><strong>{readable(s.concern)}</strong><small>Day {s.mission_day} · {s.origin==='synthetic_demo'?'Imported demo':'Entered in SALUS'}</small></div><span>{readable(s.status)} <ChevronRight size={16}/></span>
    </Link>)}{!assessments.length && !history.isPending && <p>No assessments on record.</p>}</section>
  </div>;
}

function Knowledge() {
  const {search} = useLocation(), topic = new URLSearchParams(search).get('topic') || '';
  const [input,setInput] = useState(topic), [query,setQuery] = useState(topic);
  const sources = useQuery({queryKey:['evidence',query], queryFn:()=>query?api<S['Evidence'][]>('/evidence/search',{query,limit:6} satisfies S['Search']):api<S['Evidence'][]>('/evidence/sources')});
  const guides = useQuery({queryKey:['guides'],queryFn:()=>api<S['Guide'][]>('/measurements/guides')});
  return <div className="subpage wide"><PageTitle label="REFERENCE LIBRARY" title="NASA Knowledge">Explore spaceflight research and measurement guides.</PageTitle>
    <form className="search-form" onSubmit={e=>{e.preventDefault();setQuery(input.trim());}}><Search size={19}/><input aria-label="Search NASA evidence" placeholder="Search fatigue, circulation, gravity…" maxLength={300} value={input} onChange={e=>setInput(e.target.value)}/><button className="button primary">Search</button></form>
    <ErrorNote error={sources.error || guides.error}/>
    {!sources.isPending && !sources.data?.length && !sources.error && <p>No matching NASA evidence found.</p>}
    <div className="evidence-grid">{sources.data?.map(source=><EvidenceCard key={source.source_id} source={source}/>)}</div>
    <h2 className="section-heading">Measurement guides</h2>
    {guides.data?.map(guide=><details className="guide surface" key={guide.indicator}><summary>{guide.title} <small>{guide.unit}</small></summary><p>{guide.why}</p><p>{guide.equipment}</p><p>{guide.instructions}</p><p>{guide.common_mistakes}</p><p>{guide.limitations}</p><a href={guide.source} target="_blank" rel="noreferrer">Source <ArrowUpRight size={14}/></a></details>)}
  </div>;
}

function Emergency() {
  const {search} = useLocation(), id = new URLSearchParams(search).get('assessment');
  const emergency = useQuery({queryKey:['emergency'],queryFn:()=>api<S['Guidance']>('/emergency-support')});
  return <div className="subpage emergency-page"><PageTitle label={id?'URGENT WARNING SIGN REPORTED':'CREW MEDICAL SUPPORT'} title="Emergency Assistance">{id?'The routine assessment was interrupted.':'Immediate access to the crew escalation pathway.'}</PageTitle>
    <section className="surface result-card emergency-card"><Siren size={28}/><h2>{emergency.data?.title || 'Alert the designated crew medical responder now'}</h2>
      {emergency.data ? <ol>{emergency.data.steps.map(step=><li key={step}>{step}</li>)}</ol> : <p>Use your mission’s approved emergency response procedures.</p>}
      {!emergency.data?.procedure_available && <p className="muted">Verified onboard procedures are unavailable in this prototype.</p>}
      {emergency.data?.sources.map(url=><a key={url} href={url} target="_blank" rel="noreferrer">{new URL(url).hostname.replace('www.','')} <ArrowUpRight size={14}/></a>)}
      <ErrorNote error={emergency.error}/>
    </section>
  </div>;
}

function Shell() {
  const [crew,setCrew] = useState('AST-02'), [day,setDay] = useState(45), [settings,setSettings] = useState(false);
  const location = useLocation();
  const profiles = useQuery({queryKey:['crew'],queryFn:()=>api<S['Crew'][]>('/astronauts')});
  const person = profiles.data?.find(p=>p.astronaut_id===crew);
  const ctx={crew,day,setCrew,setDay};
  useEffect(()=>{window.scrollTo({top:0});},[location.pathname]);
  return <div className="app">
    <header className="topbar">
      <Link className="brand" to="/"><img src="/salus-logo.webp" alt=""/><span><strong>SALUS</strong><small>Astronaut health</small></span></Link>
      <nav aria-label="Main navigation">{nav.map(([url,label,Icon])=><NavLink key={url} to={url} end={url==='/'}><Icon size={16}/><span>{label}</span></NavLink>)}</nav>
      <div className="top-actions"><NavLink className="emergency-button" to="/emergency"><Siren size={17}/><span>Emergency</span></NavLink>
        <button className="crew-button" type="button" aria-label="Mission settings" aria-expanded={settings} onClick={()=>setSettings(!settings)}><span className="crew-avatar">{crew.slice(-2)}</span><span className="crew-label"><strong>{crew}</strong><small>{person?.mission_role || 'Crew member'}</small></span><ChevronDown size={15}/></button>
      </div>
      {settings && <div className="settings surface"><div><h2>Mission settings</h2><button className="icon-button" type="button" aria-label="Close mission settings" onClick={()=>setSettings(false)}><X size={18}/></button></div>
        <label>Crew member<select value={crew} onChange={e=>setCrew(e.target.value)}>{profiles.data?.map(p=><option key={p.astronaut_id} value={p.astronaut_id}>{p.astronaut_id} · {p.mission_role}</option>)}</select></label>
        <label>Mission day<input type="number" min="1" max="3000" key={crew} defaultValue={day} onBlur={e=>{const value=Number(e.target.value);setDay(Number.isInteger(value)&&value>=1&&value<=3000?value:day);e.target.value=String(Number.isInteger(value)&&value>=1&&value<=3000?value:day);}} onKeyDown={e=>{if(e.key==='Enter')e.currentTarget.blur();}}/></label>
        <ErrorNote error={profiles.error}/>
        <button className="button primary" onClick={()=>setSettings(false)}>Done</button>
      </div>}
    </header>
    <main id="main"><Routes>
      <Route path="/" element={<Explore ctx={ctx}/>}/>
      <Route path="/assess" element={<StartAssessment key={location.search} ctx={ctx}/>}/>
      <Route path="/assess/:id" element={<AssessmentPage/>}/>
      <Route path="/results/:id" element={<ResultPage/>}/>
      <Route path="/history" element={<HistoryPage ctx={ctx}/>}/>
      <Route path="/knowledge" element={<Knowledge key={location.search}/>}/>
      <Route path="/emergency" element={<Emergency/>}/>
      <Route path="*" element={<div className="subpage"><PageTitle label="SALUS" title="Page unavailable"/><Link to="/">Return to Explore</Link></div>}/>
    </Routes></main>
    <footer className="footer"><span><i/> Synthetic mission data</span><span>NASA Space Apps Challenge · Research prototype</span></footer>
  </div>;
}

createRoot(document.getElementById('root')!).render(<QueryClientProvider client={queryClient}><HashRouter><Shell/></HashRouter></QueryClientProvider>);
