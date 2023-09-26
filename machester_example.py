import time, ujson
from rp2 import PIO, StateMachine, asm_pio
from machine import Pin, Timer, freq

# run at a nice simple division frequency for 1KHz signal
freq(120000000) # 120MHz

# send data in 24bit packets <8bits stop length><data byte><8bits preamble length>
# first packet has data + preamble
# middle packets just data zero padded
# last packet has stop + data + 0
# set pins is setting both the TX enable pin (first bit) & data (second bit), hence values of 0,1 & 3

@asm_pio(set_init=(PIO.OUT_LOW, PIO.OUT_LOW), out_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=24)
def tx():
    label("packet")
    out(y, 8)                                 # load preamble length
    set(x, 7)                                 # byte counter to read/loop over later 0-7
    jmp(not_y, "data_b")                      # if y==0 then go to data
    nop()
    label("preamble")                         # if y is set then we need to preamble
    set(pins, 0b00011)                [29] 
    set(pins, 0b00001)                [28] 
    jmp(y_dec, "preamble")                    # or generate start bits
    set(pins, 0b00011)                [29]    # 3 half-cycles of high followed by 1 half-cycle of low.
    set(pins, 0b00011)                [29]
    set(pins, 0b00011)                [29]
    set(pins, 0b00001)                [21]    # next change is in 2 instructions
    label("data")
    nop()                             [5]     # catch up timing if within byte read loop
    label("data_b")
    out(y, 1)                                 # read a data bit and process it
    jmp(not_y, "do_0")                        # if x=0 jump
    label("do_1")
    set(pins, 0b00011)                [29]
    set(pins, 0b00001)                [20]
    jmp(x_dec, "data")                        # get next data bit
    jmp("check_stop")                         # or data done, check for a stop byte
    label("do_0")
    set(pins, 0b00001)                [29]
    set(pins, 0b00011)                [20]
    jmp(x_dec, "data")                        # get next data bit  
    nop()                             [0]     # test timing 20/5/22
    label("check_stop")
    out(y, 8)                                 # load last 8 bits, 
    jmp(not_y, "packet")                      # y=0 so get next packet
    # otherwise send the stop bitlabel("stop_bits")
    nop()                       [4]
    # HI L HI HI HI (L/off)
    set(pins, 0b00011)                [29]    # 1 low bytes
    set(pins, 0b00001)                [29]    # 3 low byte
    set(pins, 0b00001)                [29]    # 
    set(pins, 0b00001)                [29]    # 
    set(pins, 0b00000)                        # turn off TX

# bytes <non-zero = end of stream><data MSB><data LSB><non-zero = start of stream>
# first 16bit packet           00         3333        0b
# mid   16bit packet           00         3333        00
# last  16bit packet           01         3333        00

# pin 14 is power enable, 15 is data
sm = StateMachine(0, tx, freq=19947, set_base=Pin(14))  # 20kHz, & 20 steps per wave = 1kHz wave, adjusted to 997,426KHz
sm.active(1)

def transmit(data):
    preamble_len = 13
    sm.exec("set(pins, 0b00001)") #enable tx
    time.sleep(0.01)
    for count, value in enumerate(data): 
        if count == 0:                            # first value
            # print('first value')
            sm.put((value <<8 )+ preamble_len)    # <0><value><start>
        else:
            if count == len(data)-1:              # last value
                #print('last',value)
                sm.put((0x01 << 16)+(value <<8 )) # <end><value><0>
            else:                                 # mid packet
                sm.put((value <<8 ))              # <0><value><0>
    time.sleep(0.05)
    sm.exec("set(pins, 0b00000)")                 # disable tx
while True:
    tx(data)
    time.sleep(1.5)
sm.active(0)

transmit(b'Hello World')
