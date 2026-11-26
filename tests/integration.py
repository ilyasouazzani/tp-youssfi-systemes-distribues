from pathlib import Path
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
from threading import Thread
import time

root = Path(__file__).resolve().parents[1]
logdir = root / "target" / "verification"
logdir.mkdir(parents=True, exist_ok=True)
processes = []
files = []
model_calls = []
tool_checked = False

def http(port, path, payload=None):
    conn = HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request("GET" if payload is None else "POST", path,
                     None if payload is None else json.dumps(payload),
                     {"Content-Type":"application/json"})
        with conn.getresponse() as r:
            return r.status, r.read().decode()
    finally:
        conn.close()

class Model(BaseHTTPRequestHandler):
    def do_POST(self):
        global tool_checked
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            chunks = []
            while size := int(self.rfile.readline().split(b";", 1)[0], 16):
                chunks.append(self.rfile.read(size))
                self.rfile.read(2)
            body = b"".join(chunks)
        else:
            body = self.rfile.read(int(self.headers["Content-Length"]))
        payload = json.loads(body)
        model_calls.append(self.path)
        assert self.path == "/v1/chat/completions"
        messages = payload["messages"]
        results = [m for m in messages if m["role"] == "tool"]
        if results:
            assert "ACC-001" in results[-1]["content"] and "1200" in results[-1]["content"], results
            tool_checked = True
            response = {"role":"assistant","content":"Le compte fictif ACC-001 a un solde de 1200."}
            finish = "stop"
        else:
            name = next(t["function"]["name"] for t in payload["tools"] if t["function"]["name"].endswith("find_account"))
            response = {"role":"assistant","content":None,"tool_calls":[{"id":"call_demo",
                "type":"function","function":{"name":name,"arguments":'{"id":"ACC-001"}'}}]}
            finish = "tool_calls"
        result = json.dumps({"id":"chatcmpl-demo","object":"chat.completion","model":"test-local",
            "created":1,"choices":[{"index":0,"message":response,"finish_reason":finish}],
            "usage":{"prompt_tokens":5,"completion_tokens":5,"total_tokens":10}}).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(result)))
        self.end_headers()
        self.wfile.write(result)

def launch(module, env=None, options=()):
    filename = root/module/"target"/f"{module}-1.0.0.jar"
    handle = (logdir/f"{module}.log").open("wb")
    files.append(handle)
    p = subprocess.Popen(["java","-Xms32m","-Xmx220m","-jar",str(filename),*options],
        stdout=handle,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    processes.append(p)
    return p

def wait_for(port, path, check, seconds=120):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        try:
            status, value=http(port,path)
            if check(status,value):
                return
        except OSError:
            pass
        time.sleep(2)
    raise RuntimeError(f"Service non prêt sur {port}{path}; consulter {logdir}")

server = ThreadingHTTPServer(("127.0.0.1",0),Model)
Thread(target=server.serve_forever,daemon=True).start()
try:
    launch("discovery")
    wait_for(8761,"/",lambda status,v:status==200)
    customer=launch("customer-service", options=("--eureka.client.initial-instance-info-replication-interval-seconds=2",))
    launch("ebank-service",options=("--eureka.client.initial-instance-info-replication-interval-seconds=2",
                                  "--eureka.client.registry-fetch-interval-seconds=5"))
    launch("gateway",options=("--eureka.client.registry-fetch-interval-seconds=5",
                              "--spring.cloud.loadbalancer.cache.ttl=2s"))
    wait_for(8080,"/customers",lambda status,v:status==200 and "Client Démo" in v)
    wait_for(8080,"/accounts/ACC-001",lambda status,v:status==200 and json.loads(v)["customerAvailable"])
    assert http(8080,"/accounts/INCONNU")[0] == 404
    for port in (8081,8082):
        assert http(port,"/v3/api-docs")[0] == 200
        assert http(port,"/swagger-ui/index.html")[0] == 200
    print("OK REST : Eureka, Gateway, Feign, compte enrichi, 404 et Swagger UI.",flush=True)
    launch("bank-mcp")
    wait_for(8084,"/health-check-not-a-route",lambda status,v:status==404)
    launch("bank-assistant",dict(os.environ,OPENAI_API_KEY="test-local",
                                BANK_MODEL_BASE_URL=f"http://127.0.0.1:{server.server_port}",BANK_MODEL="test-local"), ("--spring.ai.retry.max-attempts=1",))
    wait_for(8085,"/api/mcp/tools",lambda status,v:status==200 and "find_account" in v)
    status,value=http(8085,"/api/mcp/accounts/ACC-001")
    assert status==200 and "1200" in value,(status,value)
    print("OK MCP : découverte réelle des outils et consultation réelle du compte via MCP.",flush=True)
    status,value=http(8085,"/api/chat",{"question":"Quel est le solde d’ACC-001 ?"})
    assert status==200 and "1200" in value and tool_checked,(status,value,model_calls)
    assert http(8085,"/api/chat",{"question":"  "})[0]==400
    print("OK Chatbot REST : décision du modèle simulée, appel MCP et données des services réels.",flush=True)
    customer.terminate()
    customer.wait(timeout=12)
    status,value=http(8082,"/accounts/ACC-001")
    assert status==200 and json.loads(value)["customerAvailable"] is False,(status,value)
    print("OK Résilience : compte accessible avec données client indisponibles.",flush=True)
finally:
    for proc in reversed(processes):
        if proc.poll() is None:
            proc.terminate()
    for proc in processes:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    for f in files:
        f.close()
    server.shutdown()
    server.server_close()
