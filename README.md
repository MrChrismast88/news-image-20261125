# The World in One Day — Wednesday 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/MrChrismast88/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A pure-stdlib Python 3.13 program that draws a newspaper front page
summing up the world's news of Wednesday 25 November 2026 and writes it
to `/output/entry.png` (1024×1024 PNG, well under 1 MiB).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

No dependencies, no network, no randomness, no clock: two runs write
byte-identical output.

## What it draws

- **Lead:** The Trump administration proposes new tariffs of up to 20%
  on China, the EU and 12 more nations after an eight-month probe.
- **Hormuz:** Two oil tankers hit naval mines and caught fire in the
  Strait of Hormuz, Iran said; the US issued a fresh alert.
- **Yemen–Saudi Arabia:** Houthis hit the Ras Tanura refinery and a
  Riyadh skyscraper, injuring 11 people.
- **Tech:** A US court convicts Huawei of stealing trade secrets and
  bank fraud; China condemned the verdict.
- **Space:** China's Shenzhou-24 carries Pakistan's Muhammad Zeeshan Ali,
  the first foreign astronaut to board Tiangong.
- **Pacific:** Australia and the Solomon Islands sign a treaty barring
  any foreign military base in the Solomons.
- **Ukraine:** Leaked Russian statistics put Russian war dead at 490,334.
- **Also:** Hamas colonel killed in Gaza; RSF strikes kill 19 in Sudan;
  Wall Street slides; bomb in Colombia injures 23; Bangladesh raises
  the garment wage 36%; COP31 talks fail.

Sources: Reuters, AP, AFP, Just Security. All events from 25 November 2026.
