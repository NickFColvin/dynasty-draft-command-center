
from __future__ import annotations
import io, re, time
import numpy as np
import pandas as pd
import requests
import streamlit as st
from rapidfuzz import fuzz, process

BASE="https://api.sleeper.app/v1"
RB_DYNASTY="https://www.rotoballer.com/updated-dynasty-fantasy-football-rankings-rb-wr-qb-te-august-2026/1903000"

PFN_TOP30 = {
"Ja'Marr Chase":1,"Puka Nacua":2,"Bijan Robinson":3,"Jaxon Smith-Njigba":4,"Justin Jefferson":5,
"Jahmyr Gibbs":6,"CeeDee Lamb":7,"Malik Nabers":8,"Ashton Jeanty":9,"Amon-Ra St. Brown":10,
"Drake London":11,"Brock Bowers":12,"Trey McBride":13,"De'Von Achane":14,"James Cook III":15,
"Tetairoa McMillan":16,"Jeremiyah Love":17,"Nico Collins":18,"George Pickens":19,"Chris Olave":20,
"Emeka Egbuka":21,"Omarion Hampton":22,"Jonathan Taylor":23,"Garrett Wilson":24,"Ladd McConkey":25,
"Josh Allen":26,"Drake Maye":27,"Jayden Daniels":28,"A.J. Brown":29,"Chase Brown":30
}
SI_TOP30 = {
"Ja'Marr Chase":1,"Puka Nacua":2,"Bijan Robinson":3,"Jahmyr Gibbs":4,"Jaxon Smith-Njigba":5,
"Amon-Ra St. Brown":6,"CeeDee Lamb":7,"Justin Jefferson":8,"Malik Nabers":9,"Ashton Jeanty":10,
"Jeremiyah Love":11,"De'Von Achane":12,"Brock Bowers":13,"Drake London":14,"Trey McBride":15,
"Jonathan Taylor":16,"Tetairoa McMillan":17,"Nico Collins":18,"Emeka Egbuka":19,"Omarion Hampton":20,
"Josh Allen":21,"Chris Olave":22,"George Pickens":23,"James Cook III":24,"Garrett Wilson":25,
"Ladd McConkey":26,"A.J. Brown":27,"Drake Maye":28,"Jayden Daniels":29,"Chase Brown":30
}
DS_TOP25 = {
"Ja'Marr Chase":1,"Bijan Robinson":2,"Jaxon Smith-Njigba":3,"Jahmyr Gibbs":4,"Puka Nacua":5,
"Jeremiyah Love":6,"Amon-Ra St. Brown":7,"CeeDee Lamb":8,"Justin Jefferson":9,"Malik Nabers":10,
"Ashton Jeanty":11,"De'Von Achane":12,"Jonathan Taylor":13,"Drake London":14,"Omarion Hampton":15,
"Nico Collins":16,"Brock Bowers":17,"Trey McBride":18,"Tetairoa McMillan":19,"James Cook III":20,
"George Pickens":21,"Chris Olave":22,"Emeka Egbuka":23,"Kenneth Walker III":24,"Colston Loveland":25
}
FP_TOP5 = {"Ja'Marr Chase":1,"Jaxon Smith-Njigba":2,"Puka Nacua":3,"Bijan Robinson":4,"Jahmyr Gibbs":5}

HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"}

st.set_page_config(page_title="Dynasty Draft Command Center v3.20", page_icon="🏈", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #0f1115;
        color: #e8eaed;
    }
    section[data-testid="stSidebar"] {
        background-color: #151922;
    }
    div[data-testid="stMetric"] {
        background-color: #171b24;
        border: 1px solid #2a3140;
        padding: 12px;
        border-radius: 10px;
    }
    div[data-testid="stDataFrame"] {
        background-color: #131720;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #171b24;
        border-radius: 8px 8px 0 0;
        padding: 8px 14px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #232938 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f4f6f8;
    }
    p, label, .stMarkdown, .stCaption {
        color: #d7dce2;
    }
</style>
""", unsafe_allow_html=True)


# ---- Built-in Aug 4 single-QB dynasty fallback (top 100) ----
# Source: RotoBaller top-315 single-QB dynasty rankings, Aug 4 2026.
FALLBACK_DYNASTY = """rank,name,position
1,Ja'Marr Chase,WR
2,Bijan Robinson,RB
3,Jahmyr Gibbs,RB
4,Jaxon Smith-Njigba,WR
5,Puka Nacua,WR
6,Amon-Ra St. Brown,WR
7,Malik Nabers,WR
8,Justin Jefferson,WR
9,Drake London,WR
10,Ashton Jeanty,RB
11,Jeremiyah Love,RB
12,CeeDee Lamb,WR
13,Brock Bowers,TE
14,De'Von Achane,RB
15,Trey McBride,TE
16,James Cook III,RB
17,George Pickens,WR
18,Tetairoa McMillan,WR
19,Emeka Egbuka,WR
20,Omarion Hampton,RB
21,Jonathan Taylor,RB
22,Carnell Tate,WR
23,Josh Allen,QB
24,Nico Collins,WR
25,Garrett Wilson,WR
26,Drake Maye,QB
27,Chris Olave,WR
28,Jordyn Tyson,WR
29,Luther Burden III,WR
30,Jayden Daniels,QB
31,A.J. Brown,WR
32,Chase Brown,RB
33,Ladd McConkey,WR
34,Lamar Jackson,QB
35,Colston Loveland,TE
36,DeVonta Smith,WR
37,Marvin Harrison Jr.,WR
38,Saquon Barkley,RB
39,Kenneth Walker III,RB
40,Quinshon Judkins,RB
41,Zay Flowers,WR
42,Rashee Rice,WR
43,Christian McCaffrey,RB
44,Breece Hall,RB
45,Tyler Warren,TE
46,Rome Odunze,WR
47,Makai Lemon,WR
48,Jaylen Waddle,WR
49,Tee Higgins,WR
50,TreVeyon Henderson,RB
51,Brian Thomas Jr.,WR
52,Kyren Williams,RB
53,Bucky Irving,RB
54,Jameson Williams,WR
55,Caleb Williams,QB
56,Jadarian Price,RB
57,Travis Etienne Jr.,RB
58,Harold Fannin Jr.,TE
59,Cam Skattebo,RB
60,Javonte Williams,RB
61,Joe Burrow,QB
62,Jalen Hurts,QB
63,Jordan Addison,WR
64,Sam LaPorta,TE
65,Josh Jacobs,RB
66,Patrick Mahomes II,QB
67,Bhayshul Tuten,RB
68,Tucker Kraft,TE
69,DJ Moore,WR
70,Justin Herbert,QB
71,Derrick Henry,RB
72,Michael Wilson,WR
73,KC Concepcion,WR
74,Christian Watson,WR
75,Kyle Pitts Sr.,TE
76,Omar Cooper Jr.,WR
77,DK Metcalf,WR
78,Kenyon Sadiq,TE
79,Alec Pierce,WR
80,Terry McLaurin,WR
81,D'Andre Swift,RB
82,Jaxson Dart,QB
83,Wan'Dale Robinson,WR
84,David Montgomery,RB
85,Parker Washington,WR
86,Denzel Boston,WR
87,Jonah Coleman,RB
88,Mike Evans,WR
89,Josh Downs,WR
90,Davante Adams,WR
91,Jayden Higgins,WR
92,Jakobi Meyers,WR
93,Trevor Lawrence,QB
94,Matthew Golden,WR
95,Courtland Sutton,WR
96,Kyle Monangai,RB
97,Bo Nix,QB
98,RJ Harvey,RB
99,Oronde Gadsden II,TE
100,Dak Prescott,QB
"""

# Built-in exact Aug 20 FantasyPros PPR projection fallback for top 10 at each major position.
FP_FALLBACK = """name,position,season_fpts
Puka Nacua,WR,339.8
Ja'Marr Chase,WR,336.0
Jaxon Smith-Njigba,WR,324.1
Amon-Ra St. Brown,WR,319.8
Drake London,WR,287.1
Rashee Rice,WR,274.1
CeeDee Lamb,WR,273.0
Justin Jefferson,WR,272.8
Chris Olave,WR,261.7
A.J. Brown,WR,255.2
Jahmyr Gibbs,RB,372.9
Bijan Robinson,RB,369.5
Christian McCaffrey,RB,334.8
Jonathan Taylor,RB,310.1
De'Von Achane,RB,292.4
Chase Brown,RB,278.5
Ashton Jeanty,RB,276.7
Derrick Henry,RB,273.7
James Cook III,RB,270.6
Saquon Barkley,RB,264.7
Josh Allen,QB,372.5
Lamar Jackson,QB,324.9
Drake Maye,QB,323.0
Jayden Daniels,QB,322.6
Jalen Hurts,QB,320.5
Joe Burrow,QB,310.9
Jaxson Dart,QB,309.9
Brock Purdy,QB,307.5
Trevor Lawrence,QB,306.2
Dak Prescott,QB,306.2
Trey McBride,TE,254.3
Brock Bowers,TE,244.1
Colston Loveland,TE,211.4
Tyler Warren,TE,199.2
Kyle Pitts Sr.,TE,195.7
Harold Fannin Jr.,TE,191.1
Sam LaPorta,TE,184.1
Travis Kelce,TE,182.1
Dallas Goedert,TE,179.4
Tucker Kraft,TE,178.4
"""

class Sleeper:
    def __init__(self):
        self.s=requests.Session()
        self.s.headers.update({"User-Agent":"DynastyDraftCommandCenter/3.20"})
    def get(self,p,t=20):
        r=self.s.get(BASE+p,timeout=t); r.raise_for_status(); return r.json()
    def user(self,u): return self.get(f"/user/{u}")
    def leagues(self,uid,s): return self.get(f"/user/{uid}/leagues/nfl/{s}")
    def drafts(self,lid): return self.get(f"/league/{lid}/drafts")
    def picks(self,did): return self.get(f"/draft/{did}/picks")
    def users(self,lid): return self.get(f"/league/{lid}/users")
    def players(self): return self.get("/players/nfl",45)

api=Sleeper()
@st.cache_data(ttl=300)
def c_user(x): return api.user(x)
@st.cache_data(ttl=30)
def c_leagues(uid,s): return api.leagues(uid,s)
@st.cache_data(ttl=15)
def c_drafts(lid): return api.drafts(lid)
@st.cache_data(ttl=5)
def c_picks(did): return api.picks(did)
@st.cache_data(ttl=15)
def c_users(lid): return api.users(lid)
@st.cache_data(ttl=86400)
def c_players(): return api.players()

def nn(s):
    s=str(s).lower().replace("’","'")
    s=re.sub(r"\b(jr\.?|sr\.?|ii|iii|iv)\b","",s)
    s=re.sub(r"[^a-z0-9 ]","",s)
    return re.sub(r"\s+"," ",s).strip()

def sleeper_df(mp):
    rows=[]
    for pid,p in mp.items():
        pos="RB" if p.get("position")=="FB" else p.get("position")
        if pos not in {"QB","RB","WR","TE"}: continue
        name=p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip()
        rows.append({"player_id":str(pid),"name":name,"name_norm":nn(name),"position":pos,
                     "age":pd.to_numeric(p.get("age"),errors="coerce"),"team":p.get("team") or "FA"})
    return pd.DataFrame(rows)

@st.cache_data(ttl=21600)
def dynasty_board():
    # Prefer the full current RotoBaller page; fall back to bundled top 100.
    try:
        r=requests.get(RB_DYNASTY,headers=HEADERS,timeout=25); r.raise_for_status()
        text=re.sub(r"<[^>]+>"," ",r.text)
        text=text.replace("&apos;","'").replace("&#8217;","'").replace("&amp;","&")
        text=re.sub(r"\s+"," ",text)
        # HTML table text generally renders: tier rank player pos.
        pat=re.compile(r"(?:^|\s)(\d{1,2})\s+(\d{1,3})\s+([A-Za-z0-9'.\- ]{2,45}?)\s+(QB|RB|WR|TE)(?=\s)")
        rows={}
        for m in pat.finditer(text):
            rank=int(m.group(2))
            if 1<=rank<=400 and rank not in rows:
                name=re.sub(r"\s+"," ",m.group(3)).strip()
                rows[rank]={"market_rank":rank,"name":name,"name_norm":nn(name),"position":m.group(4),"market_source":"RotoBaller live"}
        if len(rows)>=80:
            return pd.DataFrame([rows[k] for k in sorted(rows)])
    except Exception:
        pass
    fb=pd.read_csv(io.StringIO(FALLBACK_DYNASTY))
    fb=fb.rename(columns={"rank":"market_rank"})
    fb["name_norm"]=fb.name.map(nn)
    fb["market_source"]="RotoBaller bundled Aug 4"
    return fb

@st.cache_data(ttl=21600)
def projections():
    # Try live FantasyPros projections. If blocked or layout changes, merge in built-in exact top-10 fallbacks.
    parts=[]
    for pos in ["QB","RB","WR","TE"]:
        try:
            url=f"https://www.fantasypros.com/nfl/projections/{pos.lower()}.php?scoring=PPR&week=draft"
            r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status()
            tabs=pd.read_html(io.StringIO(r.text))
            for t in tabs:
                if isinstance(t.columns,pd.MultiIndex):
                    t.columns=[" ".join(str(x) for x in tup if "Unnamed" not in str(x)).strip() for tup in t.columns]
                pc=next((c for c in t.columns if "player" in str(c).lower()),None)
                fc=next((c for c in t.columns if "fpts" in str(c).lower()),None)
                if pc is None or fc is None: continue
                out=[]
                for _,row in t.iterrows():
                    raw=str(row[pc]).strip()
                    # Usually "Player TEAM"
                    raw=re.sub(r"\s+\(\d+\)$","",raw)
                    tokens=raw.split()
                    team=tokens[-1] if tokens and re.fullmatch(r"[A-Z]{2,4}",tokens[-1]) else ""
                    name=" ".join(tokens[:-1]) if team else raw
                    # remove duplicate abbreviated name sometimes embedded
                    toks=name.split()
                    if len(toks)>=4 and re.fullmatch(r"[A-Z]\.",toks[-2]): name=" ".join(toks[:-2])
                    mm=re.search(r"-?\d+(?:\.\d+)?",str(row[fc]).replace(",",""))
                    if not mm: continue
                    f=float(mm.group())
                    if f>0: out.append({"name":name,"name_norm":nn(name),"position":pos,"season_fpts":f,"proj_source":"FantasyPros live"})
                if len(out)>=10:
                    parts.append(pd.DataFrame(out)); break
        except Exception:
            pass
    live=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame(columns=["name","name_norm","position","season_fpts","proj_source"])
    fb=pd.read_csv(io.StringIO(FP_FALLBACK))
    fb["name_norm"]=fb.name.map(nn); fb["proj_source"]="FantasyPros bundled Aug 20"
    # Live wins; fallback fills gaps.
    allp=pd.concat([live,fb],ignore_index=True)
    allp=allp.drop_duplicates(["name_norm","position"],keep="first")
    allp["proj_ppg"]=allp.season_fpts/17.0
    return allp

def attach(base,src,cols,same_pos=True):
    out=base.copy()
    for c in cols:
        if c not in out.columns: out[c]=np.nan if "source" not in c else None
    for i,r in out.iterrows():
        cand=src
        if same_pos and "position" in src.columns: cand=cand[cand.position==r.position]
        ex=cand[cand.name_norm==r.name_norm]
        sr=ex.iloc[0] if len(ex) else None
        if sr is None and len(cand):
            m=process.extractOne(r.name_norm,cand.name_norm.tolist(),scorer=fuzz.ratio)
            if m and m[1]>=95: sr=cand[cand.name_norm==m[0]].iloc[0]
        if sr is not None:
            for c in cols:
                if c in sr.index: out.at[i,c]=sr[c]
    return out


def build_standalone_consensus(rb_df):
    """
    Build consensus directly from ranking-source rows, independent of Sleeper/player dataframe state.
    RotoBaller supplies the full backbone; bundled snapshots adjust overlapping names.
    """
    rb=rb_df.copy()
    rb=rb[["name","name_norm","market_rank"]].dropna(subset=["market_rank"]).copy()
    rb["market_rank"]=pd.to_numeric(rb["market_rank"],errors="coerce")
    rb=rb.dropna(subset=["market_rank"]).sort_values("market_rank").drop_duplicates("name_norm")
    rb["pfn_rank"]=rb["name"].map(PFN_TOP30)
    rb["si_rank"]=rb["name"].map(SI_TOP30)
    rb["ds_rank"]=rb["name"].map(DS_TOP25)
    rb["fp_rank"]=rb["name"].map(FP_TOP5)

    rank_cols=["market_rank","pfn_rank","si_rank","ds_rank","fp_rank"]

    vals=[]
    for _,r in rb.iterrows():
        raw=[]
        scores=[]
        for c in rank_cols:
            v=pd.to_numeric(r[c],errors="coerce")
            if pd.notna(v):
                raw.append(float(v))
                scores.append(100*np.exp(-0.010*(float(v)-1)))
        consensus_value=float(np.mean(scores))
        sources=len(scores)
        spread=(max(raw)-min(raw)) if len(raw)>1 else 0.0
        if sources>=4 and spread<=5:
            conf="High"
        elif sources>=3 and spread<=8:
            conf="Medium"
        elif sources>=2 and spread<=12:
            conf="Mixed"
        else:
            conf="Single source"
        vals.append((consensus_value,sources,spread,conf))

    rb[["consensus_value","consensus_sources","source_spread","consensus_confidence"]]=pd.DataFrame(vals,index=rb.index)
    rb["consensus_rank"]=rb["consensus_value"].rank(method="min",ascending=False)

    # Hard sanity fallback for ordering.
    top10=rb.sort_values("consensus_rank").head(10)["name"].tolist()
    elite={"Ja'Marr Chase","Puka Nacua","Bijan Robinson","Jahmyr Gibbs","Jaxon Smith-Njigba",
           "Amon-Ra St. Brown","CeeDee Lamb","Justin Jefferson","Malik Nabers","Ashton Jeanty",
           "Drake London","Brock Bowers","Trey McBride"}
    overlap=sum(1 for n in top10 if n in elite)
    if len(rb)<100 or overlap<6:
        rb["consensus_rank"]=rb["market_rank"]
        rb["consensus_value"]=100*np.exp(-0.010*(rb["market_rank"]-1))
        rb["consensus_sources"]=1
        rb["source_spread"]=0.0
        rb["consensus_confidence"]="Backbone fallback"
        fallback=True
    else:
        fallback=False

    rb.attrs["fallback"]=fallback
    rb.attrs["top10"]=rb.sort_values("consensus_rank").head(10)["name"].tolist()
    return rb

def merge_consensus_into_players(players_df, consensus_df):
    x=players_df.copy()
    keep=["name_norm","pfn_rank","si_rank","ds_rank","fp_rank","consensus_rank","consensus_value",
          "consensus_sources","source_spread","consensus_confidence"]
    c=consensus_df[keep].drop_duplicates("name_norm")
    x=x.merge(c,on="name_norm",how="left",suffixes=("","_cons"))
    return x

def age_adj(pos,age):
    if pd.isna(age): return 0.0
    peak={"WR":24.5,"RB":23.5,"TE":25.5,"QB":27.0}[pos]
    old={"WR":2.4,"RB":3.8,"TE":1.8,"QB":1.0}[pos]
    young={"WR":1.3,"RB":1.7,"TE":1.0,"QB":0.5}[pos]
    d=age-peak
    return float(np.clip((-d*young if d<0 else -d*old),-18,8))

def league_mult(pos): return {"WR":1.08,"RB":1.02,"TE":.97,"QB":.70}[pos]
def replacement(pos): return {"WR":10.2,"RB":9.4,"TE":8.0,"QB":16.0}[pos]

def score(df):
    x=df.copy()
    # Every ranked player is usable; exact real PPR projection is an extra production signal.
    x["rank_ok"]=x.market_rank.notna()
    legacy_market=100*np.exp(-0.0068*(x.market_rank-1))
    market=np.where(x.consensus_value.notna(),x.consensus_value,legacy_market)
    x["market_value"]=market

    # Conservative estimated projection fallback for ranked players without exact points.
    # These are clearly labeled as estimates, not sourced projections.
    rank_num=x.market_rank.astype(float)
    pos_base=x.position.map({"QB":295.0,"RB":205.0,"WR":215.0,"TE":145.0})
    pos_decay=x.position.map({"QB":0.55,"RB":0.95,"WR":0.85,"TE":0.75})
    est_points=(pos_base - pos_decay*(rank_num-1)).clip(lower=55)
    x["estimated_season_fpts"]=est_points.round(1)
    x["display_season_fpts"]=x.season_fpts.where(x.season_fpts.notna(),x.estimated_season_fpts)
    x["display_proj_ppg"]=(x["display_season_fpts"]/17.0).round(2)
    x["age_adjustment"]=[age_adj(p,a) for p,a in zip(x.position,x.age)]
    # For players without a points projection, production is neutral rather than invented.
    projected=x.proj_ppg.notna()
    exact_prod=50+(x.proj_ppg-x.position.map(replacement)).clip(-5,12)*2.5
    est_prod=50+(x.display_proj_ppg-x.position.map(replacement)).clip(-5,12)*1.2
    prod=np.where(projected, exact_prod, est_prod)
    x["projection_exact"]=projected
    x["projection_status"]=np.where(
        projected,
        "Exact projection",
        "Dynasty rank only"
    )
    x["model_value"]=(0.78*market + 0.14*prod + 0.08*(50+x.age_adjustment*2))*x.position.map(league_mult)
    x.loc[~x.rank_ok,"model_value"]=np.nan
    x["model_value"]=x.model_value.clip(0,100).round(1)
    x["model_rank"]=x.model_value.rank(method="min",ascending=False)
    x["edge"]=(x.model_value-x.market_value).round(1)
    x["consensus_edge"]=(x.consensus_rank-x.model_rank).round(0)
    return x

def rp(o,t): return ((o-1)//t+1,(o-1)%t+1)
def slot_for(o,t):
    r,p=rp(o,t); return p if r%2 else t+1-p
def nextp(slot,current,t,rounds):
    """
    Return the user's future startup picks.
    If the user is currently on the clock, exclude the current pick so
    availability logic evaluates the following turn rather than this one.
    """
    a=[]
    user_on_clock=(slot_for(current,t)==slot)
    for r in range(1,rounds+1):
        pir=slot if r%2 else t+1-slot
        ov=(r-1)*t+pir
        if user_on_clock:
            if ov>current:
                a.append(ov)
        else:
            if ov>=current:
                a.append(ov)
    return a[:3]


# ---------------- Decision engine v3.3 ----------------

def add_tiers(df):
    """
    Smoothed dynasty tiers for startup drafting.

    Goals:
    - Avoid giant all-in-one tiers.
    - Avoid tiny 1-2 player tiers unless there is a truly large cliff.
    - Keep early tiers useful for real draft decisions.
    """
    x=df.sort_values(["model_value","market_rank"],ascending=[False,True]).copy()
    if x.empty:
        x["tier"]=[]
        return x

    vals=x.model_value.tolist()
    ranks=x.market_rank.tolist()
    tiers=[]
    tier=1
    tier_start=0
    tier_anchor=float(vals[0])

    for i,(v,mr) in enumerate(zip(vals,ranks)):
        if i==0:
            tiers.append(tier)
            continue

        tier_size=i-tier_start
        prev_v=float(vals[i-1])
        gap=prev_v-float(v)
        cumulative=tier_anchor-float(v)

        # Early board: require a reasonable tier size unless cliff is very large.
        if tier <= 3:
            min_size=4
            normal_band=6.5
            big_gap=4.5
        elif tier <= 6:
            min_size=5
            normal_band=8.0
            big_gap=5.5
        else:
            min_size=6
            normal_band=10.0
            big_gap=6.5

        start_new = False

        # Normal tier break only after minimum useful size.
        if tier_size >= min_size and cumulative >= normal_band:
            start_new = True

        # Truly large adjacent cliff can create a smaller tier.
        if gap >= big_gap and tier_size >= 2:
            start_new = True

        # Extra-deep cumulative cliff forces a break.
        if cumulative >= normal_band * 1.45:
            start_new = True

        if start_new:
            tier += 1
            tier_start=i
            tier_anchor=float(v)

        tiers.append(tier)

    x["tier"]=tiers
    return x

    tiers=[]
    tier=1
    tier_anchor=float(x.iloc[0].model_value)
    prev_rank=float(x.iloc[0].market_rank) if pd.notna(x.iloc[0].market_rank) else 1.0
    for idx, row in x.iterrows():
        v=float(row.model_value)
        mr=float(row.market_rank) if pd.notna(row.market_rank) else prev_rank

        # Wider bands as we move deeper, because value differences compress later.
        if tier <= 2:
            band=5.0
        elif tier <= 5:
            band=6.5
        else:
            band=8.0

        market_cliff=(mr-prev_rank)>=5 and tier<=8
        cumulative_drop=(tier_anchor-v)>=band

        if tiers and (cumulative_drop or market_cliff):
            tier += 1
            tier_anchor=v

        tiers.append(tier)
        prev_rank=mr

    x["tier"]=tiers
    return x

def availability_probability(row, picks_until_next):
    """
    Estimate probability a player survives to user's next pick from dynasty market rank.
    This is intentionally conservative and transparent, not a simulated claim of certainty.
    """
    if picks_until_next is None or picks_until_next <= 0:
        return 0.0
    rank=float(row.market_rank)
    # How many selections until market ADP would normally consume the player?
    cushion=rank - current
    # Logistic survival curve. Positive cushion = more likely to remain.
    scale=max(4.0, picks_until_next*0.42)
    z=(cushion-picks_until_next)/scale
    p=1/(1+np.exp(-z))
    return float(np.clip(p,0.02,0.98))

def position_run_alert(picks, players, window=8):
    if not picks:
        return None
    z=pd.DataFrame(picks).tail(window).copy()
    if z.empty or "player_id" not in z.columns:
        return None
    z["player_id"]=z.player_id.astype(str)
    z=z.merge(players[["player_id","position"]],on="player_id",how="left")
    vc=z.position.value_counts()
    if vc.empty:
        return None
    pos=vc.index[0]
    n=int(vc.iloc[0])
    if n>=4:
        return f"{n} {pos}s have gone in the last {min(window,len(z))} picks."
    return None

def roster_construction_status(roster):
    counts=roster.position.value_counts().to_dict() if len(roster) else {}
    # 21-round target ranges for this exact league.
    targets={"WR":(7,9),"RB":(5,7),"QB":(1,2),"TE":(1,2)}
    rows=[]
    for pos in ["WR","RB","TE","QB"]:
        lo,hi=targets[pos]
        n=counts.get(pos,0)
        if n<lo: status="BUILD"
        elif n<=hi: status="ON TRACK"
        else: status="HEAVY"
        rows.append({"Pos":pos,"Rostered":n,"Target":f"{lo}-{hi}","Status":status})
    return pd.DataFrame(rows)

def decision_summary(avail, next_overall, current_overall):
    if avail.empty:
        return None

    board=add_tiers(avail)
    top=board.iloc[0]
    current_tier=int(top.tier)
    tier_pool=board[board.tier==current_tier].copy()
    tier_remaining=len(tier_pool)
    picks_until=(next_overall-current_overall) if next_overall else None

    # Survival estimates for everyone in the current tier.
    survival=[]
    if picks_until and picks_until>0:
        for _,r in tier_pool.iterrows():
            survival.append(availability_probability(r,picks_until))
        expected_survivors=sum(survival)
        chance_any_survives=1.0
        for p in survival:
            chance_any_survives*=max(0.0,1-p)
        chance_any_survives=1-chance_any_survives
    else:
        expected_survivors=0.0
        chance_any_survives=0.0

    # Tier-drop penalty: difference between current tier's best player and next tier's best.
    next_tier_pool=board[board.tier>current_tier]
    if len(next_tier_pool):
        next_best=next_tier_pool.iloc[0]
        tier_drop=float(top.model_value-next_best.model_value)
    else:
        next_best=None
        tier_drop=0.0

    recommendation="TAKE NOW"
    reasons=[]

    # Strong TAKE conditions.
    if tier_remaining <= 2:
        recommendation="TAKE NOW"
        reasons.append(f"Only {tier_remaining} player{'s' if tier_remaining!=1 else ''} remain in Tier {current_tier}.")
    elif picks_until and picks_until>0 and chance_any_survives < 0.35:
        recommendation="TAKE NOW"
        reasons.append(f"Low estimated chance ({chance_any_survives:.0%}) that anyone from this tier reaches your next pick.")
    elif tier_drop >= 5.0:
        recommendation="TAKE NOW"
        reasons.append(f"There is a meaningful {tier_drop:.1f}-point model drop to the next tier.")

    # WAIT conditions.
    if picks_until and picks_until>0 and tier_remaining >= 5 and chance_any_survives >= 0.70:
        recommendation="WAIT"
        reasons.append(f"{tier_remaining} players remain in Tier {current_tier}, with a {chance_any_survives:.0%} estimated chance at least one survives.")

    # TRADE DOWN is only flagged when the tier is deep and the drop is small.
    if picks_until and picks_until>0 and tier_remaining >= 6 and chance_any_survives >= 0.78 and tier_drop < 4.0:
        recommendation="TRADE DOWN"
        reasons.append("The current tier is deep enough that moving back a few spots may preserve player quality while adding value.")

    # 1QB guardrail.
    if top.position=="QB" and top.market_rank>15:
        if recommendation=="TAKE NOW":
            recommendation="WAIT ON QB"
        reasons.append("This is 1QB, so quarterback scarcity is lower than in superflex.")

    # WR-format context.
    if top.position=="WR":
        reasons.append("3WR + 2FLEX increases the value of elite and deep WR assets.")

    # Build shortlist.
    same_tier=tier_pool.head(8)

    return {
        "top":top,
        "board":board,
        "same_tier":same_tier,
        "picks_until":picks_until,
        "tier_remaining":tier_remaining,
        "chance_any_survives":chance_any_survives,
        "expected_survivors":expected_survivors,
        "tier_drop":tier_drop,
        "next_best":next_best,
        "recommendation":recommendation,
        "rationale":" ".join(reasons) if reasons else "Highest roster-adjusted dynasty value available.",
    }



# ---------------- Monte Carlo draft simulator v3.9 ----------------

def simulate_to_next_pick(board, picks_to_simulate, n_sims=3000, seed=42, pressure=None):
    """
    Fast Monte Carlo simulator using NumPy arrays rather than repeated DataFrame copies.
    """
    if picks_to_simulate is None or picks_to_simulate <= 0 or board.empty:
        return None

    rng=np.random.default_rng(seed)
    base=board.sort_values("market_rank").copy().reset_index(drop=True)
    pool_n=min(len(base), max(80, picks_to_simulate*4))
    base=base.head(pool_n).copy()

    ranks=base.market_rank.to_numpy(dtype=float)
    positions=base.position.to_numpy()
    n=len(base)

    survive_counts=np.zeros(n,dtype=int)
    best_survivor_counts=np.zeros(n,dtype=int)

    pos_mult_map={"WR":1.08,"RB":1.04,"TE":0.92,"QB":0.72}
    pressure=pressure or {"WR":1.0,"RB":1.0,"QB":1.0,"TE":1.0}
    for k in pos_mult_map:
        pos_mult_map[k]*=pressure.get(k,1.0)
    base_pos=np.array([pos_mult_map.get(p,1.0) for p in positions],dtype=float)

    for _ in range(int(n_sims)):
        alive=np.ones(n,dtype=bool)

        for _pick in range(int(picks_to_simulate)):
            alive_idx=np.flatnonzero(alive)
            if len(alive_idx)==0:
                break

            # Top 14 alive by rank; base is already sorted by rank.
            cand_idx=alive_idx[:min(14,len(alive_idx))]
            cand_ranks=ranks[cand_idx]
            best_rank=cand_ranks[0]
            rank_gap=cand_ranks-best_rank

            weights=np.exp(-0.22*rank_gap) * base_pos[cand_idx]

            # Pick-level manager preference noise.
            pos_noise={
                "WR":rng.lognormal(0.0,0.12),
                "RB":rng.lognormal(0.0,0.15),
                "TE":rng.lognormal(0.0,0.12),
                "QB":rng.lognormal(-0.10,0.18),
            }
            taste=np.array([pos_noise.get(positions[i],1.0) for i in cand_idx])
            weights*=taste
            weights*=rng.lognormal(0.0,0.20,size=len(cand_idx))
            weights/=weights.sum()

            chosen_local=rng.choice(len(cand_idx),p=weights)
            alive[cand_idx[chosen_local]]=False

        alive_idx=np.flatnonzero(alive)
        survive_counts[alive_idx]+=1
        if len(alive_idx):
            best_survivor_counts[alive_idx[0]]+=1

    out=base[["player_id","name","position","market_rank","tier","model_value"]].copy()
    out["survival_prob"]=survive_counts/n_sims
    out["best_survivor_prob"]=best_survivor_counts/n_sims
    return out

def pairing_table(current_choice, sim_df, top_n=12):
    if sim_df is None or sim_df.empty:
        return pd.DataFrame()
    x=sim_df.copy()
    # Pairing score balances survivor probability and model value.
    x["pair_score"]=(x["survival_prob"]*100*0.45 + x["model_value"]*0.55).round(1)
    # Avoid recommending same player if current choice is already being taken.
    x=x[x.player_id!=current_choice.player_id]
    return x.sort_values(["pair_score","market_rank"],ascending=[False,True]).head(top_n)



# ---------------- Trade Lab + opponent tendencies v3.12 ----------------

def startup_pick_value(overall):
    return round(100*(float(overall)**-0.36),2)

def future_rookie_value(round_no, years_out=1, expected_slot="mid"):
    base={1:31.0,2:13.5,3:6.0,4:3.0}.get(int(round_no),1.5)
    slot_mult={"early":1.27,"mid":1.0,"late":0.80}.get(expected_slot,1.0)
    time_discount=0.88**max(int(years_out),0)
    return round(base*slot_mult*time_discount,2)

def parse_pick_list(s):
    vals=[]
    for tok in str(s).split(","):
        tok=tok.strip()
        if not tok: continue
        try:
            v=int(tok)
            if v>0: vals.append(v)
        except: pass
    return vals

def player_value_by_name(players_df, name):
    if not name: return 0.0, None
    m=players_df[players_df.name==name]
    if m.empty: return 0.0, None
    r=m.iloc[0]
    return float(r.model_value) if pd.notna(r.model_value) else 0.0, r

def trade_verdict(give, receive):
    if give<=0 and receive<=0: return "NO TRADE", 0
    delta=receive-give
    ratio=(receive/give) if give>0 else 99
    if ratio>=1.10: verdict="ACCEPT"
    elif ratio>=1.02: verdict="LEAN ACCEPT"
    elif ratio>=0.97: verdict="FAIR"
    elif ratio>=0.90: verdict="LEAN DECLINE"
    else: verdict="DECLINE"
    return verdict, delta

def manager_tendency_table(picks, players, users):
    if not picks:
        return pd.DataFrame()
    z=pd.DataFrame(picks).copy()
    if z.empty or "player_id" not in z.columns:
        return pd.DataFrame()
    z["player_id"]=z.player_id.astype(str)
    z=z.merge(players[["player_id","position","age","market_rank"]],on="player_id",how="left")
    um={str(u.get("user_id")):(u.get("display_name") or u.get("username") or str(u.get("user_id"))) for u in users}
    rows=[]
    for uid,g in z.groupby("picked_by"):
        vc=g.position.value_counts(normalize=True).to_dict()
        rows.append({
            "Manager":um.get(str(uid),str(uid)),
            "Picks":len(g),
            "WR %":round(100*vc.get("WR",0)),
            "RB %":round(100*vc.get("RB",0)),
            "QB %":round(100*vc.get("QB",0)),
            "TE %":round(100*vc.get("TE",0)),
            "Avg age":round(g.age.mean(),1) if g.age.notna().any() else np.nan,
            "Avg market rank":round(g.market_rank.mean(),1) if g.market_rank.notna().any() else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["Picks","Avg market rank"],ascending=[False,True])

def league_position_pressure(picks, players, window=12):
    if not picks:
        return {"WR":1.0,"RB":1.0,"QB":1.0,"TE":1.0}
    z=pd.DataFrame(picks).tail(window).copy()
    if z.empty: return {"WR":1.0,"RB":1.0,"QB":1.0,"TE":1.0}
    z["player_id"]=z.player_id.astype(str)
    z=z.merge(players[["player_id","position"]],on="player_id",how="left")
    vc=z.position.value_counts().to_dict()
    total=max(len(z),1)
    # Raise probability for positions being actively drafted; cap to avoid overreaction.
    out={}
    baseline={"WR":0.38,"RB":0.30,"QB":0.17,"TE":0.15}
    for pos in ["WR","RB","QB","TE"]:
        observed=vc.get(pos,0)/total
        ratio=(observed+0.05)/(baseline[pos]+0.05)
        out[pos]=float(np.clip(ratio,0.70,1.35))
    return out


def top_decision_cards(avail, roster, n=5):
    if avail.empty:
        return pd.DataFrame()
    board=add_tiers(avail).copy()
    counts=roster.position.value_counts().to_dict() if len(roster) else {}

    rows=[]
    for _,r in board.head(max(n,10)).iterrows():
        pos=r.position
        reason=[]
        action="CONSIDER"

        if pos=="WR":
            reason.append("3WR + 2FLEX fit")
        elif pos=="RB":
            reason.append("RB scarcity / anchor upside")
        elif pos=="QB":
            reason.append("1QB discount applies")
        elif pos=="TE":
            reason.append("TE advantage only if price is right")

        if pd.notna(r.get("consensus_rank")):
            reason.append(f"Consensus #{int(r.consensus_rank)}")
        if pd.notna(r.get("model_rank")):
            reason.append(f"Our #{int(r.model_rank)}")
        if pd.notna(r.get("tier")):
            reason.append(f"Tier {int(r.tier)}")

        # simple action labels
        if len(rows)==0:
            action="TAKE"
        elif pd.notna(r.get("model_rank")) and pd.notna(r.get("consensus_rank")):
            edge=float(r.consensus_rank-r.model_rank)
            if edge>=5:
                action="VALUE"
            elif edge<=-6:
                action="MARKET > MODEL"
            else:
                action="STRONG ALT"

        rows.append({
            "Player":r["name"],
            "Pos":pos,
            "Action":action,
            "Consensus":int(r.consensus_rank) if pd.notna(r.get("consensus_rank")) else None,
            "Our Rank":int(r.model_rank) if pd.notna(r.get("model_rank")) else None,
            "Tier":int(r.tier) if pd.notna(r.get("tier")) else None,
            "Model Value":r.model_value,
            "Why":" • ".join(reason)
        })
        if len(rows)>=n:
            break
    return pd.DataFrame(rows)

st.title("🏈 Dynasty Draft Command Center v3.20")
st.caption("Stable local dynasty backbone + live Sleeper sync + real 2026 PPR projection layer")

with st.sidebar:
    username=st.text_input("Sleeper username")
    season=st.number_input("Season",2024,2030,2026)
    refresh=st.slider("Refresh seconds",5,30,7)
if not username: st.stop()

try:
    players=sleeper_df(c_players())
    d=dynasty_board()
    p=projections()
    players=attach(players,d,["market_rank","market_source"],True)
    players=attach(players,p,["season_fpts","proj_ppg","proj_source"],True)
    consensus_board=build_standalone_consensus(d)
    players=merge_consensus_into_players(players,consensus_board)
    players=score(players)
except Exception as e:
    st.error(f"Data load failed: {e}"); st.stop()

user=c_user(username.strip())
leagues=c_leagues(user["user_id"],int(season))
lm={f"{l.get('name','Unnamed')} — {l['league_id']}":l for l in leagues}
league=lm[st.sidebar.selectbox("League",list(lm))]
drafts=c_drafts(str(league["league_id"]))
dm={f"{(x.get('metadata') or {}).get('name') or x.get('type','Draft')} — {x['draft_id']}":x for x in drafts}
draft=dm[st.sidebar.selectbox("Draft",list(dm))]
picks=c_picks(str(draft["draft_id"]))
users=c_users(str(league["league_id"]))

teams=int((draft.get("settings") or {}).get("teams") or league.get("total_rosters") or 12)
rounds=int((draft.get("settings") or {}).get("rounds") or 21)
slot=(draft.get("draft_order") or {}).get(str(user["user_id"]))
slot=int(slot) if slot else st.sidebar.number_input("Your draft slot",1,teams,2)
current=len(picks)+1
r,pickin=rp(current,teams)
picked={str(x.get("player_id")) for x in picks if x.get("player_id")}
players["available"]=~players.player_id.isin(picked)
avail=players[players.available & players.rank_ok].copy()

# Mild roster-context adjustment.
myids=[str(x.get("player_id")) for x in picks if str(x.get("picked_by"))==str(user["user_id"])]
myroster=players[players.player_id.isin(myids)]
cnt=myroster.position.value_counts().to_dict()
def need(pos):
    mins={"WR":3,"RB":2,"TE":1,"QB":1}
    if cnt.get(pos,0)<mins[pos]:
        return {"WR":1.035,"RB":1.025,"TE":1.01,"QB":1.0}[pos]
    return 1.0
avail["draft_score"]=avail.model_value*[need(x) for x in avail.position]
avail.loc[(avail.position=="QB")&(avail.market_rank>20),"draft_score"]*=.92
avail=avail.sort_values(["draft_score","model_value"],ascending=False)

nxt=nextp(slot,current,teams,rounds)
a,b,c,d1,e=st.columns(5)
a.metric("League",league.get("name",""))
b.metric("Draft slot",slot)
c.metric("Current",f"{r}.{pickin:02d}")
d1.metric("Your next",nxt[0] if nxt else "—")
e.metric("Ranked players matched",int(players.rank_ok.sum()))


# ================= HOME COMMAND CENTER =================
st.markdown("---")
st.subheader("⚡ Draft Command Center")

home_on_clock=(slot_for(current,teams)==slot)
if home_on_clock:
    st.success(f"YOU ARE ON THE CLOCK — {r}.{pickin:02d} (overall {current})")
else:
    picks_to_you=(nxt[0]-current) if nxt else None
    if picks_to_you is not None:
        st.info(f"PREPARE — {picks_to_you} selection{'s' if picks_to_you!=1 else ''} before your pick.")
    else:
        st.info("PREPARE — waiting for your next pick.")

# Top 5 decisions
st.markdown("### Top 5 decisions")
home_cards=top_decision_cards(avail,myroster,5)
if len(home_cards):
    st.dataframe(home_cards,use_container_width=True,hide_index=True)
else:
    st.warning("No ranked players available.")

# Decision / tier summary
home_decision=None
if len(avail):
    if home_on_clock and nxt:
        home_decision=decision_summary(avail,nxt[0],current)
    else:
        home_decision=decision_summary(avail,None,current)

if home_decision:
    h1,h2,h3,h4=st.columns(4)
    h1.metric("Mode","ON CLOCK" if home_on_clock else "PREPARE")
    h2.metric("Best available",home_decision["top"]["name"])
    h3.metric("Tier players left",home_decision["tier_remaining"])
    h4.metric("Drop to next tier",f"{home_decision['tier_drop']:.1f}")

    if home_on_clock and home_decision["picks_until"] is not None:
        s1,s2,s3=st.columns(3)
        s1.metric("Following pick",nxt[0] if nxt else "—")
        s2.metric("Tier survival",f"{home_decision['chance_any_survives']:.0%}")
        s3.metric("Expected survivors",f"{home_decision['expected_survivors']:.1f}")

# Quick simulator snapshot
st.markdown("### Next-turn outlook")
if home_on_clock and nxt:
    home_follow=nxt[0]
    home_sim_picks=home_follow-current-1
elif not home_on_clock and nxt:
    upcoming=nxt[0]
    later=nextp(slot,upcoming,teams,rounds)
    home_follow=later[0] if later else None
    home_sim_picks=(home_follow-upcoming-1) if home_follow else None
else:
    home_follow=None
    home_sim_picks=None

if home_sim_picks is not None and home_sim_picks>0:
    home_sim_key=("home",int(home_sim_picks),1000,tuple(avail.head(40).player_id.tolist()))
    if st.session_state.get("home_sim_key")!=home_sim_key:
        sim_board_home=add_tiers(avail)
        st.session_state["home_sim_results"]=simulate_to_next_pick(
            sim_board_home,home_sim_picks,n_sims=1000,seed=7,
            pressure=league_position_pressure(picks,players)
        )
        st.session_state["home_sim_key"]=home_sim_key
    hs=st.session_state.get("home_sim_results")
    if hs is not None and len(hs):
        likely=hs[hs.survival_prob>=0.10].sort_values(["market_rank","survival_prob"],ascending=[True,False]).head(5)
        best=hs.sort_values(["best_survivor_prob","market_rank"],ascending=[False,True]).iloc[0]
        q1,q2,q3=st.columns(3)
        q1.metric("Following pick",home_follow if home_follow else "—")
        q2.metric("Most likely best survivor",best["name"])
        q3.metric("Best-survivor probability",f"{best['best_survivor_prob']:.0%}")
        if len(likely):
            lv=likely[["name","position","market_rank","survival_prob"]].copy()
            lv["Survival %"]=(100*lv.survival_prob).round().astype(int).astype(str)+"%"
            st.dataframe(lv[["name","position","market_rank","Survival %"]]
                         .rename(columns={"name":"Likely Available","position":"Pos","market_rank":"Market Rank"}),
                         use_container_width=True,hide_index=True)
else:
    st.caption("Simulator outlook will activate once the following turn can be identified.")

# Roster + room snapshot
left_home,right_home=st.columns(2)
with left_home:
    st.markdown("### Roster build")
    st.dataframe(roster_construction_status(myroster),use_container_width=True,hide_index=True)

with right_home:
    st.markdown("### Room pressure")
    pressure=league_position_pressure(picks,players)
    rp1,rp2,rp3,rp4=st.columns(4)
    rp1.metric("WR",f"{pressure['WR']:.2f}x")
    rp2.metric("RB",f"{pressure['RB']:.2f}x")
    rp3.metric("QB",f"{pressure['QB']:.2f}x")
    rp4.metric("TE",f"{pressure['TE']:.2f}x")
    hottest=max(pressure,key=pressure.get)
    coldest=min(pressure,key=pressure.get)
    st.caption(f"Hot: {hottest} • Cold: {coldest}")

st.markdown("---")
st.caption("Detailed tools remain below if you need deeper analysis.")

tabs=st.tabs(["🎯 War Room","🏆 Consensus","🎲 Draft Simulator","🔁 Trade Lab","🧠 Opponents","📊 Tiers & Availability","🧱 Roster Build","📋 Live Board","🔬 Data QA"])

with tabs[0]:
    user_on_clock=(slot_for(current,teams)==slot)

    # Before user's pick, show preparation mode. Once on the clock, evaluate
    # the following turn (e.g. 2.11 after 1.02) for TAKE/WAIT/TRADE DOWN logic.
    if user_on_clock:
        st.success(f"YOU ARE ON THE CLOCK — {r}.{pickin:02d}")
        decision=decision_summary(avail,nxt[0] if nxt else None,current)
    else:
        picks_to_user=(nxt[0]-current) if nxt else None
        st.info(
            f"PREPARE — {picks_to_user} selection{'s' if picks_to_user != 1 else ''} before your pick."
            if picks_to_user is not None else "PREPARE — waiting for your next pick."
        )
        # Do not use the user's immediate upcoming pick as a WAIT/TRADE horizon.
        # Show the best board option, but suppress action advice until user is on clock.
        decision=decision_summary(avail,None,current)

    if decision:
        top=decision["top"]
        x1,x2,x3,x4=st.columns(4)
        x1.metric("Recommendation",decision["recommendation"] if user_on_clock else "PREPARE")
        x2.metric("Best available now",top["name"])
        x3.metric("Tier",int(top["tier"]) if "tier" in top else "—")
        x4.metric("Tier players left",decision["tier_remaining"])
        if user_on_clock:
            st.write(decision["rationale"])
        else:
            st.write("Action advice will activate when Sleeper advances to your pick. The board below is your current preparation view.")
        if user_on_clock and decision["picks_until"] is not None and decision["picks_until"] > 0:
            d1,d2,d3,d4=st.columns(4)
            d1.metric("Selections until your following pick",decision["picks_until"])
            d2.metric("Chance this tier survives",f"{decision['chance_any_survives']:.0%}")
            d3.metric("Expected tier survivors",f"{decision['expected_survivors']:.1f}")
            d4.metric("Drop to next tier",f"{decision['tier_drop']:.1f}")
        elif not user_on_clock and nxt:
            st.caption(f"Your upcoming pick is overall {nxt[0]}. Once Sleeper reaches that pick, the app will evaluate the following turn automatically.")
        if decision["next_best"] is not None:
            st.caption(f"Next-tier best player: {decision['next_best']['name']}")

        run=position_run_alert(picks,players)
        if run:
            st.warning(f"Run alert: {run} Do not chase automatically; compare the next tier drop.")

        war_room_limit=st.selectbox("War Room players shown",[25,50,100,"All"],index=1,key="warroom_limit")
        war_room_df=decision["board"] if war_room_limit=="All" else decision["board"].head(int(war_room_limit))
        view=war_room_df[["name","position","team","age","consensus_rank","consensus_sources","consensus_confidence","tier","display_season_fpts","display_proj_ppg","projection_status","model_rank","consensus_edge","model_value"]]
        view.columns=["Player","Pos","Team","Age","Consensus","Sources","Confidence","Tier","2026 PPR Pts","PPG","Projection","Our Rank","Edge","Model Value"]
        st.dataframe(view,use_container_width=True,hide_index=True)

        if decision["same_tier"] is not None and len(decision["same_tier"])>1:
            names=", ".join(decision["same_tier"].name.tolist())
            st.caption(f"Same-tier alternatives: {names}")

with tabs[1]:
    st.subheader("Consensus dynasty board")
    st.caption("This table is built directly from ranking-source rows, then merged into Sleeper. It no longer depends on the live player dataframe to construct consensus.")

    cb=consensus_board.sort_values("consensus_rank").copy()
    if cb.attrs.get("fallback",False):
        st.warning("Consensus sanity fallback active: displaying stable RotoBaller order.")
    else:
        st.success("Consensus sanity check passed.")

    top10=cb.head(10)["name"].tolist()
    st.write("Consensus top 10:", ", ".join(top10))
    st.write(f"Consensus table rows: **{len(cb)}**")

    shown=st.selectbox("Players shown",[30,50,100,200,"All"],index=1,key="consensus_display")
    view=cb if shown=="All" else cb.head(int(shown))
    st.dataframe(
        view[["name","market_rank","pfn_rank","si_rank","ds_rank","fp_rank",
              "consensus_rank","consensus_sources","consensus_confidence","source_spread"]]
        .rename(columns={"name":"Player","market_rank":"RotoBaller","pfn_rank":"PFN","si_rank":"SI",
                         "ds_rank":"DraftSharks","fp_rank":"FantasyPros","consensus_rank":"Consensus",
                         "consensus_sources":"Sources","consensus_confidence":"Confidence","source_spread":"Spread"}),
        use_container_width=True,hide_index=True
    )

with tabs[2]:
    st.subheader("Monte Carlo availability simulator")

    user_on_clock=(slot_for(current,teams)==slot)
    if user_on_clock and nxt:
        following_pick=nxt[0]
        picks_to_sim=following_pick-current-1
        st.write(f"Simulating the **{picks_to_sim} opponent selections** between your current pick and your following pick at overall **{following_pick}**.")
    elif not user_on_clock and nxt:
        # Preparation mode: simulate from the user's upcoming pick to their following turn.
        upcoming=nxt[0]
        later=nextp(slot,upcoming,teams,rounds)
        # nextp sees upcoming as on-clock and returns following pick
        following_pick=later[0] if later else None
        picks_to_sim=(following_pick-upcoming-1) if following_pick else None
        st.write(
            f"Preparation simulation: assuming you pick at overall **{upcoming}**, "
            + (f"there are **{picks_to_sim} opponent selections** before your following pick at overall **{following_pick}**."
               if following_pick else "")
        )
    else:
        following_pick=None
        picks_to_sim=None

    sim_count=st.selectbox("Simulations",[1000,3000,5000],index=1,key="sim_count")

    if picks_to_sim is not None and picks_to_sim > 0:
        sim_board=add_tiers(avail)
        sim_key=(int(picks_to_sim),int(sim_count),tuple(sim_board.head(40).player_id.tolist()))
        if st.session_state.get("sim_key")!=sim_key:
            with st.spinner("Running draft simulation..."):
                st.session_state["sim_results"]=simulate_to_next_pick(
                    sim_board,picks_to_sim,n_sims=sim_count,seed=42,
                    pressure=league_position_pressure(picks,players)
                )
                st.session_state["sim_key"]=sim_key

        sim_df=st.session_state.get("sim_results")
        if sim_df is not None and len(sim_df):
            st.success("Simulation complete — results below.")
            s1,s2,s3=st.columns(3)
            tier1=sim_df[sim_df.tier==sim_df.tier.min()] if "tier" in sim_df.columns else sim_df.head(0)
            chance_t1=1-np.prod(1-tier1.survival_prob.values) if len(tier1) else 0
            s1.metric("Chance a current top-tier player survives",f"{chance_t1:.0%}")
            best_likely=sim_df.sort_values(["best_survivor_prob","market_rank"],ascending=[False,True]).iloc[0]
            s2.metric("Most likely best survivor",best_likely["name"])
            s3.metric("Probability best survivor",f"{best_likely['best_survivor_prob']:.0%}")

            st.markdown("**Likely players available at your following pick**")
            show=sim_df[sim_df.survival_prob>=0.10].sort_values(["market_rank","survival_prob"],ascending=[True,False]).head(20).copy()
            show["Survival %"]=(100*show.survival_prob).round(0).astype(int).astype(str)+"%"
            show["Best-survivor %"]=(100*show.best_survivor_prob).round(0).astype(int).astype(str)+"%"
            st.dataframe(
                show[["name","position","market_rank","tier","model_value","Survival %","Best-survivor %"]]
                .rename(columns={"name":"Player","position":"Pos","market_rank":"Market Rank","tier":"Tier","model_value":"Model Value"}),
                use_container_width=True,hide_index=True
            )

            if len(avail):
                current_choice=avail.iloc[0]
                pair=pairing_table(current_choice,sim_df,12)
                st.markdown(f"**Best projected pairings if you take {current_choice['name']} now**")
                pshow=pair.copy()
                pshow["Survival %"]=(100*pshow.survival_prob).round().astype(int).astype(str)+"%"
                st.dataframe(
                    pshow[["name","position","market_rank","tier","model_value","Survival %","pair_score"]]
                    .rename(columns={"name":"Following Pick Target","position":"Pos","market_rank":"Market Rank",
                                     "tier":"Tier","model_value":"Model Value","pair_score":"Pair Score"}),
                    use_container_width=True,hide_index=True
                )
        else:
            st.info("No simulation results yet.")
    else:
        st.info("Simulator will activate once the app can identify both your current/upcoming pick and the following turn.")


with tabs[3]:
    st.subheader("Trade Lab")
    st.caption("Compare startup picks, future rookie picks, and current players using the same dynasty model.")

    left,right=st.columns(2)
    with left:
        st.markdown("**You give**")
        give_startup=st.text_input("Startup overall picks (comma separated)",value="",key="give_startup")
        give_player=st.selectbox("Player you give",[""]+players[players.rank_ok].sort_values("model_value",ascending=False).name.tolist(),key="give_player")
        give_future_round=st.selectbox("Future rookie round",[0,1,2,3,4],index=0,key="give_fr")
        give_years=st.selectbox("Years out",[0,1,2,3],index=1,key="give_yrs")
        give_slot=st.selectbox("Expected rookie slot",["early","mid","late"],index=1,key="give_slot")

    with right:
        st.markdown("**You receive**")
        recv_startup=st.text_input("Startup overall picks (comma separated)",value="",key="recv_startup")
        recv_player=st.selectbox("Player you receive",[""]+players[players.rank_ok].sort_values("model_value",ascending=False).name.tolist(),key="recv_player")
        recv_future_round=st.selectbox("Future rookie round",[0,1,2,3,4],index=0,key="recv_fr")
        recv_years=st.selectbox("Years out",[0,1,2,3],index=1,key="recv_yrs")
        recv_slot=st.selectbox("Expected rookie slot",["early","mid","late"],index=1,key="recv_slot")

    give_val=sum(startup_pick_value(x) for x in parse_pick_list(give_startup))
    recv_val=sum(startup_pick_value(x) for x in parse_pick_list(recv_startup))

    pv,_=player_value_by_name(players,give_player)
    give_val+=pv
    pv,_=player_value_by_name(players,recv_player)
    recv_val+=pv

    if give_future_round:
        give_val+=future_rookie_value(give_future_round,give_years,give_slot)
    if recv_future_round:
        recv_val+=future_rookie_value(recv_future_round,recv_years,recv_slot)

    verdict,delta=trade_verdict(give_val,recv_val)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Give value",f"{give_val:.1f}")
    c2.metric("Receive value",f"{recv_val:.1f}")
    c3.metric("Net",f"{delta:+.1f}")
    c4.metric("Verdict",verdict)

    if verdict in {"ACCEPT","LEAN ACCEPT"}:
        st.success("Model likes your side of the deal.")
    elif verdict=="FAIR":
        st.warning("Close enough that tier/roster context should decide it.")
    else:
        st.error("Model does not like the price.")

with tabs[4]:
    st.subheader("Opponent tendencies")
    tend=manager_tendency_table(picks,players,users)
    if tend.empty:
        st.info("This will populate once the draft starts.")
    else:
        st.dataframe(tend,use_container_width=True,hide_index=True)

        pressure=league_position_pressure(picks,players)
        st.markdown("**Current room pressure (last 12 picks)**")
        pcols=st.columns(4)
        for col,pos in zip(pcols,["WR","RB","QB","TE"]):
            col.metric(pos,f"{pressure[pos]:.2f}x")

        # Simple room read.
        hottest=max(pressure,key=pressure.get)
        coldest=min(pressure,key=pressure.get)
        st.write(f"Current room read: **{hottest} is being drafted aggressively**; **{coldest} is relatively cold**.")
        st.caption("The Monte Carlo simulator now uses this live room pressure to tilt opponent pick probabilities.")


with tabs[5]:
    if avail.empty:
        st.info("No available ranked players.")
    else:
        tb=add_tiers(avail)
        next_overall=nxt[0] if nxt else None
        picks_until=(next_overall-current) if next_overall else None
        tier_limit=st.selectbox("Players shown",[50,100,200,"All"],index=3,key="tier_limit")
        tview=tb.copy() if tier_limit=="All" else tb.head(int(tier_limit)).copy()
        if picks_until and picks_until>0:
            tview["Chance available at your next pick"]=[
                availability_probability(row,picks_until) for _,row in tview.iterrows()
            ]
            tview["Chance available at your next pick"]=(100*tview["Chance available at your next pick"]).round().astype(int).astype(str)+"%"
        else:
            tview["Chance available at your next pick"]="—"
        tier_counts=tb.groupby("tier").size().rename("Players left").reset_index()
        st.dataframe(tier_counts.head(12),use_container_width=True,hide_index=True)
        st.dataframe(
            tview[["name","position","market_rank","tier","model_value","Chance available at your next pick"]]
            .rename(columns={"name":"Player","position":"Pos","market_rank":"Market Rank","tier":"Tier","model_value":"Model Value"}),
            use_container_width=True,hide_index=True
        )
        if picks_until and picks_until>0:
            st.caption(f"Availability is a model estimate based on market rank and {picks_until} selections until your next pick; it is not a guarantee.")

with tabs[6]:
    build=roster_construction_status(myroster)
    st.dataframe(build,use_container_width=True,hide_index=True)
    if len(myroster):
        ages=myroster.age.dropna()
        avg_age=ages.mean() if len(ages) else np.nan
        wr=myroster[myroster.position=="WR"]
        rb=myroster[myroster.position=="RB"]
        a1,a2,a3=st.columns(3)
        a1.metric("Rostered",len(myroster))
        a2.metric("Average age",f"{avg_age:.1f}" if pd.notna(avg_age) else "—")
        a3.metric("WR/RB share",f"{100*((len(wr)+len(rb))/len(myroster)):.0f}%")
        st.dataframe(
            myroster[["name","position","age","market_rank","model_value"]]
            .sort_values("model_value",ascending=False)
            .rename(columns={"name":"Player","position":"Pos","age":"Age","market_rank":"Market Rank","model_value":"Model Value"}),
            use_container_width=True,hide_index=True
        )
    else:
        st.info("Your startup roster is empty. This panel will update as Sleeper records your picks.")

with tabs[7]:
    if not picks: st.info("No picks yet.")
    else:
        z=pd.DataFrame(picks); z["player_id"]=z.player_id.astype(str)
        z=z.merge(players[["player_id","name","position","market_rank","model_value"]],on="player_id",how="left")
        um={str(u.get("user_id")):(u.get("display_name") or u.get("username") or str(u.get("user_id"))) for u in users}
        z["Manager"]=z.picked_by.astype(str).map(um).fillna(z.picked_by.astype(str))
        st.dataframe(z[["pick_no","name","position","Manager","market_rank","model_value"]],use_container_width=True,hide_index=True)

with tabs[8]:
    st.write(f"Dynasty rows matched to Sleeper: **{int(players.rank_ok.sum())}**")
    st.write(f"Players with exact 2026 PPR projection points: **{int(players.projection_exact.sum())}**")
    st.write(f"Ranked players using conservative estimated projection fallback: **{int((players.rank_ok & ~players.projection_exact).sum())}**")
    st.write(f"Dynasty data source: **{d.market_source.iloc[0] if len(d) else 'none'}**")
    q=st.text_input("Search player")
    if q:
        st.dataframe(players[players.name.str.contains(q,case=False,na=False)]
                     [["player_id","name","position","team","age","market_rank","market_source","season_fpts","proj_ppg","display_season_fpts","display_proj_ppg","projection_status","proj_source","model_value"]],
                     use_container_width=True,hide_index=True)

st.caption(f"Auto-refresh every {refresh}s. Sleeper is live; rankings/projections are cached.")
if st.button("Refresh all now"):
    st.cache_data.clear(); st.rerun()
time.sleep(refresh); st.rerun()
