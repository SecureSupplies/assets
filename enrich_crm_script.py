#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,re,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import requests
PORTAL="https://login.securesupplies.us/"
E=json.loads(Path("factura_verified_enrichments.json").read_text(encoding="utf-8"))
R=Path("factura_enrichment_report.json");A=Path("factura_enrichment_audit.jsonl");S=Path("factura_zoho_schema.json")
class X(RuntimeError):pass
def now():return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def nt(v):return re.sub(r"[^a-z0-9]+","",str(v or "").lower())
def ck(v):
 w=re.findall(r"[a-z0-9]+",str(v or "").lower().replace("&"," and "));q={"incorporated","corporation","company","limited","holdings","llc","inc","corp","ltd","co"}
 while w and w[-1] in q:w.pop()
 return "".join(w)
def cl(v):return re.sub(r"\s+"," ",str(v or "")).strip()
def dom(v):
 t=cl(v).lower()
 if not t:return ""
 if "@" in t and not t.startswith("http"):t=t.rsplit("@",1)[-1]
 else:
  if "://" not in t:t="https://"+t
  u=urlparse(t);t=u.netloc or u.path.split("/")[0]
 t=t.split(":",1)[0]
 return t[4:] if t.startswith("www.") else t
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
def pcheck():
 try:
  r=requests.get(PORTAL,timeout=15,allow_redirects=True);return {"reachable":r.status_code<500,"status_code":r.status_code,"final_url":r.url}
 except Exception as e:return {"reachable":False,"error":str(e)[:300]}
class Z:
 def __init__(self):
  self.s=requests.Session();self.cid=os.getenv("ZOHO_CLIENT_ID","");self.cs=os.getenv("ZOHO_CLIENT_SECRET_VALUE") or os.getenv("ZOHO_CLIENT_SECRET","");self.rt=os.getenv("ZOHO_REFRESH_TOKEN_VALUE") or os.getenv("ZOHO_REFRESH_TOKEN","");self.acc=(os.getenv("ZOHO_ACCOUNTS_DOMAIN") or "https://accounts.zoho.com").rstrip("/");self.api=(os.getenv("ZOHO_API_DOMAIN") or "https://www.zohoapis.com").rstrip("/");self.can=bool(self.cid and self.cs and self.rt);self.t=self.ref() if self.can else os.getenv("ZOHO_ACCESS_TOKEN","")
  if not self.t:raise X("No Zoho OAuth credential configured")
 def ref(self):
  r=self.s.post(self.acc+"/oauth/v2/token",data={"refresh_token":self.rt,"client_id":self.cid,"client_secret":self.cs,"grant_type":"refresh_token"},timeout=30)
  if r.status_code>=400:raise X(f"OAuth refresh HTTP {r.status_code}: {r.text[:400]}")
  x=r.json();self.api=(x.get("api_domain") or self.api).rstrip("/")
  if not x.get("access_token"):raise X("OAuth refresh failed: zoho_error={} desc={} http={} rt_len={} rt_1000={} cid_len={} cid_1000={} cs_len={} host={}".format(x.get("error"),x.get("error_description"),r.status_code,len(self.rt),self.rt.startswith("1000."),len(self.cid),self.cid.startswith("1000."),len(self.cs),self.acc))
  return str(x["access_token"])
 def call(self,m,p,params=None,body=None):
  u=f"{self.api}/crm/v8/{p.lstrip('/')}";red=False
  for i in range(5):
   r=self.s.request(m,u,headers={"Authorization":f"Zoho-oauthtoken {self.t}","Content-Type":"application/json"},params=params,json=body,timeout=60)
   if r.status_code==401 and self.can and not red:self.t=self.ref();red=True;continue
   if r.status_code in {429,500,502,503,504} and i<4:time.sleep(min(2**(i+1),12));continue
   if r.status_code==204:return {}
   if r.status_code>=400:raise X(f"{m} {p} HTTP {r.status_code}: {r.text[:1200]}")
   return r.json() if r.text.strip() else {}
  raise X("API retry limit")
 def mods(self):return self.call("GET","settings/modules").get("modules",[])
 def fields(self,m):return self.call("GET","settings/fields",params={"module":m}).get("fields",[])
 def records(self,m,fs):
  o=[];pg=1;tok=None;fs=list(dict.fromkeys(x for x in fs if x))[:50]
  while 1:
   x=self.call("GET",m,params={**({"page_token":tok} if tok else {"page":pg}),"per_page":200,"fields":",".join(fs),"sort_by":"id","sort_order":"asc"});b=x.get("data",[]);o+=b;tok=(x.get("info") or {}).get("next_page_token")
   if not b or not (x.get("info") or {}).get("more_records"):return o
   pg+=1
 def update(self,m,rows):
  q={"submitted":0,"success":0,"failed":0,"details":[]}
  for i in range(0,len(rows),100):
   b=rows[i:i+100];x=self.call("PUT",m,body={"data":b,"trigger":[]});it=x.get("data",[]);q["submitted"]+=len(b);q["details"]+=it
   q["success"]+=sum(str(z.get("status","")).lower()=="success" for z in it);q["failed"]+=sum(str(z.get("status","")).lower()!="success" for z in it)+max(0,len(b)-len(it))
  return q
def mt(m):return {nt(m.get(k)) for k in ("api_name","module_name","plural_label","singular_label") if m.get(k)}
def module(ms,k):
 z=[]
 for m in ms:
  t=mt(m);s=0
  if k=="v":s=100 if t&{"vendorcontacts","vendorcontact"} else 90 if any("vendor" in x and "contact" in x for x in t) else 65 if t&{"vendors","vendor"} else 0
  else:s=100 if t&{"routes","route"} else 80 if any("route" in x for x in t) else 0
  if s:z.append((s,m))
 return max(z,key=lambda x:x[0])[1] if z else None
FA={"vn":["Vendor Name","Vendor Contact Name","Company Name","Account Name","Name","Vendor"],"p":["000 Products","000 Product","Primary Product","Main Product","Products","Product"],"st":["Street Address","Physical Address","Vendor Address","Mailing Street","Street","Address"],"a2":["Address Line 2","Address 2","Suite","Unit","Mailing Street 2"],"ci":["City","Mailing City","Vendor City"],"sa":["State","Mailing State","State Province","Vendor State"],"zi":["ZIP Code","Zip","Postal Code","Mailing Zip","Mailing Postal Code"],"co":["Country","Mailing Country","Vendor Country"],"ro":["Routes","Route","Assigned Route","Route Number","Route Name"],"ph":["Main Business Phone","Business Phone","Phone","Vendor Phone","Main Phone"],"fa":["Fax","Fax Number"],"em":["Business Email","Vendor Email","Email","Sales Email"],"we":["Official Website","Website","Vendor Website","URL"],"cn":["Contact Name","Primary Contact","Public Contact Name"],"ct":["Contact Title","Title","Job Title"],"li":["LinkedIn","LinkedIn Company Page"],"so":["Enrichment Source","Source URL","Source","Research Source"],"ve":["Verification Date","Verified At","Last Verified","Enriched Date"]}
LM={"000 Products":"p","Street Address":"st","Address Line 2":"a2","City":"ci","State":"sa","ZIP":"zi","Country":"co","Routes":"ro","Phone":"ph","Fax":"fa","Email":"em","Website":"we","Contact Name":"cn","Contact Title":"ct","LinkedIn":"li","Source":"so","Verification Date":"ve"}
def ft(f):return {nt(f.get(k)) for k in ("field_label","api_name","display_label") if f.get(k)}
def wr(f):
 if f.get("read_only") is True:return False
 o=f.get("operation_type") or {};return bool(f.get("api_name")) and not(isinstance(o,dict) and o.get("api_update") is False)
def fmap(fs,k):
 for l in FA[k]:
  t=nt(l);q=[f for f in fs if wr(f) and t in ft(f)]
  if q:return sorted(q,key=lambda f:nt(f.get("field_label"))!=t)[0]
 return None
def tv(v):
 if isinstance(v,str):return [v] if v.strip() else []
 if isinstance(v,list):return [s for x in v for s in tv(x)]
 if isinstance(v,dict):return [s for k in ("name","display_value","actual_value","value") for s in tv(v.get(k))]
 return []
def lm(f):
 for k in ("lookup","multiselectlookup","multi_select_lookup"):
  o=f.get(k)
  if isinstance(o,dict):
   m=o.get("module")
   if isinstance(m,dict) and m.get("api_name"):return str(m["api_name"])
   if o.get("api_name"):return str(o["api_name"])
 return ""
class I:
 def __init__(self,z):self.z=z;self.c={}
 def load(self,m):
  if m not in self.c:
   f=self.z.fields(m);self.c[m]=(f,self.z.records(m,[x["api_name"] for x in f if x.get("api_name")][:50]))
  return self.c[m]
 def eid(self,m,targets,route=0):
  _,rs=self.load(m);w={nt(x) for x in targets if x};q=[]
  for r in rs:
   ss=[s for v in r.values() for s in tv(v)]
   if not w&{nt(s) for s in ss}:continue
   nums=[int(a.group(1)) for s in ss if (a:=re.match(r"\s*(\d+)",s))];q.append((min(nums or [10**9]),str(r.get("id")),ss[0] if ss else ""))
  if not q:return None,"no exact CRM reference"
  q.sort(key=lambda x:x[0] if route else 0);return q[0][1],"exact CRM reference "+q[0][2]
 def product(self,f,v):
  d=str(f.get("data_type") or "").lower();ops={"Diesel Fuel":["Diesel Fuel","Diesel","ULSD"],"DEF":["DEF","Diesel Exhaust Fluid"],"Propane":["Propane","Propane / LPG","LPG"]}.get(v,[v])
  if "lookup" in d:
   m=lm(f)
   if not m:return None,"product lookup module missing"
   x,w=self.eid(m,ops);return (([{"id":x}] if "multi" in d else {"id":x}) if x else None),w
  if "picklist" in d:
   a=[p.get("actual_value",p.get("display_value")) for p in f.get("pick_list_values") or []]
   for x in ops:
    for y in a:
     if y is not None and nt(x)==nt(y):return ([y] if "multi" in d else y),"existing taxonomy "+str(y)
   return None,"product option missing"
  return v,"direct"
 def route(self,f,c,n,rm):
  d=str(f.get("data_type") or "").lower()
  if "lookup" in d:
   m=lm(f) or rm
   if not m:return None,"route lookup module missing"
   x,w=self.eid(m,[c,n],1);return (([{"id":x}] if "multi" in d else {"id":x}) if x else None),w
  if "picklist" in d:
   a=[p.get("actual_value",p.get("display_value")) for p in f.get("pick_list_values") or []]
   for x in (c,n):
    for y in a:
     if y is not None and nt(x)==nt(y):return ([y] if "multi" in d else y),"existing route "+str(y)
   return None,"route option missing"
  return c,"direct"
def sv(k,v):
 if v is None:return None
 if isinstance(v,str):
  v=cl(v)
  if not v:return None
  if k=="Contact Name" and nt(v) in {"ext","extension","na","none"}:return None
  if k=="Email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+",v):return None
  if k in {"Website","LinkedIn","Source"} and not v.lower().startswith(("http://","https://")):return None
  if k=="Country" and v!="United States":return None
 return v
def eq(a,b):
 if isinstance(a,dict) and isinstance(b,dict):return str(a.get("id",""))==str(b.get("id",""))
 if isinstance(a,list) and isinstance(b,list):
  x=sorted(str(z.get("id")) for z in a if isinstance(z,dict) and z.get("id"));y=sorted(str(z.get("id")) for z in b if isinstance(z,dict) and z.get("id"))
  if x or y:return x==y
 return nt(a)==nt(b)
def match(r,na,e,f):
 n=tv(r.get(na))
 if not n or ck(n[0]) not in {ck(x) for x in e["a"]}:return False
 ex=dom(e["d"].get("Website") or e["d"].get("Email"));ds=set()
 for k in ("we","em"):
  x=f.get(k)
  if x:ds|={dom(v) for v in tv(r.get(x["api_name"])) if dom(v)}
 if ex and ds and ex not in ds:return False
 if e["n"]=="American Energy / FuelOilNow.com" and ck(n[0])=="americanenergy":
  ci=cl(r.get(f["ci"]["api_name"])) if f.get("ci") else "";sa=cl(r.get(f["sa"]["api_name"])) if f.get("sa") else ""
  if ex not in ds and not(nt(ci)==nt(e["d"]["City"]) and nt(sa)==nt(e["d"]["State"])):return False
 return True
def run(mode,limit):
 z=Z();ms=z.mods();vm=module(ms,"v");rm=module(ms,"r")
 if not vm:raise X("Vendor Contacts module not found")
 va=str(vm["api_name"]);ra=str(rm["api_name"]) if rm else "";fs=z.fields(va);f={k:fmap(fs,k) for k in FA}
 if not f["vn"]:raise X("Vendor name field not found")
 na=str(f["vn"]["api_name"]);rec=z.records(va,["id",na]+[str(x["api_name"]) for x in f.values() if x]);ix=I(z);rows=[];au=[];c=Counter();ma=set()
 for r in rec:
  q=[e for e in E if match(r,na,e,f)]
  if not q:continue
  if len(q)!=1:au.append({"status":"ambiguous","record_id":r.get("id"),"matches":[x["n"] for x in q]});c["ambiguous"]+=1;continue
  e=q[0];ma.add(e["n"]);u={"id":r["id"]};ch=[];sk=[]
  for k in ["000 Products","Street Address","Address Line 2","City","State","ZIP","Country","Routes","Phone","Fax","Email","Website","Contact Name","Contact Title","LinkedIn","Source","Verification Date"]:
   if k not in e["s"]:continue
   v=sv(k,e["d"].get(k))
   if v is None:continue
   ff=f.get(LM[k])
   if not ff:sk.append({"field":k,"reason":"field not found"});continue
   d=str(ff.get("data_type") or "").lower();cv=v;why="direct"
   if k=="000 Products":cv,why=ix.product(ff,str(v))
   elif k=="Routes":cv,why=ix.route(ff,str(v),str(e["d"].get("Route Name") or ""),ra)
   elif "date" in d:cv=str(v)[:10]
   elif "multiselectpicklist" in d and not isinstance(v,list):cv=[v]
   elif k=="Source" and "picklist" in d:cv=None;why="source picklist unsafe"
   if cv is None:sk.append({"field":k,"reason":why});continue
   api=str(ff["api_name"])
   if eq(r.get(api),cv):c["already_current"]+=1;continue
   u[api]=cv;ch.append({"field":k,"api":api,"old":r.get(api),"new":cv,"source":e["d"].get("Source"),"conversion":why})
  name=tv(r.get(na))[0] if tv(r.get(na)) else ""
  if len(u)==1:au.append({"status":"no changes","record_id":r["id"],"record_name":name,"canonical":e["n"],"skips":sk});c["no_changes"]+=1;continue
  if limit and len(rows)>=limit:c["limit"]+=1;continue
  rows.append(u);au.append({"status":"prepared","record_id":r["id"],"record_name":name,"canonical":e["n"],"changes":ch,"skips":sk});c["records"]+=1;c["fields"]+=len(ch)
 res={"submitted":0,"success":0,"failed":0,"details":[]}
 if mode=="apply" and rows:res=z.update(va,rows)
 with A.open("w",encoding="utf-8") as h:
  for x in au:h.write(json.dumps(x,ensure_ascii=False,default=str)+"\n")
 dump(S,{"vendor_module":vm,"routes_module":rm,"fields":{k:(v and {"label":v.get("field_label"),"api":v.get("api_name"),"type":v.get("data_type")}) for k,v in f.items()}})
 return {"generated_at":now(),"mode":mode,"portal":pcheck(),"vendor_module":va,"routes_module":ra or None,"records_scanned":len(rec),"staged_vendors":len(E),"matched_vendors":len(ma),"unmatched":sorted({x["n"] for x in E}-ma),"records_prepared":len(rows),"counters":dict(c),"apply_result":res}
def test():
 assert ck("J.T. Horn Oil Co., Inc.")==ck("JT Horn Oil")
 assert dom("sales@suncoastresources.com")=="suncoastresources.com"
 assert len(E)==17 and sum(x["d"]["000 Products"]=="Diesel Fuel" for x in E)==15
 print("FACTURA verified enrichment self-test passed")
def main():
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["audit","apply"],default=os.getenv("FACTURA_ENRICH_MODE","audit"));p.add_argument("--max-updates",type=int,default=100);p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:test();return 0
 x={"started_at":now(),"status":"started","mode":a.mode}
 try:x.update(run(a.mode,a.max_updates));x["status"]="completed" if x["apply_result"]["failed"]==0 else "completed_with_errors";x["finished_at"]=now();dump(R,x);print(json.dumps(x,indent=2,ensure_ascii=False,default=str));return 0 if x["apply_result"]["failed"]==0 else 4
 except Exception as e:x.update({"status":"failed","error":str(e),"finished_at":now(),"portal":pcheck()});dump(R,x);print(json.dumps(x,indent=2),file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
