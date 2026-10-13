# Power Tests

## First Cell Test
- Cell 1: 3.56V
- Cell 2: 3.56V
- Cell 3: 3.56V
- Cell 4: 3.56V

## 2S2P Output Test
- 7.12V at BMS B+ B-
- 3.56V at BMS B+ BM, B- BM (Cell groups balanced)
- 5.08 at distribution (buck output)
- reduced to 7.11V ~ 15mins (low load)

## Charge test #1 TP5100
- 10:45AM 7.11V (BM 3.55V)
- 11:00AM 7.13V (BM 3.56V)
- 11:15AM 7.14V (BM 3.57V)
- 11:30AM 7.15V (BM 3.57V)
- 11:45AM 7.15V (BM 3.57V)

Result - Failure: Battery charge test manually terminated due to high temperature at TP5100 module.
TP5100 emitted high heat and sizzling sounds, board discarded due to safety concern.
BMS balancing remained consistent.

## Charge test #2 8.4V 1.2A dedicated 2S Charger
- 12:47PM 7.15V (BM 3.57V)
- 01:02PM 7.29V (BM 3.64V)
- 01:17PM 7.34V (BM 3.66V)
- 01:32PM 7.38V (BM 3.68V)
- 01:47PM 7.41V (BM 3.70V)

Result - Success: Battery charge was found to be acceptable with an increase in about 0.26V over an hour.
Low to no heat observed across PCB and batteries remained cool. External charger heated to expected level.
The charger was observed to continue supplying charge near the target voltage rather than demonstrating the expected charge-current taper/cutoff behavior. Charging therefore requires manual monitoring pending further validation or replacement.
BMS balancing remained consistent.

## Discharge Test
- 12:40PM 8.21V
- 02:15PM 8.06V
- 03:25PM 7.86V
- 05:26PM 7.57V
- 06:47PM 7.37V

Result — Preliminary success: The pack powered the Raspberry Pi 5 and LCD continuously for approximately six hours under low load. 
Pack voltage decreased from 8.21 V to 7.37 V. 
BMS cell-group balance remained consistent during testing. 
Higher-load runtime testing is still required.
