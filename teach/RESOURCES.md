# Baremetal Hardware Debugging — Resources

## Knowledge

### BeagleBone AI Hardware

- [BeagleBone AI System Reference Manual](https://beagleboard.org/static/beaglebone/a/Docs.html)
  Official documentation: schematics, memory map, pinmux, PRCM. Use for: anything about the BBAI hardware itself.

- [AM572x Sitara Processor Technical Reference Manual](https://www.ti.com/lit/pdf/spruhz6)
  The SoC manual for the BBAI's dual-core A15 + 2x M4 + 2x DSP. 7000+ pages. Use for: PRCM registers, UART config, pinmux controller, GIC distributor.

### Serial / UART Debugging

- [BeagleBone AI Serial Console](https://beagleboard.org/getting-started#serial)
  Official guide: connecting a USB-UART cable, identifying pins, baud rate (115200 8N1).

### JTAG / OpenOCD

- [OpenOCD User's Guide](https://openocd.org/doc/html/index.html)
  Reference for JTAG debugging on ARM. Scripts for TI Sitara / OMAP targets.

- [Tag-Connect TC2050-IDC](https://www.tag-connect.com/product/tc2050-idc-legacy)
  The 10-pin JTAG cable for the BBAI's mini-JTAG header. This + ARM-20 adapter gets you OpenOCD access.

### ARM Debug Architecture

- [ARM Architecture Reference Manual ARMv7-A (ARM DDI 0406C)](https://developer.arm.com/documentation/ddi0406/latest/)
  Chapter B1: System registers. Chapter B6: Debug. Use for: understanding monitor mode, debug registers, vector catch.

### Crash Debugging (Data/Prefetch Aborts)

- [ARM Exceptions and Interrupts](https://developer.arm.com/documentation/dui0473/m/exceptions-and-interrupts)
  Understanding exception types, vector table, and fault status registers (DFSR, IFSR, DFAR, IFAR).

## Tools

- `screen` / `minicom` / `picocom` — terminal emulators for serial console
- OpenOCD — JTAG debug server
- GDB (arm-none-eabi-gdb) — debugger client
- Saleae Logic / sigrok — cheap logic analyzer for UART/timing debug
