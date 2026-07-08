# Serial Console Setup for BBAI Baremetal Debugging

Completed Lesson 1 ("Serial Console Debugging") which covered: the BBAI UART0/UART3 pinout for serial console connection, how the existing `src/serial.c` code maps to real hardware (PL011 in QEMU vs TI UART3 at 0x49020000), the "see nothing" checklist (power → swap TX/RX → GND → baud → voltage → PRCM clock → pinmux), and ARM DFSR decoding for exception handlers.

The user correctly answered both quizzes (UART0 vs UART3 when using only one USB-UART cable; swapping TX/RX as the first debug step).

**Implications:** The user already has working UART code for both QEMU and BBAI. Next lesson can cover U-Boot chainloading (getting the kernel binary onto an SD card and booting it), which is the next bottleneck before any UART output can appear from the custom kernel.

**Status:** active
