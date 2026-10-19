from app.ceso.service import ceso_service
from app.ceso.provider import (
    SimulatedTelemetryProvider,
    LinuxTestbedTelemetryProvider,
    parse_ping_output,
    parse_ip_link_stats
)

def test_parse_ping_output_ubuntu_live_scenarios():
    # 1. Live Ubuntu scenario reported by user: 19 of 20 packets received (5% loss, 145.363ms RTT)
    ping_ubuntu_5_loss = """
PING 10.0.2.2 (10.0.2.2) 56(84) bytes of data.
64 bytes from 10.0.2.2: icmp_seq=1 ttl=64 time=145.2 ms
64 bytes from 10.0.2.2: icmp_seq=2 ttl=64 time=145.8 ms
64 bytes from 10.0.2.2: icmp_seq=3 ttl=64 time=145.5 ms
64 bytes from 10.0.2.2: icmp_seq=20 ttl=64 time=145.4 ms

--- 10.0.2.2 ping statistics ---
20 packets transmitted, 19 received, 5% packet loss, time 19041ms
rtt min/avg/max/mdev = 144.981/145.363/146.120/0.250 ms
"""
    rtt, loss = parse_ping_output(ping_ubuntu_5_loss, returncode=0)
    assert rtt == 145.363
    assert loss == 5.0

    # 2. Ubuntu scenario with 15% packet loss (17 of 20 received)
    ping_ubuntu_15_loss = """
PING 10.0.2.2 (10.0.2.2) 56(84) bytes of data.
--- 10.0.2.2 ping statistics ---
20 packets transmitted, 17 received, 15% packet loss, time 19050ms
rtt min/avg/max/mdev = 144.500/145.100/146.000/0.300 ms
"""
    rtt, loss = parse_ping_output(ping_ubuntu_15_loss, returncode=0)
    assert rtt == 145.1
    assert loss == 15.0

    # 3. Baseline healthy ping output (0% loss, 0.104ms RTT)
    ping_healthy = """
PING 10.0.2.2 (10.0.2.2) 56(84) bytes of data.
64 bytes from 10.0.2.2: icmp_seq=1 ttl=64 time=0.104 ms

--- 10.0.2.2 ping statistics ---
20 packets transmitted, 20 received, 0% packet loss, time 1904ms
rtt min/avg/max/mdev = 0.095/0.104/0.120/0.010 ms
"""
    rtt, loss = parse_ping_output(ping_healthy, returncode=0)
    assert rtt == 0.104
    assert loss == 0.0

    # 4. Total reachability failure (100% loss)
    ping_loss_100 = """
PING 10.0.2.2 (10.0.2.2) 56(84) bytes of data.

--- 10.0.2.2 ping statistics ---
20 packets transmitted, 0 received, 100% packet loss, time 2048ms
"""
    rtt, loss = parse_ping_output(ping_loss_100, returncode=1)
    assert rtt == 999.0
    assert loss == 100.0

def test_parse_ip_link_stats():
    sample_ip_link = """
3: veth-r1-r2@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc netem state UP mode DEFAULT group default qlen 1000
    link/ether 52:54:00:12:34:57 brd ff:ff:ff:ff:ff:ff
    RX:  bytes packets errors dropped  miss mcast
        204800    2048     15     240     0     0
    TX:  bytes packets errors dropped carrier collsns
        409600    4096      0     180     0     0
"""
    stats = parse_ip_link_stats(sample_ip_link, "veth-r1-r2")
    assert stats["is_up"] is True
    assert stats["rx_bytes"] == 204800
    assert stats["tx_bytes"] == 409600
    assert stats["rx_errors"] == 15
    assert stats["rx_drops"] == 240
    assert stats["tx_drops"] == 180

def test_telemetry_provider_topology_links_structure():
    active = ceso_service.set_provider_mode("LINUX_TESTBED")
    assert active == "LINUX_TESTBED"

    state = ceso_service.collect_and_normalize()
    assert len(state.links) == 3
    # Check that links[1] represents impaired router link
    link1 = state.links[1]
    assert link1.source_node == "netops-rtr1"
    assert link1.target_node == "netops-rtr2"

    # Reset provider mode back to SIMULATED
    ceso_service.set_provider_mode("SIMULATED")
