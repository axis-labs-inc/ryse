# Pair a RYSE SmartBridge with Home Assistant

This guide explains how to connect a **RYSE SmartBridge** (the IoT IP gateway) to a
Home Assistant bridge so you can control shades that are attached to the SmartBridge.

The SmartBridge speaks **HomeKit over your local network**. Home Assistant talks to it
with the built-in **HomeKit Device** integration (formerly *HomeKit Controller*). You do
**not** need the RYSE BLE custom component for this path.

Once pairing succeeds, each shade on the SmartBridge appears in Home Assistant as a
normal **cover** entity. You can open it, close it, set a position, put it on a
dashboard, and use it in automations and scenes.

**Contents**

1. [Before you start](#1-before-you-start)
2. [Get the SmartBridge onto your network](#2-get-the-smartbridge-onto-your-network)
3. [Attach shades to the SmartBridge](#3-attach-shades-to-the-smartbridge)
4. [Make sure the SmartBridge is free to pair](#4-make-sure-the-smartbridge-is-free-to-pair)
5. [Pair the SmartBridge in Home Assistant](#5-pair-the-smartbridge-in-home-assistant)
6. [Using the shades](#6-using-the-shades)
7. [Troubleshooting](#7-troubleshooting)
8. [SmartBridge vs BLE pairing](#8-smartbridge-vs-ble-pairing)

---

## 1. Before you start

| Requirement | Details |
| --- | --- |
| RYSE SmartBridge | Powered on and reachable on the same LAN as Home Assistant. Model number is printed on the bottom (`BR-0101` needs Ethernet; `BR-0201` can use Ethernet or Wi‑Fi). |
| HomeKit pairing code | The eight-digit code (and often a QR code) printed on the bottom of the SmartBridge or on its packaging. Keep it; Home Assistant needs it to finish pairing. |
| Home Assistant | Any current release with the default config (Zeroconf discovery is included). If you turned `default_config` off, add `zeroconf:` to `configuration.yaml` and restart. |
| Same network | The SmartBridge and the Home Assistant host must be on the **same Layer‑2 network**. Guest Wi‑Fi, client isolation, and VLANs that block mDNS will stop discovery. |
| Single HomeKit controller | A HomeKit accessory can be paired to **only one** controller at a time. It cannot stay in Apple Home *and* Home Assistant. |

You do **not** need an Apple device for day-to-day use with Home Assistant. An iPhone is
optional and only useful if you prefer to join the SmartBridge to Wi‑Fi through Apple
Home first (see model notes below).

---

## 2. Get the SmartBridge onto your network

Home Assistant discovers the SmartBridge as a HomeKit accessory on IP. It must already
be online before you try to pair.

1. Plug the SmartBridge into power.
2. Join it to your LAN (see model table below).
3. Open the **RYSE** mobile app and add the SmartBridge if it is not already listed.

Setup depends on the model printed under the unit:

| Model | Network | Recommended first step |
| --- | --- | --- |
| **BR-0101** | **Ethernet only** — use the included cable to the router. | Set the SmartBridge up in the **RYSE app** and add your shades to it **before** pairing with Home Assistant. |
| **BR-0201** | Ethernet **or** Wi‑Fi. | Join the network through the RYSE app first. You can also start from HomeKit on this model, but app-first setup is the most reliable path for Home Assistant. |

Official RYSE help for putting the bridge online:

- [Do I need Ethernet or Wi‑Fi?](https://support.helloryse.com/en/articles/5186282-do-i-need-to-connect-my-smartbridge-into-a-wifi-router-or-an-ethernet-port)
- [Pairing SmartBridge to the App (with Ethernet)](https://support.helloryse.com/en/articles/5628738-pairing-smartbridge-to-the-app-with-ethernet)
- [Pairing SmartBridge to iPhone via Wi‑Fi](https://support.helloryse.com/en/articles/9664001-pairing-smartbridge-to-iphone-via-wi-fi)
- [Pairing SmartBridge to Android via Wi‑Fi](https://support.helloryse.com/en/articles/9663662-pairing-smartbridge-to-android-via-wi-fi)

Wait until the SmartBridge shows as connected in the RYSE app (typically all three blue LEDs
solid on a healthy link) before continuing.

---

## 3. Attach shades to the SmartBridge

Pair each SmartShade / SmartCurtain to the SmartBridge in the RYSE app so the bridge
exposes them as HomeKit accessories.

1. In the RYSE app, open your SmartBridge.
2. Add a shade and follow the on-screen pairing steps (press **PAIR** on the shade when
   asked).
3. Give each shade a clear name. That name is what Home Assistant will use as the
   default device title.
4. Confirm you can open and close each shade from the RYSE app through the SmartBridge.

Official guide: [Pairing SmartShade to the App via SmartBridge](https://support.helloryse.com/en/articles/5628836-pairing-smartshade-to-the-app-via-smartbridge).

---

## 4. Make sure the SmartBridge is free to pair

HomeKit accessories accept **one** controller. If the SmartBridge is already paired to
Apple Home (or another HomeKit controller), Home Assistant cannot finish pairing.

### If it is in Apple Home

1. Open the **Apple Home** app.
2. Remove the RYSE SmartBridge accessory (and its shades) from the home.
3. Do **not** factory-reset unless removal fails. Removing it from Apple Home leaves it
   on your network but opens it for a new controller — that is what Home Assistant
   needs.

### If it was previously paired and will not show up

Community reports for used or reassigned SmartBridges are consistent: clear the old
HomeKit pairing, then set the bridge up again on the network.

1. Delete the SmartBridge from the RYSE app if it is still listed
   ([Delete a SmartBridge from the App](https://support.helloryse.com/en/articles/5631433-delete-a-smartbridge-from-the-app)).
2. Factory-reset the SmartBridge: with a pin, **press and hold** the reset button on the
   back of the unit for **more than 3 seconds** until it reboots into a clean state.
   (A short press only toggles Wi‑Fi setup modes on `BR-0201` — that is not a factory
   reset.) See also
   [How to Factory Reset your SmartBridge](https://support.helloryse.com/en/articles/5643724-how-to-factory-reset-your-smartbridge).
3. Repeat [section 2](#2-get-the-smartbridge-onto-your-network) and
   [section 3](#3-attach-shades-to-the-smartbridge).

---

## 5. Pair the SmartBridge in Home Assistant

### 5.1 Discovery (usual case)

1. Go to **Settings → Devices & services**.
2. Under *Discovered*, look for a **HomeKit Device** card for the RYSE SmartBridge.
3. Select **Configure**.
4. Enter the **HomeKit pairing code** from the bottom of the SmartBridge (format
   `XXX-XX-XXX`) and submit.
5. Assign a room if asked, then select **Finish**.

Home Assistant adds the SmartBridge and the shades that are currently attached to it.
Each shade becomes a **cover** entity you can control like any other cover.

### 5.2 Add it manually if no discovery card appears

1. Go to **Settings → Devices & services → Add integration**.
2. Search for and select **HomeKit Device**.
3. Pick the RYSE SmartBridge from the list of unpaired accessories.
4. Enter the pairing code and finish as above.

### 5.3 What you should see

After a successful pair:

- a **HomeKit Device** integration entry for the SmartBridge;
- one **cover** entity per shade (for example `cover.living_room_shade`);
- open / close / position controls that mirror what the RYSE app shows through the bridge.

New shades you later attach to the SmartBridge in the RYSE app are usually picked up
automatically. If an entity is missing, reload the HomeKit Device entry or restart
Home Assistant.

---

## 6. Using the shades

Open a shade from **Settings → Devices & services → HomeKit Device**, or add the cover
entities to any dashboard.

- **Open** raises the shade, **Close** lowers it.
- The position slider accepts values from 0 to 100 (Home Assistant cover semantics:
  **100 is open**, **0 is closed**).
- Automations and scenes work the same way as for any other cover.

Example automation:

```yaml
automation:
  - alias: Close living room shades at sunset
    triggers:
      - trigger: sun
        event: sunset
    actions:
      - action: cover.close_cover
        target:
          entity_id: cover.living_room_shade
```

Optional: after the SmartBridge is paired with Home Assistant, you can expose those
covers back to Siri / Apple Home with Home Assistant’s separate **HomeKit Bridge**
integration. That is an *export* step and is not required for control inside Home
Assistant.

---

## 7. Troubleshooting

**No discovery card for the SmartBridge**

- Confirm the SmartBridge is online in the RYSE app.
- Confirm Home Assistant and the SmartBridge share the same LAN (no guest Wi‑Fi / client
  isolation).
- Confirm Zeroconf is enabled (`default_config` or an explicit `zeroconf:` entry).
- Confirm the SmartBridge is not still paired to Apple Home or another controller
  ([section 4](#4-make-sure-the-smartbridge-is-free-to-pair)).

**Pairing rejects the code / “already paired”**

HomeKit thinks another controller owns the accessory. Remove it from Apple Home, or
factory-reset and set it up again, then retry with the code printed on the unit.

**Shades missing after the bridge pairs**

Add the shades to the SmartBridge in the RYSE app first, then reload the HomeKit Device
integration. Empty bridges expose no cover entities.

**Confusing HomeKit Device with HomeKit Bridge**

| Integration | Role |
| --- | --- |
| **HomeKit Device** | Imports RYSE SmartBridge accessories *into* Home Assistant. Use this for pairing. |
| **HomeKit Bridge** | Exports Home Assistant entities *out* to Apple Home. Not used to pair the SmartBridge. |

**Prefer not to use the SmartBridge at all**

If the Home Assistant host (or a Bluetooth proxy) is close enough to the shades, you can
pair each shade over BLE with the RYSE custom component instead. See the
[BLE user guide in the README](../README.md#3-pair-a-ryse-ble-device).

---

## 8. SmartBridge vs BLE pairing

| | SmartBridge (this guide) | BLE custom component |
| --- | --- | --- |
| Hardware | RYSE SmartBridge on Ethernet / Wi‑Fi | Bluetooth adapter or proxy near each shade |
| Home Assistant integration | Built-in **HomeKit Device** | RYSE custom component (`custom_components/ryse`) |
| Extra software | None (built into Home Assistant) | Install the component from this repository |
| Best when | Shades are far from the HA host; you already own a SmartBridge | You want direct local BLE control without a gateway |

Do not pair the same physical shade to both paths at once. A shade that is actively
managed by the SmartBridge is not available for a separate BLE bond to Home Assistant.

---

## Further reading

- Home Assistant: [HomeKit Device](https://www.home-assistant.io/integrations/homekit_controller/)
- RYSE product page: [SmartBridge](https://www.helloryse.com/products/ryse-smartbridge)
- RYSE Help Center: [Installation & Setup](https://support.helloryse.com/en/collections/3165414-installation-setup)
