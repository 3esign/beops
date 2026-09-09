import ssl, socket, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = os.path.join(ROOT, "data", "ca-bundle-windows.pem")
print("bundle:", b, os.path.exists(b), os.path.getsize(b) if os.path.exists(b) else 0)
ctx = ssl.create_default_context(cafile=b)
print("CA certs loaded:", len(ctx.get_ca_certs()))
for h in ("www.parking-servis.co.rs", "registar.ratel.rs", "www.putevi-srbije.rs", "opendata.stat.gov.rs"):
    try:
        s = ctx.wrap_socket(socket.create_connection((h, 443), 12), server_hostname=h)
        print(f"  OK  {h:32s} {s.version()}")
        s.close()
    except Exception as e:
        print(f"  ERR {h:32s} {type(e).__name__}: {str(e)[:80]}")
