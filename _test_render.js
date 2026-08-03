const fs = require('fs');
const vm = require('vm');

const html = fs.readFileSync('mrlovewords9272_catalog_standalone.html', 'utf-8');
// 提取所有内联 <script>：仅跳过“标签带 src 属性”的外部脚本；不要因内容含 src= 误杀
const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let m, parts = [];
while ((m = re.exec(html))) {
  if (/\bsrc=/.test(m[1] || '')) continue;   // 仅标签属性带 src 才跳过
  parts.push(m[2]);
}
console.log('inline script blocks:', parts.length);

// DOM 桩
function mkEl(id) {
  return {
    id, innerHTML: '', textContent: '', value: '', dataset: {}, style: {},
    classList: { toggle(){}, add(){}, remove(){}, contains(){return false;} },
    addEventListener(){}, appendChild(){}, focus(){},
    querySelectorAll(){ return []; }, querySelector(){ return null; },
    closest(){ return null; }, scrollIntoView(){},
  };
}
const els = {};
const location = { hash: '' };
const document = {
  getElementById(id){ return els[id] || (els[id] = mkEl(id)); },
  querySelectorAll(){ return []; },
  querySelector(){ return null; },
  documentElement: { style: { setProperty(){}, getPropertyValue(){ return ''; } } },
  body: { classList: { toggle(){}, add(){}, remove(){} } },
  addEventListener(){},
};
const localStorage = { _d:{}, getItem(k){ return this._d[k]||null; }, setItem(k,v){ this._d[k]=v; }, removeItem(k){ delete this._d[k]; } };
const window = { __CAT__: [], addEventListener(){}, scrollTo(){} };
const sandbox = {
  window, document, localStorage, location,
  matchMedia(){ return { matches: false }; },
  confirm(){ return false; }, console,
  encodeURIComponent, decodeURIComponent,
  Object, Array, JSON, Math, parseInt, isNaN, Set, Map, Date, String, Number, RegExp,
};
vm.createContext(sandbox);
// 逐段运行到同一 sandbox（函数声明会挂到 context 全局，闭包仍可捕获 const DATA）
for (const p of parts) { vm.runInContext(p, sandbox, { timeout: 30000 }); }

let failures = 0;
function assert(cond, msg){ if(cond){ console.log('  ✓', msg); } else { console.log('  ✗ FAIL:', msg); failures++; } }

console.log('[1] 初始网格渲染');
const grid0 = els['gridView'].innerHTML || '';
assert(grid0.length > 1000, 'gridView 有内容 (len=' + grid0.length + ')');
assert(grid0.includes('class="gcard"'), '包含封面卡片 .gcard');
assert(grid0.includes('共 <b>'), '包含篇数统计');
assert((els['stats'].innerHTML||'').includes('结构化增强'), 'stats 进度条已填充');
vm.runInContext('renderDash()', sandbox);   // 总览面板按需渲染
const dashG = els['dashGenres'].innerHTML || '';
assert(dashG.length > 0 && dashG.includes('古风'), '数据总览·题材已生成(含古风)');
assert((els['dashHier'].innerHTML||'').includes('全库身份格局'), '身份格局汇总已生成');

console.log('[2] 打开详情视图（首篇）');
vm.runInContext('openDetail(DATA[0].id)', sandbox);
const det = els['detailView'].innerHTML || '';
assert(det.length > 500, 'detailView 有内容 (len=' + det.length + ')');
assert(det.includes('dtitle'), '详情含标题 .dtitle');
assert(det.includes('transcript'), '详情含台词区 .transcript');
assert(det.includes('返回总册'), '详情含返回按钮');
const spkCount = (det.match(/class="spk line-speaker"/g) || []).length;
const paraCount = (det.match(/class="dpara"/g) || []).length;
assert(paraCount > 0, '分段台词已生成 ('+paraCount+' 段)');
assert(spkCount <= paraCount, '说话人药丸数('+spkCount+') <= 段落数('+paraCount+')');

console.log('[3] 题材筛选（古风）');
vm.runInContext('state.filters.genre="古风"; state.page=1; renderGrid();', sandbox);
const gridG = els['gridView'].innerHTML || '';
assert((gridG.match(/class="gcard"/g) || []).length > 0, '古风筛选后仍有卡片');
assert(gridG.includes('古风'), '筛选结果含古风标签');

console.log('[4] 搜索（哥哥）');
vm.runInContext('state.filters.genre=null; state.kw="哥哥"; state.page=1; renderGrid();', sandbox);
assert((els['gridView'].innerHTML||'').length > 0, '搜索“哥哥”有结果');

console.log('[5] 回到全量网格');
vm.runInContext('state.kw=""; state.page=1; renderGrid();', sandbox);
const gridAll = els['gridView'].innerHTML || '';
const allCards = (gridAll.match(/class="gcard"/g) || []).length;
assert(allCards > 20, '全量网格卡片数正常 (' + allCards + ')');

console.log('[6] 剧本体 story 渲染（留痕）');
vm.runInContext('state.view="detail"; state.selectedId="03RP8-i8sXI"; renderDetail(DATA.find(r=>r.id==="03RP8-i8sXI"));', sandbox);
const dvS = els['detailView'].innerHTML || '';
assert(dvS.includes('class="story"'), 'story 容器存在');
assert(dvS.includes('class="sn"'), '叙述段 .sn 存在');
assert(dvS.includes('class="sl"'), '台词段 .sl 存在');
assert(dvS.includes('主人：'), '彩色说话人标签“主人：”存在');
assert(dvS.includes('剧本体'), '分节标题标注剧本体');

console.log('[7] 无 story 篇目回退（A puppy kept in a hotel / 精校层）');
vm.runInContext('state.selectedId="y1LPRK97wMI"; renderDetail(DATA.find(r=>r.id==="y1LPRK97wMI"));', sandbox);
const dvB = els['detailView'].innerHTML || '';
assert(dvB.includes('class="dpara"'), '回退到分段台词 .dpara');
assert(!dvB.includes('class="story"'), '无 story 容器');

console.log(failures === 0 ? '\nALL PASS ✅' : '\n'+failures+' 项失败 ❌');
if (failures > 0) process.exit(1);
