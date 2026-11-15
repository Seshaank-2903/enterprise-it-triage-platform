# Corporate VPN & Network Troubleshooting Guide

- **Doc ID:** `KB-NET-202`
- **Canonical URL:** `https://kb.enterprise.internal/network/vpn-troubleshooting`
- **Classification:** Standard Operating Procedure (SOP)

## 1. WireGuard & GlobalProtect Connection Failures
1. If client status shows `Handshake Failed`, check if current IP is blocklisted due to consecutive failed authentications.
2. Ensure local DNS server is set to route corporate intranet traffic via `10.0.0.2` and fallback `1.1.1.1`.
3. To reset the tunnel interface on macOS:
   ```bash
   sudo ifconfig utun3 down && sudo ifconfig utun3 up
   ```
4. On Windows:
   Restart the `WireGuard Tunnel Service` from `services.msc`.

## 2. Remote Office Wi-Fi Routing
Corporate 802.1X Wi-Fi networks require the Enterprise Root CA Certificate installed in the local system trust store.
