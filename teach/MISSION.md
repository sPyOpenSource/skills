# Mission: Baremetal Hardware Debugging

## Why

You're building a baremetal RTOS on the BeagleBone AI (Cortex-A15). It works in QEMU, but real hardware has new failure modes: wrong clock configs, pinmux errors, unresponsive peripherals, silent hangs. You need hardware-level debugging skills to bridge that gap.

## Success looks like

- Can connect a serial console to the BBAI and see boot output
- Can chainload a kernel via U-Boot over SD card
- Can interpret a data/prefetch abort dump and find the offending code
- Can use JTAG (OpenOCD + GDB) to halt, step, and inspect state on real hardware
- Can debug peripheral init failures (PRCM, pinmux, MMC2) systematically

## Constraints

- Lessons under 10 minutes each
- Every lesson ties to your real BBAI codebase (`/Users/xuyi/Source/OS/UEFI/`)
- Prefer practical steps over theory — you already know ARM assembly and C
- Hardware budget: BBAI board, USB-UART cable, JTAG adapter (Tag-Connect TC2050)

## Out of scope

- Writing production-quality device drivers from scratch
- Deep electrical engineering / signal integrity
- Debugging Linux or other OSes — this is about baremetal only
