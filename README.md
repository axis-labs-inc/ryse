# RYSE Home Assistant component

A full-featured Home Assistant custom component to drive RYSE BLE Smart Shade devices.

This README walks you through installing the component on a Home Assistant bridge and
pairing a RYSE BLE Smart Shade with it.

Once a shade is paired it appears in Home Assistant as a normal **cover** entity, so you
can open it, close it, set it to any position, put it on a dashboard, and use it in
automations and scenes.

**Contents**

1. [Before you start](#1-before-you-start)
2. [Install the custom component](#2-install-the-custom-component)
3. [Pair a RYSE BLE device](#3-pair-a-ryse-ble-device)
4. [Using the shade](#4-using-the-shade)
5. [Troubleshooting](#5-troubleshooting)
6. [Updating and removing](#6-updating-and-removing)
7. [Known limitations](#7-known-limitations)

---

## 1. Before you start

Check the following before installing. Most pairing problems come from one of these
being missing.

| Requirement | Details |
| --- | --- |
| Home Assistant version | **2026.3 or newer.** The component uses Python 3.14 syntax, and 2026.3 is the first release that runs on Python 3.14. On older versions the component fails to load with a `SyntaxError`. |
| Bluetooth adapter | A working Bluetooth adapter on the bridge (built-in, USB dongle, or a Bluetooth proxy is *not* enough — see the limitations below). |
| Bluetooth integration | Home Assistant's **Bluetooth** integration must already be set up under **Settings → Devices & services**. |
| BlueZ / `bluetoothctl` | Pairing is performed with `bluetoothctl`. It is already present on Home Assistant OS, Supervised, and the official Container image. On a Core install in a Python virtual environment, install it yourself (`sudo apt install bluez` on Debian/Ubuntu). |
| Internet access | On first start Home Assistant downloads the `ryseble` library (version 1.9.0) from PyPI. |
| Range | Keep the shade within a few metres of the bridge while pairing. Walls and metal blinds reduce range considerably. |

---

## 2. Install the custom component

### 2.1 Download the files

Download the repository archive:

<https://github.com/mohamedkallel82/ryse/archive/refs/heads/main.zip>

Unzip it. The part you need is the `custom_components/ryse` folder.

### 2.2 Copy the folder onto the bridge

Copy the whole `ryse` folder into the `custom_components` directory of your Home
Assistant configuration. Create `custom_components` first if it does not exist.

Depending on your installation type you can use the **Samba share** add-on, the
**Terminal & SSH** add-on, the **Studio Code Server** add-on, or plain `scp`. For
example, over SSH:

```bash
scp -r custom_components/ryse root@homeassistant.local:/config/custom_components/
```

When you are done the layout must look exactly like this:

```text
/config
└── custom_components
    └── ryse
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── cover.py
        ├── manifest.json
        ├── quality_scale.yaml
        ├── strings.json
        └── translations
            └── en.json
```

A common mistake is ending up with `/config/custom_components/ryse-main/custom_components/ryse`.
The `ryse` folder — the one containing `manifest.json` — must sit directly inside
`custom_components`.

### 2.3 Restart Home Assistant

Go to **Settings → System → top-right menu → Restart Home Assistant**.

Custom components are only picked up at startup, so this step is required.

### 2.4 Check that it loaded

Go to **Settings → Devices & services → Add integration** and type `RYSE`. If the
integration shows up in the list, the component loaded correctly.

If it does not appear, open **Settings → System → Logs** and look for errors
mentioning `ryse`. The most common causes are a wrong folder layout (see above) or a
Home Assistant version older than 2026.3.

---

## 3. Pair a RYSE BLE device

The following video shows how to pair a RYSE BLE device with Home Assistant:

[![Watch the video](https://img.youtube.com/vi/G24vZGYZ-_o/0.jpg)](https://youtu.be/G24vZGYZ-_o)

### 3.1 Put the shade in pairing mode

**Press the PAIR button on the RYSE shade.**

This is not optional. The shade only advertises itself as "ready to pair" for a short
time after the button is pressed, and Home Assistant deliberately ignores RYSE devices
that are not in pairing mode. If you take too long, just press the button again.

### 3.2a Pair from the discovery notification (usual case)

A shade in pairing mode is normally picked up automatically:

1. Go to **Settings → Devices & services**.
2. A **RYSE** card appears under *Discovered* with the name of your shade.
3. Select **Configure**.
4. The dialog *Pair your RYSE device* asks you to press the PAIR button. Press it if
   the shade has fallen out of pairing mode, then select **Submit**.
5. Wait for pairing to finish and select **Finish**.

### 3.2b Add the device manually

If no discovery card appears, add it by hand:

1. Go to **Settings → Devices & services → Add integration**.
2. Search for and select **RYSE**.
3. Home Assistant scans for RYSE devices that are currently in pairing mode and shows
   them in a dropdown. Pick your shade.
4. Select **Submit**.

If the scan finds nothing you get *"No RYSE BLE device found in pairing mode. Please
press the PAIR button and retry."* — press the PAIR button on the shade and start again.

### 3.3 What happens during pairing

Pairing usually takes between 10 and 30 seconds. In the background Home Assistant trusts,
connects, pairs and bonds the shade over BlueZ, and retries up to three times before
giving up. Leave the shade powered and in range until the dialog closes.

### 3.4 The result

When pairing succeeds you get:

- a **device** named after the shade, with manufacturer *RYSE* and model *SmartShade BLE*;
- one **cover** entity for that device, for example `cover.ryse_shade`.

Repeat the whole of section 3 for each additional shade.

---

## 4. Using the shade

Open the device page from **Settings → Devices & services → RYSE**, or add the cover
entity to any dashboard.

- **Open** raises the shade fully, **Close** lowers it fully.
- The position slider accepts any value from 0 to 100, where **100 is fully open** and
  **0 is fully closed**.
- Position changes made with the physical remote or the RYSE app are pushed to Home
  Assistant by the shade, so the entity follows them without you doing anything.
- Home Assistant also polls the shade every 15 seconds as a fallback and to re-establish
  the Bluetooth link if it drops.

After a Home Assistant restart the entity is briefly shown as *Unavailable* until the
first successful connection to the shade. This is normal.

Example automation that closes a shade at sunset:

```yaml
automation:
  - alias: Close the living room shade at sunset
    triggers:
      - trigger: sun
        event: sunset
    actions:
      - action: cover.close_cover
        target:
          entity_id: cover.ryse_shade
```

---

## 5. Troubleshooting

**"No RYSE BLE device found in pairing mode"**
Press the PAIR button on the shade immediately before starting the flow. Also check that
the shade is not already added to Home Assistant — configured devices are filtered out of
the list on purpose.

**Pairing fails with "Failed to connect"**
Move the bridge and the shade closer together, power-cycle the shade, and try again. If
it keeps failing, an old bond may be in the way. From a terminal on the bridge:

```bash
bluetoothctl remove AA:BB:CC:DD:EE:FF
```

Use your shade's Bluetooth address, then pair again.

**The entity stays *Unavailable***
The shade is out of range, powered down, or connected to something else — a phone running
the RYSE app holds the BLE connection and locks Home Assistant out. Close the app and
wait for the next poll.

**Getting more detail in the logs**
Add this to `configuration.yaml` and restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.ryse: debug
    ryseble: debug
```

Then reproduce the problem and read **Settings → System → Logs**.

---

## 6. Updating and removing

**To update**, download the archive again, delete `/config/custom_components/ryse`,
copy the new folder in its place, and restart Home Assistant. Your paired devices and
entity settings are preserved.

**To remove a single shade**, open **Settings → Devices & services → RYSE**, then delete
the entry for that device.

**To remove the component entirely**, delete all RYSE entries first, then delete the
`/config/custom_components/ryse` folder and restart Home Assistant.

---

## 7. Known limitations

- The bridge needs its own Bluetooth adapter. Pairing shells out to `bluetoothctl` on the
  machine running Home Assistant, so remote Bluetooth proxies (ESPHome and similar) cannot
  be used to pair a shade.
- A shade can only talk to one client at a time. Keep the RYSE phone app closed while
  Home Assistant is using it.
- Tilt is not supported; the shade exposes open, close and position only.
- The integration is installed manually. This repository is not currently packaged for
  HACS.
