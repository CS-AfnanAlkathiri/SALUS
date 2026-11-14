import { ScanLine, Crosshair } from 'lucide-react';

const outline = 'M160 20 C141 20 133 33 133 52 L133 65 C127 62 129 76 136 81 Q140 92 147 97 L147 111 Q132 122 108 126 C86 127 76 144 72 165 L62 222 Q59 243 47 267 L30 310 L19 326 L11 351 Q11 356 16 353 L26 337 L22 359 Q23 365 28 359 L37 341 L34 358 Q36 363 40 357 L48 338 Q53 330 50 318 L72 278 Q88 252 95 230 L108 184 Q114 215 117 234 Q119 252 110 278 C100 308 100 331 104 360 L113 423 Q117 449 112 481 L113 542 L106 566 Q103 578 116 580 L131 580 Q137 578 136 568 L137 546 L146 478 Q153 450 148 427 L153 369 Q156 335 160 326 Q164 335 167 369 L172 427 Q167 450 174 478 L183 546 L184 568 Q183 578 189 580 L204 580 Q217 578 214 566 L207 542 L208 481 Q203 449 207 423 L216 360 C220 331 220 308 210 278 Q201 252 203 234 Q206 215 212 184 L225 230 Q232 252 248 278 L270 318 Q267 330 272 338 L280 357 Q284 363 286 358 L283 341 L292 359 Q297 365 298 359 L294 337 L304 353 Q309 356 309 351 L301 326 L290 310 L273 267 Q261 243 258 222 L248 165 C244 144 234 127 212 126 Q188 122 173 111 L173 97 Q180 92 184 81 C191 76 193 62 187 65 L187 52 C187 33 179 20 160 20 Z';
const muscles = [
  'M149 111Q139 132 112 141Q123 164 153 160L157 132Z',
  'M108 131Q80 138 77 168Q86 186 103 167L114 148Z',
  'M101 174Q81 184 72 224Q79 235 89 218Z',
  'M69 234Q58 268 43 305Q49 302 61 283Q81 253 83 232Z',
  'M110 166Q125 179 154 171L153 195Q128 194 113 180Z',
  'M117 187Q130 200 153 200L153 214Q131 213 119 204Z',
  'M120 209Q135 219 153 219L153 233Q130 232 123 225Z',
  'M124 233Q135 241 153 239L153 256Q137 253 124 246Z',
  'M121 254Q126 273 151 294Q142 268 121 254Z',
  'M112 280Q103 313 109 339L124 416Q136 401 128 373Q115 320 130 300Z',
  'M135 303Q128 333 134 371L141 406Q150 371 150 345Q147 318 135 303Z',
  'M118 441Q123 424 132 440Q133 473 121 523Q116 500 118 478Z',
  'M137 450Q145 454 141 477L131 538L125 543Z',
];
const markers = [
  { id: 'head_brain', label: 'Head & brain', x: 160, y: 49, side: 'right' },
  { id: 'chest_heart', label: 'Cardiovascular', x: 174, y: 166, side: 'right' },
  { id: 'abdomen', label: 'Abdomen', x: 151, y: 245, side: 'left' },
  { id: 'musculoskeletal', label: 'Musculoskeletal', x: 125, y: 422, side: 'left' },
  { id: 'general_health', label: 'General health', x: 202, y: 365, side: 'right' },
];

export function Anatomy({ selected, select }: { selected: string; select: (id: string) => void }) {
  return <div className="anatomy-panel">
    <div className="anatomy-header"><div><div className="eyebrow"><ScanLine size={15}/> Anatomy explorer</div><p>Select a region to explore</p></div><Crosshair size={19} aria-hidden="true"/></div>
    <div className="anatomy-stage">
      <div className="scan-ring ring-one"/><div className="scan-ring ring-two"/><div className="scan-ring ring-three"/>
      <svg className="figure" viewBox="0 0 320 603" aria-hidden="true">
        <defs>
          <linearGradient id="skin"><stop stopColor="#8095b9" stopOpacity=".8"/><stop offset=".26" stopColor="#ccd9ed" stopOpacity=".85"/><stop offset=".5" stopColor="#eff6ff" stopOpacity=".8"/><stop offset=".76" stopColor="#b1c2df" stopOpacity=".9"/><stop offset="1" stopColor="#798db7" stopOpacity=".85"/></linearGradient>
          <linearGradient id="muscle" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#e5f0fb"/><stop offset=".55" stopColor="#8d9fc6"/><stop offset="1" stopColor="#647ead"/></linearGradient>
          <radialGradient id="joint"><stop stopColor="#f9fdff"/><stop offset="1" stopColor="#879bc0"/></radialGradient>
          <radialGradient id="organ"><stop stopColor="#faf3ff"/><stop offset="1" stopColor="#aa90c5"/></radialGradient>
          <clipPath id="outlineClip"><path d={outline}/></clipPath>
        </defs>
        <ellipse cx="160" cy="585" rx="89" ry="11" fill="#8f9bc6" opacity=".22"/>
        <path d={outline} fill="url(#skin)" stroke="#8a9dbe" strokeWidth="1.4"/>
        <g clipPath="url(#outlineClip)">
          <g opacity=".62" fill="url(#muscle)" stroke="#eef5ff" strokeWidth="1.1">
            {muscles.map(d => <path key={d} d={d}/>)}<g transform="translate(320) scale(-1 1)">{muscles.map(d => <path key={d} d={d}/>)}</g>
          </g>
          <g fill="none" stroke="#f3f8ff" strokeOpacity=".85" strokeWidth="2">
            <path d="M160 104V301 M146 126 Q121 124 100 142 M174 126Q199 124 220 142 M145 279 Q113 267 115 290 Q123 313 154 312 M175 279 Q207 267 205 290 Q197 313 166 312"/>
            {[0,1,2,3,4,5].map(i => <path key={i} d={`M159 ${149+i*11}Q139 ${136+i*10} 117 ${146+i*10}Q128 ${166+i*10} 157 ${169+i*11} M161 ${149+i*11}Q181 ${136+i*10} 203 ${146+i*10}Q192 ${166+i*10} 163 ${169+i*11}`}/>)}
            <path d="M95 161L76 230L45 316 M225 161L244 230L275 316 M135 312L129 429L124 547 M185 312L191 429L196 547"/>
          </g>
          <g opacity=".82" fill="url(#joint)">{[[95,152],[225,152],[75,232],[245,232],[129,426],[191,426],[124,545],[196,545]].map(([x,y]) => <ellipse key={x} cx={x} cy={y} rx="8" ry="10"/>)}</g>
          <path d="M144 36Q153 27 160 32Q168 27 177 37Q183 44 178 56Q171 66 160 61Q147 67 140 56Q136 47 144 36Z" fill="url(#organ)" opacity={selected === 'head_brain' ? '.95' : '.63'} stroke="#dcd1ee"/>
          <path d="M160 33V61M144 44q7-7 12 1m-12 8q7 3 10-3m12-4q6-9 12-3m-12 7q6 7 12 1" fill="none" stroke="#8b76ae" strokeWidth="1"/>
          <path d="M149 144Q124 148 123 184Q128 203 148 196Q156 174 149 144Z M171 144Q196 148 197 184Q192 203 172 196Q164 174 171 144Z" fill="url(#organ)" opacity=".43"/>
          <path d="M162 161Q170 150 181 159Q198 172 177 195Q159 187 154 174Q151 163 162 161Z" fill="#b585b8" opacity={selected === 'chest_heart' ? '.9' : '.56'} stroke="#f5d9f5"/>
          <path d="M133 227Q149 217 166 224Q164 235 147 240Q135 242 133 227Z M166 232Q189 224 189 247Q183 260 171 258Q157 255 166 232Z" fill="url(#organ)" opacity={selected === 'abdomen' ? '.9' : '.48'}/>
          <g fill="none" stroke="#7e90c1" strokeWidth="1.3" opacity=".72">
            <path d="M160 69L160 153L169 163L161 180L161 274L135 312L127 429L124 551 M161 274L185 312L193 429L197 551 M158 137L104 150L76 231L42 320 M166 137L216 150L244 231L278 320"/>
            <path d="M141 64l10 2m18 0 10-2m-19 5-3 10 6 1m-11 8q8 4 16 0"/>
          </g>
        </g>
      </svg>
      <div className="markers">
        {markers.map(marker => <button key={marker.id} type="button" aria-pressed={selected === marker.id} aria-label={marker.label}
          className={`marker ${marker.side} ${selected === marker.id ? 'active' : ''}`}
          style={{ left: `${marker.x/3.2}%`, top: `${marker.y/6.03}%` }} onClick={() => select(marker.id)}>
          <span className="marker-dot"/><span className="marker-label">{marker.label}</span>
        </button>)}
      </div>
    </div>
    <div className="anatomy-footer"><span><i/> Selectable region</span><span>Anterior view</span></div>
  </div>;
}
