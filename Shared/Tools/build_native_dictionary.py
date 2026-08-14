#!/usr/bin/env python3
import argparse, base64, json, struct
from pathlib import Path

MAGIC=b'ZYDICT1\0'
FMT='<8sIIIIII' + 'Q'*15
HEADER_SIZE=struct.calcsize(FMT)

def dec(s): return base64.b64decode(s)
def align8(buf):
    while len(buf)%8: buf.append(0)

def put(buf,data):
    align8(buf); off=len(buf); buf.extend(data); return off

def u32s(vals): return struct.pack('<%dI'%len(vals),*vals)

def build(payload_path,out_path):
    p=json.loads(Path(payload_path).read_text('utf-8'))
    word_pool=dec(p['word_pool_b64'])
    word_offsets=dec(p['word_offsets_b64'])
    pron_offsets=dec(p['pron_offsets_b64'])
    syllable_ids=dec(p['syllable_ids_b64'])
    weights=dec(p['weights_b64'])
    bucket_offsets=dec(p['bucket_offsets_b64'])
    bucket_word_ids=dec(p['bucket_word_ids_b64'])
    sylls=p['syllable_table']
    sp=bytearray(); so=[0]
    for s in sylls:
        sp.extend(s.encode('utf-8')); so.append(len(sp))
    syllable_offsets=u32s(so)
    bucket_symbols=u32s([ord(ch) for ch in p['bucket_symbols']])

    buf=bytearray(b'\0'*HEADER_SIZE)
    word_pool_off=put(buf,word_pool); word_pool_size=len(word_pool)
    word_offsets_off=put(buf,word_offsets)
    pron_offsets_off=put(buf,pron_offsets)
    syllable_ids_off=put(buf,syllable_ids); syllable_ids_count=len(syllable_ids)//2
    weights_off=put(buf,weights)
    syllable_pool_off=put(buf,sp); syllable_pool_size=len(sp)
    syllable_offsets_off=put(buf,syllable_offsets)
    bucket_symbols_off=put(buf,bucket_symbols)
    bucket_offsets_off=put(buf,bucket_offsets)
    bucket_word_ids_off=put(buf,bucket_word_ids); bucket_word_ids_count=len(bucket_word_ids)//4
    file_size=len(buf)
    header=struct.pack(FMT,
        MAGIC,1,HEADER_SIZE,p['word_count'],p['indexed_word_count'],len(sylls),len(p['bucket_symbols']),
        file_size,
        word_pool_off,word_pool_size,
        word_offsets_off,pron_offsets_off,
        syllable_ids_off,syllable_ids_count,
        weights_off,
        syllable_pool_off,syllable_pool_size,
        syllable_offsets_off,
        bucket_symbols_off,bucket_offsets_off,bucket_word_ids_off,bucket_word_ids_count)
    assert len(header)==HEADER_SIZE
    buf[:HEADER_SIZE]=header
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    Path(out_path).write_bytes(buf)
    print(json.dumps({'output':str(out_path),'bytes':len(buf),'word_count':p['word_count'],'syllables':len(sylls),'buckets':len(p['bucket_symbols'])},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('payload'); ap.add_argument('output'); a=ap.parse_args(); build(a.payload,a.output)
