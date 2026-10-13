**Battery Configuration**: 2S2P lithium-ion pack. Maximum pack voltage: 8.4 V nominal full charge.

## BATTERY PACK / BMS
Pack + --> BMS B+
Series Midpoint --> BMS BM
Pack - --> BMS B-
====================================================
## CHARGING
BMS P+ --> Dedicated Charger +
BMS P- --> Dedicated Charger -
====================================================
## MAIN POWER
BMS P+ --> 10A Fuse
10A Fuse --> Switch VIN
BMS P- --> Switch GND

Switch GND --> CK2416 GND
Switch VOUT --> CK2416 VIN
====================================================
## 5V OUTPUT
CK2416 GND --> WAGO GND
CK2416 VOUT --> WAGO 5V
====================================================
## DEVICES
WAGO 5V --> Devices +
WAGO GND --> Devices -
====================================================
## BUTTON
Switch A --> Button T1
Switch B --> Button T2