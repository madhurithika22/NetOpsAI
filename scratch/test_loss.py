import os
import sys
import subprocess

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.research_v2.testbed.topology import ResearchTopology

try:
    print("Creating topology...")
    ResearchTopology.create_topology()
    
    # 1. Baseline ping (20 probes)
    res_base = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-host-a", "ping", "-c", "20", "-i", "0.05", "10.0.3.10"], capture_output=True, text=True)
    print("Baseline Ping stdout:\n", "\n".join(res_base.stdout.splitlines()[-3:]))
    
    # 2. Inject fault
    print("\nInjecting tc netem delay 150ms loss 20%...")
    subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-router-1", "tc", "qdisc", "add", "dev", "veth-r1-r2", "root", "netem", "delay", "150ms", "loss", "20%"], check=True)
    
    # 3. Check qdisc counters
    qdisc_show = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-router-1", "tc", "-s", "qdisc", "show", "dev", "veth-r1-r2"], capture_output=True, text=True)
    print("\nQdisc stats:\n", qdisc_show.stdout)
    
    # 4. Probes with n=5
    p5 = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-host-a", "ping", "-c", "5", "-i", "0.2", "10.0.3.10"], capture_output=True, text=True)
    print("\nPing n=5:\n", "\n".join(p5.stdout.splitlines()[-3:]))
    
    # 5. Probes with n=50
    p50 = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-host-a", "ping", "-c", "50", "-i", "0.05", "10.0.3.10"], capture_output=True, text=True)
    print("\nPing n=50:\n", "\n".join(p50.stdout.splitlines()[-3:]))
    
    # 6. Check qdisc stats after pings
    qdisc_show_after = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-router-1", "tc", "-s", "qdisc", "show", "dev", "veth-r1-r2"], capture_output=True, text=True)
    print("\nQdisc stats after pings:\n", qdisc_show_after.stdout)
    
    # 7. Remove fault and verify recovery
    subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-router-1", "tc", "qdisc", "del", "dev", "veth-r1-r2", "root"], check=True)
    p_rec = subprocess.run(["sudo", "-n", "ip", "netns", "exec", "rns-host-a", "ping", "-c", "20", "-i", "0.05", "10.0.3.10"], capture_output=True, text=True)
    print("\nRecovery Ping stdout:\n", "\n".join(p_rec.stdout.splitlines()[-3:]))

finally:
    ResearchTopology.destroy_topology()
    print("\nCleanup done.")
