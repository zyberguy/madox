gobgobi_loader: gobi_loader.c
	gcc -Wall gobi_loader.c -o gobi_loader

all: gobi_loader

install: gobi_loader
	install gobi_loader /lib/udev
	install 60-gobi.rules /etc/udev/rules.d
	mkdir -p /lib/firmware
	udevadm control --reload-rules

uninstall:
	-rm /lib/udev/gobi_loader
	-rm /etc/udev/rules.d/60-gobi.rules

clean:
	@-rm gobi_loader
	@-rm *~
