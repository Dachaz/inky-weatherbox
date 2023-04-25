# inky-weatherbox
![](/assets/images/header.jpg)

## What is it?
An [over-engineered](#known-issues-and-learnings) weather display. Face the inevitable wind and rain in style!

## What does it display?
![](/assets/images/display.png)

## How does it work?

### Hardware
Depending on your preferences, you could either do a full battery-powered build or a simplified, USB-powered build.

#### Full build:
* RaspberryPi [Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) (without GPIO headers)
* [Long headers](https://www.tme.eu/en/details/zl209-20p/pin-headers/connfly/ds1021-1-20sf15-b/) (18mm) ⚠️ Soldering required!
* Pimoroni [Inky pHAT](https://shop.pimoroni.com/products/inky-phat) display (my build has v1 of the pHAT, which is lower resolution)
* PiSupply [PiJuice Zero](https://uk.pi-supply.com/products/pijuice-zero)
* PiSupply [PiJuice Zero 1200mAh Battery](https://uk.pi-supply.com/products/pijuice-zero-1200mah-battery)
* 3D printed [case](/assets/case)

#### Minimal build:
* Any RaspberryPi (pre-soldered GPIO works perfectly)
* Pimoroni [Inky pHAT](https://shop.pimoroni.com/products/inky-phat) display
* **Optional:** A better-designed case, like the one from [Balena Inkyshot](https://github.com/balena-labs-projects/inkyshot/tree/master/assets)

### Software
Again, depending on your build, there are two flavours:

#### Full build:
* Config-file driven
* Wakes up PiZero every hour
* Reports the battery level to NewRelic (so you can get alerted when the battery is low)
* Updates the display
* Creates both a local and a remote (NewRelic) log entry for each run
* Sets PiZero to sleep for an hour (or until next morning, if in quiet time)

#### Minimal build:
* A single CLI script that takes various arguments and either updates the Inky pHAT display or outputs image to a file

## Setup

1. [Install RaspberryPi Lite OS](https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system) — you could use the full-blown (desktop) OS but that will needlessly drain your battery on each wake-up.
1. Configure your wireless networking. Ensure that "Wait for network on boot" is enabled in `raspi-config`
1. Enable I2C and SPI in `raspi-config`
1. **Recommended:** [Set-up SSH](https://www.raspberrypi.com/documentation/computers/remote-access.html) on your RaspberryPi
1. [Install Inky pHAT software](https://learn.pimoroni.com/article/getting-started-with-inky-phat). In short: `curl https://get.pimoroni.com/inky | bash` and say **Y** to everything (to install all additional packages we'll need later).
1. **Recommended:** Verify that your installation works by running one of Pimoroni code examples, e.g. the [Name Badge Example](https://learn.pimoroni.com/article/getting-started-with-inky-phat#running-the-built-in-examples).

### Minimal build:
7. Copy `weather.py` somewhere to your RaspberryPi. e.g. `/home/[you]`
8. Set up `weather.py` to run every half an hour:
   1. Run the crontab editor: `crontab -e`
   1. Add the following line: `*/30 * * * * python3 /home/[you]/weather.py` (this will give you weather in Amsterdam, see the following section on how to pass parameters)

### Full build:
7. [Install PiJuice software](https://github.com/PiSupply/PiJuice/tree/master/Software). Since we're running headless, that boils down to `sudo apt-get install pijuice-base`
1. If you haven't connected the battery yet, power down, connect the battery, connect back to the power and run `pijuice_cli`.
   * Ensure that your battery is recognised correctly, and if not - [change the battery profile](https://github.com/PiSupply/PiJuice/tree/master/Software#battery-profile)
   * Set the correct [RTC time](https://github.com/PiSupply/PiJuice/tree/master/Software#wakeup-alarm)
1. [Set up a free NewRelic account](https://newrelic.com/signup)
1. Create a copy of `config.ini.SAMPLE` and call it `config.ini`
   * Copy your NewRelic [License API key](https://one.newrelic.com/admin-portal/api-keys/home) to `config.ini`
   * Edit the rest of the file to reflect your preferences.
1. Copy all of the code from this repository somewhere to your RaspberryPi. e.g. `/home/[you]/inky-weatherbox`
1. Set up `runandturnoff.py` to run on every boot:
    1. Run the crontab editor: `crontab -e`
    1. Add the following lines:
    `@reboot python3 /home/[you]/inky-weatherbox/runandturnoff.py` (make sure to use the same path from the previous step)
1. **Recommended:** Set `runandturnoff.py` to run when you switch from USB power (charging) to battery power:
    1. Enable "No power" [System Event](https://github.com/PiSupply/PiJuice/tree/master/Software#system-events-menu-1) and set it to `USER_FUNC1`
    1. [Configure](https://github.com/PiSupply/PiJuice/tree/master/Software#user-scripts-menu-1) `USER_FUNC1` to point to `/home/[you]/inky-weatherbox/runandturnoff.py` (make sure that the file is executable)
1. **Optional:** Create a [dashboard](https://one.eu.newrelic.com/dashboards) in NewRelic to track the battery life:
    * Click **+ Create a Dashboard** > **Create a New Dashboard**
    * To view the battery level:
      1. Click **Add a widget** > **Add a chart**
      1. Add this query: `SELECT latest(battery.charge_level) FROM Metric WHERE app.name ='inky-weatherbox' TIMESERIES AUTO ` (if you changed the app name in `config.ini` update it here).
      1. Click **Run**
      1. Set **Chart name** to "Battery"
      1. Expand **Null values** and set the dropdown value to **Remove**
      1. Click **Save**
    * To view the latest log entries:
      1. Click **Add a widget** > **Add a chart**
      1. Add this query: `SELECT message,batt FROM Log ORDER BY timestamp DESC`
      1. Click **Save**
1. **Optional:** Set up an [alert](https://one.eu.newrelic.com/alerts-ai/alerts-classic/policies) when the battery level is low
    * `SELECT latest(battery.charge_level) FROM Metric WHERE app.name = 'inky-weatherbox'`


## Usage

### `runandturnoff.py` ([source](/runandturnoff.py))
This file is, essentially, the implementation of the *[Full Build logic](#software)*.

If it's run on battery power, it will turn RaspberryPi off after the run. If it's run while being charged via any of the USB ports (on RaspberryPi or PiJuice) it will not turn RaspberryPi off (and will not schedule the next run).

### `weather.py` ([source](/weather.py))
This file is either called by `runandturnoff.py` or it can be executed stand-alone. To see all the CLI parameters, run `python3 weather.py -h` (or just `./weather.py -h`). The `--mock` mode is useful for testing on a computer that doesn't have Inky pHAT connected as it will output the target image to a file (`inky.png`).

#### Usage examples
```bash
./weather.py -lat 44.80 -lon 20.47            # Gets weather for Belgrade, RS in ºC and km/h
./weather.py -lat 54.97 -lon -1.61 -w mph     # Gets weather for Newcastle upon Tyne, UK in ºC and mph
./weather.py -lat 25.04 -lon 77.35 -w kn -t F # Gets weather for Nassau, BS in ºF and knots
./weather.py -m v1 # Gets weather for Amsterdam and creates inky.png instead of updating the display
```
ℹ️ All of the previous examples can be run as `python3 weather.py` as well.

# Known issues and learnings

🪫 **The battery life is pretty bad.**

Even with all of the unorthodox optimisations, I couldn't get more than ~12 days out of the 1200mAh battery. What drains the battery the most is the OS boot sequence, which takes about 2 minutes. I tried disabling a lot of services, using static DNS and IP address (to not wait for the DHCP server), and getting a blazing fast SD-card — all of which shaved a few seconds off the boot process, but not enough.

🛜 **The WiFi is wonky AF.**

I've spent many hours fighting with WiFi and trying to make sure that RaspberryPi has internet connection as quickly as possible and that the `runandturnoff.py` is only run after the internet connection is fully established. With every patch (some of which are outlined in [Networking](#networking) section below) the system became more complex, but not more reliable.

🫥 **The battery may not deliver enough power**

After being on a holiday for a few weeks, and leaving `inky-weatherbox` to drain its battery without recharging, I experienced that, upon a new charge, the display gave a washed-out image, and even that red colour wasn't getting displayed at all. At first, I thought that I had damaged the screen, but once I plugged the RaspberryPi into USB, the colours were vivid and sharp again. I remember reading that eInk screens need reliable power supply to properly update the image, and it might be that the battery I'm using got damaged (or that there's a different reason it stopped working after barely 3 12-day cycles). At this point I gave up on running this project off a battery, so I didn't investigate further.

🖼️ **Only works sensibly on Inky pHAT**

While the code will not break if you try to run it with [Inky wHAT](https://shop.pimoroni.com/products/inky-what) or [Inky Impression](https://shop.pimoroni.com/products/inky-impression-4), the output will be *all over the place*. **Contributions welcome!**

🧠 **In short:**

I've picked wrong tools for the task. I was blinded by the idea of having an ultra-tiny easily-programmable computer, and I got carried away equating single-purpose microcontrollers I have around my house, with generic-purpose high-level computer such as RaspberryPi. Still, it was a valuable lesson in building hardware as I had to learn a lot of new skills (how to solder and more so: how to desolder, how RTC/low power consumption works, how to find overly specific components, how to make a simple 3D model, etc).

🤔 **Why bother sharing, then?**

When I got the idea to build this, the information was very fragmented and spread across many websites. The code in here is patchwork of about 10 different online resources. While it's *very* far from perfect, at least there are 2 good things about it:

1. `weather.py` works without you having to create any weird API keys (kudos to [Open-Meteo](https://github.com/open-meteo))
2. I plan to reuse `runandturnoff.py` for a different *incredibly original* project soon. Maybe I generalise it then 🤷‍♂️


# Additional reading

Here are some resources that I've been looking into when trying to shave seconds off the RaspberryPi's boot (to prolong the battery life).

## Networking:
- [Set static IP address](https://raspberrypi.stackexchange.com/a/74428) (Network Interfaces method)
- [Real wait for network on boot](https://forums.raspberrypi.com/viewtopic.php?t=187225) (written for `networking.service`, not `dhcpcd.service`)

## Power saving / boot optimisation:
- [Disable system services](https://raspberrypi.stackexchange.com/a/127257)
- [Disable splash screen on boot](https://scribles.net/silent-boot-up-on-raspbian-stretch/)
- See what's slowing up startup:
  - `systemd-analyze blame`
  - `systemd-analyze critical-chain`


# License

Copyright © 2023 Dachaz. This software is licensed under the **MIT License**.

Parts of the image generation code Copyright © 2020 Derek Caelin.
