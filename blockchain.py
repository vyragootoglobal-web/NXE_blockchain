""" Lumi node versions v1..v20

This single-file helper contains 20 versioned node implementations (as strings) and a helper write_versions(path='lumi_nodes') that will create a folder and write each version to its own python file (lumi_node_v01.py .. lumi_node_v20.py).

IMPORTANT: None of these files include private keys, real wallet addresses, or any device-specific information. They are intentionally minimal and educational, progressively adding features from "toy" single-file blockchain (v01) to deployable/production-ready scaffolding and handover notes (v20). Use them as a starting point — audit, test, and harden before any real network launch.

To export files from this canvas: run this script in a Python environment on your device:

python Lumi_nodes_v1_to_v20.py
# then from Python prompt or script:
from lumi_nodes_v1_to_v20 import write_versions
write_versions('lumi_nodes')

or simply import and call write_versions() to create the 20 files in ./lumi_nodes/

"""

V1 = r"""

lumi_node_v01.py

Minimal single-file blockchain: Block and Chain, in-memory only.

import hashlib import time

class Block: def init(self, index, previous_hash, timestamp, data, nonce=0): self.index = index self.previous_hash = previous_hash self.timestamp = timestamp self.data = data self.nonce = nonce self.hash = self.calc_hash()

def calc_hash(self):
    s = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

class Blockchain: def init(self): self.chain = [self.create_genesis_block()]

def create_genesis_block(self):
    return Block(0, "0", time.time(), "Genesis Block")

def latest_block(self):
    return self.chain[-1]

def add_block(self, data):
    prev = self.latest_block()
    block = Block(prev.index+1, prev.hash, time.time(), data)
    self.chain.append(block)
    return block

if name == 'main': bc = Blockchain() bc.add_block('first') for b in bc.chain: print(b.index, b.hash) """

V2 = r"""

lumi_node_v02.py

Add simple Proof-of-Work (adjustable difficulty)

import hashlib, time

class Block: def init(self, index, previous_hash, timestamp, data, nonce=0): self.index = index self.previous_hash = previous_hash self.timestamp = timestamp self.data = data self.nonce = nonce self.hash = self.calc_hash() def calc_hash(self): s = f"{self.index}{self.previous_hash}{self.timestamp}{self.data}{self.nonce}" return hashlib.sha256(s.encode()).hexdigest()

class PoWChain: def init(self, difficulty=3): self.chain = [self.genesis()] self.difficulty = difficulty def genesis(self): return Block(0, '0', time.time(), 'Genesis') def mine_block(self, data): prev = self.chain[-1] nonce = 0 while True: block = Block(prev.index+1, prev.hash, time.time(), data, nonce) if block.hash.startswith('0'*self.difficulty): self.chain.append(block) return block nonce += 1

if name == 'main': c = PoWChain(difficulty=3) print('Mining... (this may take a moment)') c.mine_block('tx1') for b in c.chain: print(b.index, b.hash) """

V3 = r"""

lumi_node_v03.py

Add a tiny REST API (Flask) so other peers can query the chain and submit blocks.

NOTE: Flask is optional; this is an example for local P2P testing only.

from flask import Flask, jsonify, request import threading import time import hashlib

app = Flask(name)

class Block: def init(self, index, prev_hash, timestamp, data, nonce=0): self.index=index; self.prev_hash=prev_hash; self.timestamp=timestamp self.data=data; self.nonce=nonce; self.hash=self.calc_hash() def calc_hash(self): return hashlib.sha256(f"{self.index}{self.prev_hash}{self.timestamp}{self.data}{self.nonce}".encode()).hexdigest()

class SimpleChain: def init(self): self.chain=[Block(0,'0',time.time(),'genesis')] def add_block(self, data): p=self.chain[-1] b=Block(p.index+1,p.hash,time.time(),data) self.chain.append(b); return b

CHAIN = SimpleChain()

@app.route('/chain', methods=['GET']) def get_chain(): return jsonify([b.dict for b in CHAIN.chain])

@app.route('/mine', methods=['POST']) def mine(): data = request.json.get('data') b = CHAIN.add_block(data) return jsonify({'index': b.index, 'hash': b.hash})

if name == 'main': app.run(port=5000) """

V4 = r"""

lumi_node_v04.py

Add peer discovery (simple peer list) and broadcast endpoints.

from flask import Flask, jsonify, request import requests, threading, time, hashlib

app = Flask(name) PEERS = set()

class Block: ... # same as v03 (omitted for brevity)

Minimal chain implementation

class Chain: def init(self): self.chain=[{'index':0,'prev_hash':'0','timestamp':time.time(),'data':'genesis','hash':'0'}] def add_block(self, data): prev=self.chain[-1]; idx=prev['index']+1 s=f"{idx}{prev['hash']}{time.time()}{data}0" h=hashlib.sha256(s.encode()).hexdigest() b={'index':idx,'prev_hash':prev['hash'],'timestamp':time.time(),'data':data,'hash':h} self.chain.append(b); return b

CHAIN=Chain()

@app.route('/peers', methods=['GET','POST']) def peers(): if request.method=='POST': p=request.json.get('peer'); PEERS.add(p); return jsonify({'peers':list(PEERS)}) return jsonify({'peers':list(PEERS)})

@app.route('/broadcast_block', methods=['POST']) def broadcast_block(): b=request.json for p in list(PEERS): try: requests.post(p+'/receive_block', json=b, timeout=1) except Exception: pass return jsonify({'sent_to':len(PEERS)})

@app.route('/receive_block', methods=['POST']) def receive_block(): b=request.json # naive accept CHAIN.chain.append(b); return jsonify({'ok':True})

if name=='main': app.run(port=5001) """

V5 = r"""

lumi_node_v05.py

Add transaction pool and simple broadcast for txs

Transactions are basic dicts: {'from': 'addr', 'to': 'addr', 'amount': 1}

from flask import Flask, jsonify, request import time, hashlib, requests

app=Flask(name) TX_POOL=[] CHAIN=[{'index':0,'hash':'0'}] PEERS=set()

@app.route('/tx', methods=['POST']) def add_tx(): tx=request.json; tx['timestamp']=time.time(); TX_POOL.append(tx) for p in PEERS: try: requests.post(p+'/tx', json=tx, timeout=1) except: pass return jsonify({'ok':True})

@app.route('/mine', methods=['POST']) def mine(): if not TX_POOL: return jsonify({'error':'no tx'}) data=str(TX_POOL.copy()); TX_POOL.clear() idx=CHAIN[-1]['index']+1 h=hashlib.sha256(f"{idx}{CHAIN[-1]['hash']}{time.time()}{data}".encode()).hexdigest() CHAIN.append({'index':idx,'hash':h,'data':data}); return jsonify({'index':idx,'hash':h})

if name=='main': app.run(port=5002) """

V6 = r"""

lumi_node_v06.py

Add a wallet module stub — NOTE: this version intentionally leaves key management to the operator.

Wallet code does NOT generate or store keys automatically here. Use external secure key storage.

Wallet API (stub): create address externally, then use this client to sign transactions offline.

Signing is left as an exercise: integrate with a hardware wallet or a secure key manager.

print('v06: wallet stubs included. DO NOT store private keys in these files.') """

V7 = r"""

lumi_node_v07.py

Separate wallet code and demonstrate how to keep keys off-device (instructions only).

README = ''' v07 notes:

Do NOT keep private keys in the repo.

Recommended: use a hardware wallet or a secure HSM, or a remote signing service.

For community-run nodes, provide 'validator' accounts from separate key-holding devices. ''' print(README) """


V8 = r"""

lumi_node_v08.py

Add Merkle tree utilities for block transaction root calculation (simplified)

import hashlib

def merkle_root(tx_list): if not tx_list: return hashlib.sha256(b'').hexdigest() leaves=[hashlib.sha256(str(tx).encode()).hexdigest() for tx in tx_list] while len(leaves)>1: nxt=[] for i in range(0,len(leaves),2): a=leaves[i] b=leaves[i+1] if i+1<len(leaves) else a nxt.append(hashlib.sha256((a+b).encode()).hexdigest()) leaves=nxt return leaves[0]

if name=='main': print('merkle root example:', merkle_root([{'a':1},{'b':2}])) """

V9 = r"""

lumi_node_v09.py

Better validation and block acceptance rules, minimal blockchain sync logic

import hashlib, time

class Chain: def init(self): self.chain=[{'index':0,'hash':'0'}] def valid_new_block(self, b, prev): # index + prev hash checks return b['prev_hash']==prev['hash'] and b['index']==prev['index']+1 def add_block(self, b): if self.valid_new_block(b, self.chain[-1]): self.chain.append(b); return True return False

Usage: receive candidate block, call add_block(b)

"""

V10 = r"""

lumi_node_v10.py

Add persistence (simple file-based) so node restart keeps chain state

import json, os

FNAME='chain_store.json'

def save_chain(chain): with open(FNAME,'w') as f: json.dump(chain,f)

def load_chain(): if not os.path.exists(FNAME): return [{'index':0,'hash':'0'}] with open(FNAME) as f: return json.load(f)

if name=='main': chain=load_chain(); print('loaded', len(chain), 'blocks') chain.append({'index':len(chain),'hash':'abc'}); save_chain(chain) """

V11 = r"""

lumi_node_v11.py

Add a clearer REST API, node status, and peers management (production advice included)

from flask import Flask, jsonify, request import json, os

app=Flask(name) CHAIN_FILE='chain.json' PEERS=set()

@app.route('/status') def status(): csize=0 if os.path.exists(CHAIN_FILE): with open(CHAIN_FILE) as f: c=json.load(f); csize=len(c) return jsonify({'blocks':csize,'peers':list(PEERS)})

production: run behind a reverse proxy, enable TLS, rate limit API, require auth for admin endpoints.

if name=='main': app.run(port=5003) """

V12 = r"""

lumi_node_v12.py

Add background miner thread (configurable) and graceful shutdown hooks

import threading, time

MINING=True

def miner_loop(): while MINING: print('simulate mining cycle...') time.sleep(5)

if name=='main': t=threading.Thread(target=miner_loop,daemon=True); t.start() try: while True: time.sleep(1) except KeyboardInterrupt: MINING=False; t.join() """

V13 = r"""

lumi_node_v13.py

Simple CLI wrapper to run node or run lightweight client

import argparse

parser=argparse.ArgumentParser() parser.add_argument('--mode', choices=['node','client'], default='node') args=parser.parse_args() if args.mode=='node': print('starting node...') else: print('running client...') """

V14 = r"""

lumi_node_v14.py

TLS and authentication notes (example placeholders) — DO NOT use self-signed certs for production.

CERT_NOTES='''

Use Certbot/Let's Encrypt for public nodes behind a domain.

Use mutual TLS for admin RPC endpoints where appropriate.

Keep private keys in HSM/hardware wallet; never in repo. ''' print(CERT_NOTES) """


V15 = r"""

lumi_node_v15.py

Encrypted snapshot/export utility (AES example using hashlib for key derivation; switch to cryptography lib)

import hashlib, json, base64

def derive_key(passphrase): return hashlib.sha256(passphrase.encode()).digest()

def encrypt_snapshot(chain_json_str, passphrase): key=derive_key(passphrase) # NOTE: placeholder XOR-based 'encryption' for example only. Replace with AES-GCM (cryptography lib) in prod. data=chain_json_str.encode() out=bytes([data[i]^key[i%len(key)] for i in range(len(data))]) return base64.b64encode(out).decode()

if name=='main': s=encrypt_snapshot('{"blocks":[]}','your-pass') print('snapshot (encrypted):', s[:60]) """

V16 = r"""

lumi_node_v16.py

Consensus abstraction: allow easy switch between PoW/PoS (PoS only scaffolded)

class Consensus: def init(self, mode='pow'): self.mode=mode def validate_block(self, block): if self.mode=='pow': # perform PoW validation return block.get('hash','').startswith('000') else: # PoS: check signature and stake (requires validator set) return True

if name=='main': print('Consensus scaffold ready') """

V17 = r"""

lumi_node_v17.py

Light-node mode: don't store full chain, only headers. Useful for mobile/community-run watchers.

class LightNode: def init(self): self.headers=[] def add_header(self, header): self.headers.append(header)

print('light node mode: stores headers only') """

V18 = r"""

lumi_node_v18.py

Dockerfile and systemd unit templates (strings) to help community run nodes reliably.

DOCKERFILE=''' FROM python:3.11-slim WORKDIR /app COPY . /app RUN pip install -r requirements.txt CMD ["python","lumi_node_v11.py"] ''' SYSTEMD_UNIT=''' [Unit] Description=Lumi Node After=network.target

[Service] User=lumi WorkingDirectory=/opt/lumi ExecStart=/usr/bin/python3 /opt/lumi/lumi_node_v11.py Restart=on-failure

[Install] WantedBy=multi-user.target ''' print('docker and systemd templates available') """

V19 = r"""

lumi_node_v19.py

Off-chain governance scaffolding: proposals, voting, and simple quorum rules stored as chain events.

class Governance: def init(self): self.proposals=[] def propose(self, title, description): p={'id':len(self.proposals)+1,'title':title,'description':description,'votes':{}} self.proposals.append(p); return p def vote(self, pid, voter, choice): p=self.proposals[pid-1]; p['votes'][voter]=choice; return p

print('governance scaffold ready') """

V20 = r"""

lumi_node_v20.py

Handover & audit readiness: contributor guide, checklist, and verification scripts (signing releases)

CONTRIBUTOR_GUIDE='''

How to build: requirements, python version

How to run tests: pytest

How to set up a local cluster: docker-compose example

How to join network as validator

Security: do NOT commit private keys; sign git tags with GPG ''' VERIFICATION_SCRIPT='''


simple example: verify file SHA256 vs published checksum

import hashlib

def sha256_file(path): h=hashlib.sha256() with open(path,'rb') as f: for chunk in iter(lambda: f.read(8192),b''): h.update(chunk) return h.hexdigest() ''' print('v20 includes handover docs and verification helpers') """

ALL_VERSIONS = [(i+1, globals()[f'V{str(i+1)}']) for i in range(20)]

import os

def write_versions(dest='lumi_nodes'): os.makedirs(dest, exist_ok=True) for i, code in ALL_VERSIONS: fn = os.path.join(dest, f'lumi_node_v{str(i).zfill(2)}.py') with open(fn,'w', encoding='utf-8') as f: f.write(code) print(f'Wrote {len(ALL_VERSIONS)} files to {os.path.abspath(dest)}')

if name=='main': write_versions()