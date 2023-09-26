# rp2040_machester_pio

## PIO example using Micropython for RP2040 microprocessor
The RP2040 microcontroller contains a programmable input/output block (PIO). This is a simple separate lopgic unit that can be programmed in something like assembly. It is very versatile, this example is primitive, but made for a quick fix in this application.

I had an existing 434MHz radio transmitter which I wanted to emulate using a similar simple radio module. The existing protocol was reverse engineered from the original transmitter. That protocol is based on a Manchester encoded signal, it  includes a specific preamble (repeated high low sequence to allow the receiver module to adjust gain), and particular (non Manchester compliant) bit patterns to mark the start and end of transmission.

The aim was to quickly replicate that protocol to fee a new sensor into the system. There is a PIO example to handle Manchester encoding, written in C and provided by the Raspberry Pi foundation;

https://github.com/raspberrypi/pico-examples/blob/master/pio/manchester_encoding/manchester_encoding.pio

and discussion around  "Port PIO Manchester encoding example to Python"

https://forums.raspberrypi.com/viewtopic.php?t=307397

This work was largely based on that information, just modified to include the preamble, start and end signal. 

In essence this PIO example works in 24bit chunks, it is not particularly efficient, because for most of the signal only the intermediate bit contains data. However the state machine easily meets the requirements and resources available. 

Of each 24 bit chunk;
- The first 8 bits are used to identify the fist bit of data, a non-zero value marks the preamble length
- The second bit contains a single data bit
- The final bit identifies if this is the last data bit

The PIO pull in 24 bits. If the first bit is identified it creates the preamble and start sequence, if the last data bit is identified the end sequence is appended. Otherwise the state machine simply Manchester encodes each data bit.

To keep things simple for a 1KHz signal I picked a state machine frequency of 60kHz and wrote the state machine in such a way that any operation consumed 60 steps. Ultimately, with much oscilloscope pokery, I discovered that the original protocol contained a timing error that meant the transmission was around 997.5Hz rather than 1KHz, so I adjusted the state machine frequency to match this error.

The end result is a state machine which can handle a custom protocol. Sending a transmission is a simple matter of filling the state machine buffer with a byte string, the PIO will process the string a byte at a time. As soon as the buffer is written to the program flow can continue with no concern for timing or holding up processor time whilst transmitting. 
