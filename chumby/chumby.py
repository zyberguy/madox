"""
Chumby GPIO Control

This is Infocast centric but can be easily adapted for the other Chumby
Falconwing based boards.

Parameter 'gpio' in the functions expect an 8bit char that corresponds
with GPMI_D07...GPMI_D00 (D7...D0) on Connector P200.

READ ME : The write is kind of messy at the moment for Infocast, should
only need to write to DOUT (Single first byte) for Infocast.

Revision : $Revision$

Author : madox@madox.net
Website : http://www.madox.net/

Reference: http://www.freescale.com/files/dsp/doc/ref_manual/IMX23RM.pdf

Notes :

*Initialize 
**Set HW_PINCTRL_MUXSELx to set for GPIO control
**Set HW_PINCTRL_DRIVEx for desired drive strength and pin voltage
**Set HW_PINCTRL_PULLx as required to enable pullups
**Set HW_PINCTRL_DOUTx to for initial drive value
**Set HW_PINCTRL_DOEx to set output/input direction (output enable)
*Normal
**Set HW_PINCTRL_DOUTx to change output
**Read HW_PINCTRL_DINx to read input

For Infocast, everything is on GPMI_D07->GPMI_D00 or bank 0

MUXSEL - Each pin is 2 bits. e.g. D00 is bits 0:1
  0b11 = GPIO
DRIVE - Each pin is 2 bits. e.g. D00 is bits 0:1
  0b00 = 4mA
  0b01 = 8mA
  0b10 = 12mA
  0b11 = reserved
PULL - Each pin is 1 bits. e.g. D00 is bit 0
  0b1 = Pullup
DOUT - Each pin is 1 bits. e.g. D00 is bit 0
DIN - Each pin is 1 bits. e.g. D00 is bit 0
DOE - Each pin is 1 bits. e.g. D00 is bit 0
  0b1 = Output

GPMI_RDY0 is attached to LED on ChumbyHackerBoard.
"""
__version__ = "$Revision: $"

#This is a hack as using python mmap offset=0x80018000 doesn't work.
#This is the largest offset that works on a chumby (multiple of 4096)
PYTHON_MMAP_OFFSET    = 0x7FFFF000
REG_PINCTRL_BASE      = 0x80018000
HW_PINCTRL_MUXSEL0    = 0x100 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_MUXSEL0_SET= 0x104 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_MUXSEL0_CLR= 0x108 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_MUXSEL0_TOG= 0x10C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

HW_PINCTRL_DRIVE0     = 0x200 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DRIVE0_SET = 0x204 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DRIVE0_CLR = 0x208 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DRIVE0_TOG = 0x20C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

HW_PINCTRL_PULL0      = 0x400 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_PULL0_SET  = 0x404 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_PULL0_CLR  = 0x408 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_PULL0_TOG  = 0x40C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

HW_PINCTRL_DOUT0      = 0x500 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOUT0_SET  = 0x504 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOUT0_CLR  = 0x508 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOUT0_TOG  = 0x50C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

HW_PINCTRL_DIN0       = 0x600 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DIN0_SET   = 0x604 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DIN0_CLR   = 0x608 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DIN0_TOG   = 0x60C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

HW_PINCTRL_DOE0       = 0x700 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOE0_SET   = 0x704 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOE0_CLR   = 0x708 + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET
HW_PINCTRL_DOE0_TOG   = 0x70C + REG_PINCTRL_BASE - PYTHON_MMAP_OFFSET

import mmap
import struct

#GPIO Tested and works!
class GPIO():
  def __init__(self):
    #Open /dev
    self.file = open("/dev/mem", "r+b")
    self.mem = mmap.mmap(self.file.fileno(), 0x20000, offset=PYTHON_MMAP_OFFSET)
    self.mem[HW_PINCTRL_MUXSEL0_SET:HW_PINCTRL_MUXSEL0_SET+4] = self._pack_32bit(0xFFFF)

  def _pack_32bit(self, value):
    return struct.pack("<L", value)
  
  def set_drive(self, drive8ma, drive12ma):
    #Clear everything first, so by default everything is actually 4mA
    self.mem[HW_PINCTRL_DRIVE0_CLR:HW_PINCTRL_DRIVE0_CLR+4] = self._pack_32bit(0x0000FFFF)
    drive = 0
    for i in range (8):
      #8mA takes precedence
      if (1<<i) & drive8ma:
        drive = drive | (0b01 << i*2)
      elif (1<<i) & drive12ma:
        drive = drive | (0b10 << i*2)
    self.mem[HW_PINCTRL_DRIVE0_SET:HW_PINCTRL_DRIVE0_SET+4] = self._pack_32bit(drive)

  def set_pullup(self, gpio):
    self.mem[HW_PINCTRL_PULL0:HW_PINCTRL_PULL0+4] = self._pack_32bit(gpio)
    
  def set_direction(self, gpio):
    self.mem[HW_PINCTRL_DOE0_SET:HW_PINCTRL_DOE0_SET+4] = self._pack_32bit(gpio)

  def read_input(self):
    return (struct.unpack("<L",self.mem[HW_PINCTRL_DIN0:HW_PINCTRL_DIN0+4])[0] & 0xFF)
  
  def write_output(self, gpio):
    self.mem[HW_PINCTRL_DOUT0:HW_PINCTRL_DOUT0+4] = self._pack_32bit(gpio | (struct.unpack("<L",self.mem[HW_PINCTRL_DIN0:HW_PINCTRL_DIN0+4])[0] & ~0xFF))
  def set_output(self, gpio):
    self.mem[HW_PINCTRL_DOUT0_SET:HW_PINCTRL_DOUT0_SET+4] = self._pack_32bit(gpio)
  def clear_output(self, gpio):
    self.mem[HW_PINCTRL_DOUT0_CLR:HW_PINCTRL_DOUT0_CLR+4] = self._pack_32bit(gpio)
  def toggle_output(self, gpio):
    self.mem[HW_PINCTRL_DOUT0_TOG:HW_PINCTRL_DOUT0_TOG+4] = self._pack_32bit(gpio)

#Coming soon
class i2c():
  def __init__(self):
    pass
