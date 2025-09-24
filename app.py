# app.py
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3, math
from typing import Optional, List
app = FastAPI(title="Prioridad Black - MVP")

def db():
    con = sqlite3.connect("mvp.db")
    con.row_factory = sqlite3.Row
    return con

# --- bootstrap ---
with db() as con:
    con.executescript("""
    CREATE TABLE IF NOT EXISTS customers (
      rut TEXT PRIMARY KEY, name TEXT, tier TEXT, address TEXT, lat REAL, lon REAL
    );
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rut TEXT NOT NULL, order_date TEXT NOT NULL,
      window_start TEXT, window_end TEXT, weight REAL, volume REAL,
      status TEXT DEFAULT 'PENDING',
      FOREIGN KEY(rut) REFERENCES customers(rut)
    );
    CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);
    """)
    con.commit()

class Customer(BaseModel):
    rut:str; name:str; tier:str; address:Optional[str]=None; lat:float; lon:float

class Order(BaseModel):
    rut:str; order_date:str; window_start:Optional[str]=None; window_end:Optional[str]=None
    weight:Optional[float]=None; volume:Optional[float]=None

@app.get("/health")
def health(): return {"status":"ok"}

@app.post("/config")
def set_config(payload:dict=Body(...)):
    with db() as con:
        for k,v in payload.items():
            con.execute("INSERT INTO config(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?",(k,str(v),str(v)))
        con.commit()
    return {"ok":True}

@app.post("/customers")
def upsert_customer(c:Customer):
    with db() as con:
        con.execute("""INSERT INTO customers(rut,name,tier,address,lat,lon)
                       VALUES(?,?,?,?,?,?)
                       ON CONFLICT(rut) DO UPDATE SET name=excluded.name,tier=excluded.tier,
                         address=excluded.address,lat=excluded.lat,lon=excluded.lon""",
                    (c.rut,c.name,c.tier,c.address,c.lat,c.lon))
        con.commit()
    return {"ok":True}

@app.post("/orders")
def create_order(o:Order):
    with db() as con:
        con.execute("""INSERT INTO orders(rut,order_date,window_start,window_end,weight,volume)
                       VALUES(?,?,?,?,?,?)""",
                    (o.rut,o.order_date,o.window_start,o.window_end,o.weight,o.volume))
        con.commit()
    return {"ok":True}

@app.get("/orders")
def list_orders(date:str):
    with db() as con:
        cur = con.execute("""SELECT o.*, c.tier, c.lat, c.lon FROM orders o
                             JOIN customers c USING(rut)
                             WHERE o.order_date=?""",(date,))
        return [dict(r) for r in cur.fetchall()]

def haversine(lat1, lon1, lat2, lon2):
    R=6371
    p1=math.radians(lat1); p2=math.radians(lat2)
    dlat=math.radians(lat2-lat1); dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def nearest_neighbor(depot, stops):
    seq=[]; cur=depot; pending=stops[:]
    while pending:
        nxt=min(pending, key=lambda s: haversine(cur["lat"],cur["lon"],s["lat"],s["lon"]))
        seq.append(nxt); pending.remove(nxt); cur=nxt
    return seq

@app.get("/routes")
def build_route(date:str):
    with db() as con:
        depot_lat=float(con.execute("SELECT value FROM config WHERE key='depot_lat'").fetchone()["value"])
        depot_lon=float(con.execute("SELECT value FROM config WHERE key='depot_lon'").fetchone()["value"])
        depot={"lat":depot_lat,"lon":depot_lon}

        rows = con.execute("""SELECT o.id, o.rut, c.tier, c.lat, c.lon, o.window_start, o.window_end
                              FROM orders o JOIN customers c USING(rut)
                              WHERE o.order_date=?""",(date,)).fetchall()
        blacks=[dict(r) for r in rows if r["tier"]=="BLACK"]
        others=[dict(r) for r in rows if r["tier"]!="BLACK"]

        seq_black = nearest_neighbor(depot, blacks) if blacks else []
        start_for_others = seq_black[-1] if seq_black else depot
        seq_others = nearest_neighbor(start_for_others, others) if others else []

        sequence=[]
        for r in seq_black+seq_others:
            tag = "BLACK" if r["tier"]=="BLACK" else r["tier"]
            sequence.append({"stop":tag,"rut":r["rut"],"order_id":r["id"]})

        # KPIs muy básicos para demo:
        total_dist=0.0; cur=depot
        for r in seq_black+seq_others:
            total_dist += haversine(cur["lat"],cur["lon"],r["lat"],r["lon"])
            cur={"lat":r["lat"],"lon":r["lon"]}

        return JSONResponse({
            "depot": depot,
            "prioritized": True,
            "sequence": sequence,
            "kpis":{"total_distance_km": round(total_dist,1)}
        })
@app.post("/seed")
def seed():
    with db() as con:
        # Configurar depot
        con.execute("INSERT INTO config(key,value) VALUES('depot_lat',?) ON CONFLICT(key) DO UPDATE SET value=?",
            (-33.518, -33.518))
        con.execute("INSERT INTO config(key,value) VALUES('depot_lon',?) ON CONFLICT(key) DO UPDATE SET value=?",
            (-70.71749, -70.71749))


        # Crear clientes
        customers = [
            ("11.111.111-1","Cliente A Black","BLACK","A",-33.44,-70.65),
            ("15.555.555-5","Cliente B Black","BLACK","B",-33.45,-70.62),
            ("9.999.999-9","Cliente C Pro","PRO","C",-33.49,-70.60),
            ("7.777.777-7","Cliente D Regular","REGULAR","D",-33.50,-70.67)
        ]
        for c in customers:
            con.execute("""INSERT INTO customers(rut,name,tier,address,lat,lon)
                           VALUES(?,?,?,?,?,?)
                           ON CONFLICT(rut) DO UPDATE SET
                           name=excluded.name,tier=excluded.tier,address=excluded.address,
                           lat=excluded.lat,lon=excluded.lon""", c)

        # Crear pedidos (usa la fecha que quieras mostrar en demo)
        date = "2025-09-24"
        orders = [
            ("11.111.111-1", date, "09:00", "12:00", 10, 0.3),
            ("15.555.555-5", date, "10:00", "13:00", 5, 0.2),
            ("9.999.999-9",  date, None,   None,     8,  0.25),
            ("7.777.777-7",  date, None,   None,     12, 0.4),
        ]
        for o in orders:
            con.execute("""INSERT INTO orders(rut,order_date,window_start,window_end,weight,volume)
                           VALUES(?,?,?,?,?,?)""", o)

        con.commit()

    return {"ok": True, "hint": "Datos cargados, ahora prueba GET /routes?date=2025-09-24"}
