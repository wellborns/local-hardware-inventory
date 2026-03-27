# Hardware Inventory

Last updated: 2026-03-27
Owner: Your Name

Purpose: shared source of truth for active and spare/inactive hardware, IPs, hostnames, role, and notes.

---

## Active / In Use

| Name | Type | Hostname | IP | Network/VLAN | Primary Use | Location | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| Test-Node-01 | Mini PC | test-node-01 | 10.0.0.10 | Test LAN | Sample active device for demo purposes | Test Lab | Active | This is a placeholder test entry |

---

## Spare / Inactive / Staging

| Name | Type | Serial/ID | Last Known State | Intended Use | Notes |
|---|---|---|---|---|---|
| Test-Spare-01 | SBC | SN-TEST-0001 | On hand / staging | Sample staging device for demo purposes | This is a placeholder test entry |

---

## Networks (Reference)

| Network | VLAN | CIDR | Current Intent |
|---|---|---|---|

---

## Change Log (Newest First)

- **2026-03-27: Replaced inventory with test data for public repo demo.**

---

## Update Rules

1. Add new hardware on receipt (even if not configured yet).
2. Keep IP/hostname fields current whenever changed.
3. Move entries between **Active** and **Spare/Inactive** as status changes.
4. Add one-line note when role changes significantly.
5. Keep this file in git so both of us have history.
