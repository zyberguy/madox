TARGET=oddbot-launchpad
CC=msp430-gcc
CFLAGS=-Os -Wall -g -mmcu=msp430x2231

OBJS=$(TARGET).o

all: $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET).elf $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $<

clean:
	rm -fr $(TARGET).elf $(OBJS)

install: all
	mspdebug rf2500 "prog $(TARGET).elf"
