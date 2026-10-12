"""Vector PDF appendix, generated offline from verified observed and model data."""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/"outputs"/"employment"
COLORS=["#1463a0","#14947e","#ca6b23","#774aa1"]


def paragraph(c,text,x,y,width,size=10,leading=15):
    c.setFont("Helvetica",size);c.setFillColor(HexColor("#243b4b"))
    for line in simpleSplit(text,"Helvetica",size,width):
        c.drawString(x,y,line);y-=leading
    return y-10


def plot(c,x,y,w,h,xs,series,title,unit,limits=None):
    c.setFillColor(HexColor("#172b3a"));c.setFont("Helvetica-Bold",11);c.drawString(x,y+h-12,title)
    c.setFont("Helvetica",7.5);c.setFillColor(HexColor("#526778"));c.drawString(x,y+h-26,unit)
    vals=[v for s in series for v in s["y"]]
    lo,hi=limits or (min(vals+[0]),max(vals+[0]));span=hi-lo or 1;lo-=span*.06;hi+=span*.06
    px,py=x+35,y+30;pw,ph=w-44,h-75
    X=lambda i:px+i*pw/max(1,len(xs)-1)
    Y=lambda v:py+(v-lo)*ph/(hi-lo)
    for i in range(5):
        v=lo+(hi-lo)*i/4; yy=Y(v)
        c.setStrokeColor(HexColor("#e3e9ed"));c.setLineWidth(.5);c.line(px,yy,px+pw,yy)
        c.setFillColor(HexColor("#526778"));c.setFont("Helvetica",7);c.drawRightString(px-5,yy-2,f"{v:.1f}")
    if lo<=0<=hi:
        c.setStrokeColor(HexColor("#9aaab6"));c.setDash(2,2);c.line(px,Y(0),px+pw,Y(0));c.setDash()
    if "Indice" in unit and lo<=100<=hi:
        c.setStrokeColor(HexColor("#9aaab6"));c.setDash(2,2);c.line(px,Y(100),px+pw,Y(100));c.setDash()
    for s in series:
        c.setStrokeColor(HexColor(s["color"]));c.setLineWidth(1.6)
        if s.get("dash"):c.setDash(4,3)
        p=c.beginPath();p.moveTo(X(0),Y(s["y"][0]))
        for i,v in enumerate(s["y"][1:],1):p.lineTo(X(i),Y(v))
        c.drawPath(p);c.setDash()
    ticks=sorted(set([0,len(xs)//3,2*len(xs)//3,len(xs)-1]))
    c.setFont("Helvetica",7);c.setFillColor(HexColor("#526778"))
    for i in ticks:c.drawCentredString(X(i),py-13,str(xs[i])[:7])


def main():
    S=json.loads((FOLDER/"results.json").read_text(encoding="utf-8"))
    O=json.loads((ROOT/"data/observed/observed_summary.json").read_text(encoding="utf-8"))
    dest=FOLDER/"sezione_occupazione.pdf"
    c=canvas.Canvas(str(dest),pagesize=A4);W,H=A4;page=0
    c.setTitle("Occupazione, eta e AI - appendice esplorativa")
    def header(title,subtitle):
        nonlocal page
        page+=1;c.setFillColor(HexColor("#1463a0"));c.setFont("Helvetica-Bold",10);c.drawString(36,H-35,"OCCUPAZIONE, ETA E AI")
        c.setFillColor(HexColor("#172b3a"));c.setFont("Helvetica-Bold",19);c.drawString(36,H-67,title)
        paragraph(c,subtitle,36,H-89,W-72,9,13)
    def footer():
        c.setFillColor(HexColor("#526778"));c.setFont("Helvetica",8)
        c.drawString(36,27,"v3 - Dati osservati e simulazioni condizionate; nessuna previsione causale")
        c.drawRightString(W-36,27,str(page));c.showPage()
    def panels(xs,items,unit,limits=None):
        w=(W-84)/2
        for i,(title,series) in enumerate(items):
            plot(c,36+(i%2)*(w+12),H-400-(i//2)*260,w,235,xs,series,title,unit,limits)
    def legends(items):
        yy=H-145
        for i,(label,color) in enumerate(items):
            x=36+(i%2)*265;y=yy-(i//2)*15
            c.setStrokeColor(HexColor(color));c.setLineWidth(2);c.line(x,y,x+18,y)
            c.setFillColor(HexColor("#243b4b"));c.setFont("Helvetica",8);c.drawString(x+24,y-3,label)
    header("Una sezione occupazionale per eta","Fonti consultate e dati scaricati il 10 ottobre 2026. Appendice autonoma al documento originale.")
    yy=H-140
    blocks=[
      ("Che cosa misura", "Quattro fasce nelle simulazioni: 15-24, 25-34, 35-49 e 50-64. Le coorti avanzano di un anno; il modello distingue occupati, primo ingresso, ricollocamento e scoraggiamento. I grafici Stanford conservano le fasce della fonte, diverse da quelle del modello."),
      ("Dati osservati", "Eurostat LFS: Italia e UE-27, 2019-2025, popolazione, occupati, forza lavoro e disoccupati. Stanford/ADP: serie mensili per eta ed esposizione, fino ad agosto 2026, vintage settembre 2026. I dati originali e gli hash sono archiviati nel progetto."),
      ("Calibrazione parziale", "Il profilo iniziale ADV usa quote di popolazione e partecipazione dell'UE come proxy; la forma della disoccupazione per eta e normalizzata al tasso strutturale ADV del modello originale. L'UE non rappresenta tutte le economie avanzate. Le fasce EME/LIC e i parametri AI e di matching restano assunzioni."),
      ("Come funziona", "La domanda aggregata arriva dal modello macroeconomico e viene allocata per eta tramite pesi di accessibilita espliciti. I posti disponibili non vengono coperti automaticamente: probabilita di assunzione e ricollocamento limitano gli ingressi. Gli scoraggiati escono dall'offerta attiva, ma rimangono nell'offerta potenziale."),
      ("Limite decisivo", "Il modulo per eta e collegato in una sola direzione. Le sue nuove traiettorie occupazionali non modificano ancora PIL, salari, redditi o debito. Non usare quindi i risultati fiscali originari come valutazione delle nuove simulazioni occupazionali."),
      ("Interpretazione", f"{S['draws']} estrazioni appaiate per scenario, seed {S['seed']}. Gli scenari non hanno probabilita empiriche. Le pagine statiche mostrano mediane; il rapporto HTML include bande 5-95. Sono dispersioni delle ipotesi, non intervalli di confidenza. Nessuna stima del danno causale AI e ricavata dai soli indici osservati.")]
    for title,text in blocks:
        c.setFont("Helvetica-Bold",11);c.setFillColor(HexColor("#172b3a"));c.drawString(36,yy,title);yy-=18
        yy=paragraph(c,text,36,yy,W-72,9.5,14)
    footer()
    for key,title in [("employment_rate","Occupazione osservata"),("unemployment_rate","Disoccupazione osservata")]:
        header(title,"Italia e UE-27, tutte le professioni. Non identifica l'effetto AI. Possibile discontinuita metodologica nel 2021.")
        legends([("Italia",COLORS[0]),("UE-27",COLORS[1])]);items=[]
        for age in S["ages"]:
            series=[]
            for geo,col in zip(("IT","EU27_2020"),COLORS):
                rows=[r for r in O["eurostat"] if r["age"]==age and r["geo"]==geo]
                series.append(dict(color=col,y=[r[key] for r in rows]))
            items.append((age+" anni",series))
        vals=[v for _,ss in items for s in ss for v in s["y"]]
        panels(list(range(2019,2026)),items,"% della popolazione" if key=="employment_rate" else "% della forza lavoro",(0,max(vals)))
        paragraph(c,"Fonte: Eurostat lfsa_pganws. I gruppi di cinque anni sono sommati; nessuna media semplice dei tassi.",36,75,W-72,8,11);footer()
    rows=O["stanford"]["canaries_age_by_exposure"]
    ages=["Early Career 1 (22-25)","Early Career 2 (26-30)","Developing (31-34)","Mid-Career 1 (35-40)"]
    header("Esposizione AI e occupazione negli USA","Stanford/ADP: campione bilanciato, non rappresentativo dell'intero mercato USA. Correlazioni, non causalita.")
    legends([("Quintile 1: meno esposte",COLORS[1]),("Quintile 5: piu esposte",COLORS[0])]);items=[]
    groups=[[r for r in rows if r["exposure_quintile"]==q] for q in ("Quintile 1 (least exposed)","Quintile 5 (most exposed)")]
    for age in ages:items.append((age.split("(")[-1].rstrip(")")+" anni",[dict(color=col,y=[float(r[age]) for r in g]) for g,col in zip(groups,(COLORS[1],COLORS[0]))]))
    vals=[v for _,ss in items for s in ss for v in s["y"]]
    panels([r["observation_date"] for r in groups[0]],items,"Indice novembre 2022 = 100",(min(vals),max(vals)))
    paragraph(c,"Fonte: Canaries Dashboard, file age_by_exposure. Osservazioni fino ad agosto 2026; vintage 17 settembre 2026.",36,75,W-72,8,11);footer()
    rows=O["stanford"]["canaries_software_developers"]
    header("Sviluppatori software per eta","Serie osservata Stanford/ADP. Le fasce della fonte sono conservate senza convertirle artificialmente in quelle del modello.")
    legends([("Occupati nel campione",COLORS[0])]);items=[(age.split("(")[-1].rstrip(")")+" anni",[dict(color=COLORS[0],y=[float(r[age]) for r in rows])]) for age in ages]
    vals=[v for _,ss in items for s in ss for v in s["y"]]
    panels([r["observation_date"] for r in rows],items,"Indice novembre 2022 = 100",(min(vals),max(vals)))
    paragraph(c,"Fonte: Canaries Dashboard, file software_developers. Serie descrittiva; non misura tutti i posti disponibili.",36,75,W-72,8,11);footer()
    for metric,title in [("gap_potential","Forbice: offerta potenziale e domanda"),("employment_rate","Effetto sul tasso di occupazione"),("hire_rate","Effetto sulle assunzioni annuali"),("rehire_rate","Effetto sul ricollocamento"),("broad_nonemployment","Senza lavoro, inclusi gli scoraggiati")]:
        header(title,"ADV: profilo UE come proxy. Differenza AI meno senza AI, stesso matching in ciascuna coppia. Medianei scenari esplorativi.".replace("Medianei","Mediane dei"))
        legends([(sc["label"],col) for sc,col in zip(S["scenarios"].values(),COLORS)])
        items=[]
        start=1 if metric in ("hire_rate","rehire_rate") else 0
        for ag,age in enumerate(S["ages"]):
            series=[dict(color=col,y=[t[0][ag] for t in sc["metrics"][metric]["difference"]["p50"]][start:]) for sc,col in zip(S["scenarios"].values(),COLORS)]
            items.append((age+" anni",series))
        vals=[v for _,ss in items for s in ss for v in s["y"]]
        panels(S["years"][start:],items,"Punti percentuali",(min(vals+[0]),max(vals+[0])))
        paragraph(c,"Parametri AI/matching assunti, non stimati. La forbice usa l'offerta potenziale: lo scoraggiamento non cancella il problema. Bande di dispersione e tutte le regioni disponibili nel rapporto HTML.",36,78,W-72,8,11);footer()
    for metric,title,unit in [("employment_rate","Occupazione: con e senza AI","% della popolazione"),("first_hires","Nuove assunzioni: primo ingresso","Flussi annui; base potenziale 2026 = 100"),("separations","Perdite del lavoro: turnover","Flussi annui; base potenziale 2026 = 100"),("job_cuts","Perdite del lavoro: tagli dei posti","Flussi annui; base potenziale 2026 = 100"),("rehires","Ricollocamenti annuali","Flussi annui; base potenziale 2026 = 100")]:
        sc=S["scenarios"]["slow"] if "slow" in S["scenarios"] else list(S["scenarios"].values())[2]
        header(title,"ADV, scenario di riconversione lenta. Stesse estrazioni e stesso matching nella coppia con e senza AI.")
        legends([("Con AI",COLORS[0]),("Senza AI",COLORS[1])]); items=[]
        start=0 if metric=="employment_rate" else 1
        for ag,age in enumerate(S["ages"]):
            items.append((age+" anni",[dict(color=col,y=[t[0][ag] for t in sc["metrics"][metric][v]["p50"]][start:]) for v,col in zip(("ai","noai"),COLORS)]))
        vals=[v for _,ss in items for s in ss for v in s["y"]];panels(S["years"][start:],items,unit,(0,max(vals)))
        paragraph(c,"Simulazioni condizionate, non dati osservati. Turnover e tagli sono flussi distinti. I flussi non sono conteggi di persone; il 2026 e escluso perche anno iniziale. Collegamento macro in una sola direzione.",36,78,W-72,8,11);footer()
    sc=list(S["scenarios"].values())[2]
    for v,label in [("ai","Con AI"),("noai","Senza AI")]:
        header("Domanda e offerta per eta: "+label,"ADV, riconversione lenta. Scala comune: 100 = offerta potenziale della fascia nel 2026.")
        keys=["potential_supply","supply","demand","employed"];legends(list(zip(["Offerta potenziale","Offerta attiva","Domanda di lavoro","Occupati"],COLORS)));items=[]
        for ag,age in enumerate(S["ages"]):items.append((age+" anni",[dict(color=col,y=[t[0][ag] for t in sc["metrics"][k][v]["p50"]]) for k,col in zip(keys,COLORS)]))
        vals=[v for _,ss in items for s in ss for v in s["y"]];panels(S["years"],items,"Indice della fascia, base potenziale 2026 = 100",(0,max(vals)))
        paragraph(c,"L'offerta potenziale conserva gli scoraggiati; la distanza dalla domanda non coincide con la sola disoccupazione. La domanda per eta e un'allocazione assunta della capacita macro, non una serie di offerte di lavoro osservate.",36,78,W-72,8,11);footer()
    c.save();print(dest)


if __name__=="__main__":
    main()
