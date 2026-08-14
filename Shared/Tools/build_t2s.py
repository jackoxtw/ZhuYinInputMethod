#!/usr/bin/env python3
import argparse,json,struct
from pathlib import Path
MAGIC=b'ZYT2S1\0\0'
HFMT='<8sIIIIQQQQQQ'
RFMT='<IIII'
HS=struct.calcsize(HFMT)
RS=struct.calcsize(RFMT)
def align8(b):
    while len(b)%8:b.append(0)
def put(b,data):align8(b);o=len(b);b.extend(data);return o
def build(payload,out):
    p=json.loads(Path(payload).read_text('utf-8'))
    cmap=sorted((ord(a),ord(b)) for a,b in zip(p['t2s_chars_trad'],p['t2s_chars_simp']))
    trad=struct.pack('<%dI'%len(cmap),*[a for a,b in cmap]); simp=struct.pack('<%dI'%len(cmap),*[b for a,b in cmap])
    phrases=[]
    for line in p['t2s_phrase_tsv'].splitlines():
        if '\t' not in line: continue
        a,b=line.split('\t',1); phrases.append((a,b))
    phrases.sort(key=lambda x:(-len(x[0].encode()),x[0]))
    pool=bytearray(); rec=[]
    for a,b in phrases:
        ao=len(pool); ab=a.encode(); pool.extend(ab); bo=len(pool); bb=b.encode(); pool.extend(bb); rec.append((ao,len(ab),bo,len(bb)))
    recb=b''.join(struct.pack(RFMT,*r) for r in rec)
    buf=bytearray(b'\0'*HS)
    to=put(buf,trad); so=put(buf,simp); ro=put(buf,recb); po=put(buf,pool); fs=len(buf)
    buf[:HS]=struct.pack(HFMT,MAGIC,1,len(cmap),len(rec),HS,fs,to,so,ro,po,len(pool))
    Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_bytes(buf)
    print(json.dumps({'output':out,'bytes':len(buf),'chars':len(cmap),'phrases':len(rec)},ensure_ascii=False))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('payload');ap.add_argument('output');a=ap.parse_args();build(a.payload,a.output)
