// Test generated report logic without external JS libraries or a live browser.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../outputs/employment/occupazione.html'),'utf8');
const payload=html.match(/<script id="payload" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
const values={observedMetric:'employment_rate',stanfordMetric:'exposure',region:'0',scenario:'reference',metric:'levels',view:'levels'};
const elements=new Map();
const document={getElementById(id){if(!elements.has(id))elements.set(id,{value:values[id]||'',textContent:id==='payload'?payload:'',innerHTML:'',append(){},addEventListener(){}});return elements.get(id);},createElement(){return {};}};
const context=vm.createContext({document,console});
vm.runInContext(code,context);
function count(id,n){assert.equal((elements.get(id).innerHTML.match(/<svg /g)||[]).length,n,id);assert.ok(!/NaN|Infinity/.test(elements.get(id).innerHTML),id);}
for(const metric of ['employment_rate','unemployment_rate','participation_rate']){
 elements.get('observedMetric').value=metric;vm.runInContext('observed()',context);count('observedCharts',4);
}
for(const metric of ['exposure','canaries_software_developers','canaries_customer_service']){
 elements.get('stanfordMetric').value=metric;vm.runInContext('stanford()',context);count('stanfordCharts',6);
}
let n=0;
for(const region of ['0','1','2'])for(const scenario of ['reference','effective','slow','persistent'])
for(const metric of ['levels','employment_rate','unemployment_rate','hire_rate','first_hire_rate','rehire_rate','gap_potential','broad_nonemployment','participation_rate'])
for(const view of ['levels','difference']){
 for(const [k,v]of Object.entries({region,scenario,metric,view}))elements.get(k).value=v;
 vm.runInContext('simulation()',context);count('simulationCharts',4);n++;
}
console.log(`Report rendering logic: ${n} simulation selections and 6 observed selections passed.`);
