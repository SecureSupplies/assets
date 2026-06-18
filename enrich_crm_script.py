import os,json,re,base64,hashlib,requests
from pathlib import Path
from nacl.public import PrivateKey
O=Path('zoho_preflight_result.json');P=Path('zoho_import_public.key')
def c(v):return re.sub(r'\s+',' ',str(v or '')).strip()
def n(v):return ' '.join(re.sub(r'[^a-z0-9]+',' ',c(v).lower()).split())
def save(x):O.write_text(json.dumps(x,indent=2),encoding='utf-8');print(json.dumps(x,indent=2))
x={'status':'started'}
try:
 cid=c(os.getenv('ZOHO_CLIENT_ID'));cs=c(os.getenv('ZOHO_CLIENT_SECRET'));rt=c(os.getenv('ZOHO_REFRESH_TOKEN'));at=c(os.getenv('ZOHO_ACCESS_TOKEN'))
 mat='|'.join((cid,cs,rt)) if cid and cs and rt else at
 if not mat:raise RuntimeError('No Zoho OAuth secret configured')
 key=PrivateKey(hashlib.blake2b(mat.encode(),digest_size=32,person=b'SSZOHO20260618').digest())
 P.write_text(base64.b64encode(bytes(key.public_key)).decode(),encoding='ascii')
 api=c(os.getenv('ZOHO_API_DOMAIN')) or 'https://www.zohoapis.com';method='access_token'
 if cid and cs and rt:
  acc=c(os.getenv('ZOHO_ACCOUNTS_DOMAIN')) or 'https://accounts.zoho.com';r=requests.post(acc.rstrip('/')+'/oauth/v2/token',data={'refresh_token':rt,'client_id':cid,'client_secret':cs,'grant_type':'refresh_token'},timeout=45)
  if r.status_code>=400:raise RuntimeError('OAuth refresh '+str(r.status_code)+': '+r.text[:400])
  q=r.json();at=c(q.get('access_token'));api=c(q.get('api_domain')) or api;method='refresh_oauth'
 if not at:raise RuntimeError('No access token available')
 h={'Authorization':'Zoho-oauthtoken '+at}
 def g(p,**k):
  r=requests.get(api.rstrip('/')+'/crm/v8/'+p,headers=h,params=k,timeout=60)
  if r.status_code>=400:raise RuntimeError(p+' '+str(r.status_code)+': '+r.text[:500])
  return r.json() if r.text.strip() else {}
 f=g('settings/fields',module='Leads').get('fields') or [];l=g('settings/layouts',module='Leads').get('layouts') or []
 try:v=g('settings/custom_views',module='Leads').get('custom_views') or []
 except Exception:v=[]
 t=n('STEP 1- LEADS - START')
 lm=[{'id':c(z.get('id')),'name':c(z.get('name') or z.get('display_label'))} for z in l if n(z.get('name') or z.get('display_label'))==t]
 vm=[{'id':c(z.get('id')),'name':c(z.get('name') or z.get('display_value'))} for z in v if n(z.get('name') or z.get('display_value'))==t]
 x={'status':'ready','auth_method':method,'key_source':'refresh_oauth' if cid and cs and rt else 'access_token','lead_fields':len(f),'layout_matches':lm,'view_matches':vm}
 save(x)
except Exception as e:x={'status':'failed','error':c(e)[:2000]};save(x);raise
