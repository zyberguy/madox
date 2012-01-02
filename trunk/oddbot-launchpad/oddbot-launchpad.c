/***********************************************************************
Oddbot Mecanum Wheel control using a Wii Nunchuk & MSP430 (msp430g2231)

                          www.madox.net

This is demonstration code to use the Texas Instruments Launchpad and a
Wii wireless nunchuk to control the 'OddBot'.

The 'OddBot' [http://www.odd.org.nz/oddbot.html] is a Mecanum wheeled
base derived from Madox Rover [http://www.madox.net/blog/?p=803].  The
design is similar but the OddBot has far superior documentation and
more practical mounting arrangements.  The carrier tray to hold the
Launchpad and Breadboard is designed to fit the OddBot.

WARNING - Do not connect the battery pack when USB is connected!!!

John Chan / Madox - www.madox.net
========================================================================
- Basic Operation

- MSP430 on TI Launchpad will control 4 servos driving Mecanum wheels
- MSP430 command input will come via a Wii Nunchuk, specifically the
  analog joystick input.
- The TI Launchpad's onboard regulator will be used to power the device,
  and the Wii wireless adapter.  The battery pack will be connected to
  tie points TP1 and TP3 for the regulator to supply 3.3V, the battery
  pack will directly power the servos.

This code is designed for Mecanum Wheels to be arranged in the following
configuration :-

         F
       _____
   [\]|2   1|[/]
L     |     |      R
   [/]|3___0|[\]

         B
------------------------------------------------------------------------
- Bill of Materials
* OddBot base (4 x Servos + 4 x Wheels + Frame)
  [http://www.odd.org.nz/oddbot.html]
* Oddbot-Launchpad Carrier
  [http://www.madox.net/]
* Texas Instruments Launchpad with msp430g2231
  [http://www.ti.com/tool/msp-exp430g2]
* Mini Breadboard
  [http://www.seeedstudio.com/]
* Wii Nunchuk Breakout board
  [http://littlebirdelectronics.com/products/wiichuck-adapter]
* 6 x AA Cell Battery Holder
* Miscellaneous Components - Header Pins, Jumper Wires, Battery Holder
------------------------------------------------------------------------
- Nunchuk

Supports 400 kHz Fast I2C
Pinout (Top left = 1, clockwise)
* 1 - SDA
* 2 - ACC (Connected to VCC)
* 3 - VCC
* 4 - SCL
* 5 - N/C
* 6 - GND
Address 0x52
0x40,0x00 Init
Read 6 bytes
(27,127,227) [100]
Byte 1 - X Stick - Left = 0x00, Mid = 0x80, Right = 0xFF
Byte 2 - Y Stick - Down = 0x00, Mid = 0x80, Up    = 0xFF
Byte 3 - X Accel - Min  = 0x00, Mid = 0x80, Max   = 0xFF
Byte 4 - Y Accel - Min  = 0x00, Mid = 0x80, Max   = 0xFF
Byte 5 - Z Accel - Max  = 0x00, Mid = 0x80, Max   = 0xFF
Byte 6 - Buttons - B0:B1 are C/Z buttons
                     3 = All Released
                     2 = Z Pressed
                     1 = C Pressed
                     0 = C+Z Pressed
                   Rest of bits are LSBs of accel and mostly useless.
                   (Not even provided on cheap eBay Wireless Nunchuk)

- Control Mapping

C - Start/Re-zero Joystick
Z - Rotate Mode
C+Z - Not used
Joystick Y - Forward/Back movement
Joystick X - Sideways movement (Normal Mode) or Rotation (Rotate Mode)
------------------------------------------------------------------------
- MSP430 - msp430g2231

Run clock at default calibrated 1 MHz
  I2C at Clock/8 or 125 kHz
  Timer A at Clock/8 or 125 kHz
    Servo pulses are 1.0 ms to 2.0 ms
    1.0 ms = 125 cycles @ 125 kHz
    1.5 ms = 187(.5) cycles @ 125 kHz
    2.0 ms = 250 cycles @ 125 kHz
      125 cycle for 1 ms-2 ms, i.e. resolution of 1/125.
      ~62 levels of speed control in forward/reverse

* Port - Pin(14) - Pin (16) - Function
* P1.0 - 2       - 1        - Servo 1 Out - Wheel 0
* P1.1 - 3       - 2        - Servo 2 Out - Wheel 1
* P1.2 - 4       - 3        - Servo 3 Out - Wheel 2
* P1.3 - 5       - 4        - Servo 4 Out - Wheel 3
* P1.4 - 6       - 5        - #SPI Chip Select (For PS2 controller)
* P1.5 - 7       - 6        - #I2C Clk In / SPI Clk In/Out
* P1.6 - 8       - 7        - I2C Clk / SPI DO
* P1.7 - 9       - 8        - IC2 Data / SPI / DI
* P2.6 - 13      - 12       - #Spare
* P2.7 - 12      - 11       - #Spare
* /RST - 10      - 9        - Reset button (Launchpad)
* TEST - 11      - 10       - #Test
* VCC  - 1       - 15,16    - 3.3V +ve
* VSS  - 14      - 13,14    - 3.3V GND

# Items are not used in this application
# DIP version is Pin(14)
------------------------------------------------------------------------
- References

msp430g2231.pdf [http://www.ti.com/lit/gpn/msp430g2231]
slau144h.pdf [www.ti.com/lit/ug/slau144h/slau144h.pdf]
***********************************************************************/

//Enough with the huge header block, the actual code starts here!!!!!!!!

#include <msp430.h>

#define NUM_SERVOS 4
#define SERVO_CAP(x) ((x < 125) ? 125 : ((x > 250) ? 250 : x))
#define ABS(x) ( x < 0 ? -x : x )

#define NUNCHUK_BUTTON_NONE 3
#define NUNCHUK_BUTTON_Z 2
#define NUNCHUK_BUTTON_C 1
#define NUNCHUK_BUTTON_CZ 0

unsigned int servo_counter = NUM_SERVOS;

//Initialize servo positions to 'neutral'
unsigned int servo_pos[NUM_SERVOS] = {187, 187, 187, 187};

//Note there is 'hard-coding' of these bit definitions in various places
unsigned int servo_pin[NUM_SERVOS] = {BIT0, BIT1, BIT2, BIT3};

//Mapping tables for wheel motion directions
//F matrix is reversed from MWRover, 'Up' is Y +ve on Nunchuk.
unsigned int F[NUM_SERVOS] = {1,1,-1,-1};
unsigned int R[NUM_SERVOS] = {1,-1,-1,1};
unsigned int CW[NUM_SERVOS] = {-1,-1,-1,-1};
unsigned int servo_centre[NUM_SERVOS] = {187, 187, 187, 187};

volatile unsigned int delay_counter = 0; //Incremented by pwm_set()

static void __inline__ delay(register unsigned int n)
{
  __asm__ __volatile__ (
  "1: \n"
  " dec %[n] \n"
  " jne 1b \n"
    : [n] "+r"(n));
}

void init()
{
  //Stop Watchdog
  WDTCTL = WDTPW + WDTHOLD;

  //Set DCO Frequency
  //(slau144h.pdf 5.2.5.2)
  BCSCTL1 = CALBC1_1MHZ;
  DCOCTL  = CALDCO_1MHZ;
  //Set ACLK to VLOCLK, 4-20kHz, 12kHz typ.  //Not used?
  BCSCTL3 = LFXT1S_2;
}

void servo_init()
{
  //Servo Init
  //(slau144h.pdf 8.2.2, 8.2.3, 8.2.5)
  P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3); //Clear outputs
  P1DIR |= (BIT0 + BIT1 + BIT2 + BIT3);  //Set output direction
  P1SEL &= ~(BIT0 + BIT1 + BIT2 + BIT3); //IO Function Select

  //Set Timer
  //(slau144h.pdf 12.3.1)
  TACTL = TASSEL_2 + MC_1 + ID_3; //SMCLK, Up Mode to TACCR0, Clk/8
  //(slau144h.pdf 12.3.4)
  TACCTL0 = CCIE; //Capture/Compare Interrupt Enable
  TACCR0 = 187; //~1.5ms @ 125kHz
}

__attribute__((interrupt(TIMERA0_VECTOR)))
void pwm_set()
{
  servo_counter++;
  if (servo_counter > NUM_SERVOS){
    delay_counter++;  //Increment Delay Counter
    servo_counter = 0;
  }

  P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3);  //Clear outputs

  if (servo_counter == NUM_SERVOS){
    TACCR0 = 1875;  //15ms delay gap after end of servo 4
    //So the period between pulses is slightly variable between
    //19 ms - 23 ms, should be good enough for most servos
  } else {
    P1OUT |= servo_pin[servo_counter];    //Set servo pin high
    TACCR0 = servo_pos[servo_counter];    //Set capture for this pin
  }
}

void i2c_init()
{
  //SDA, SCL enable, Master Mode, USI Reset State
  //(slau144h.pdf 14.2.4.1, 14.3.1)
  USICTL0 = USIPE7 | USIPE6 | USIMST | USISWRST;
  //Mode I2C, not bothering with interrupts
  //(slau144h.pdf 14.2.4, 14.3.2)
  USICTL1 = USII2C;
  //Clock/8, Clock=SMCLK, SCL Inactive High
  //(slau144h.pdf 14.2.4, 14.3.3)
  USICKCTL = USIDIV_3 | USISSEL_2 | USICKPL;
  //Release USI Reset State
  USICTL0 &= ~USISWRST;
}

void i2c_start()
{
  //I2C START Condition
  //(slau144h.pdf 14.2.4.5)
  USISRL = 0;
  USICTL0 |= USIGE | USIOE;
  USICTL0 &= ~USIGE;
}

void i2c_stop()
{
  //I2C STOP Condition
  //(slau144h.pdf 14.2.4.6)
  USICTL0 |= USIOE;
  USISRL = 0;
  USICNT = 1;
  while(!(USICTL1 & USIIFG)); //Wait for USIIFG
  USISRL = 0xFF;
  USICTL0 |= USIGE;
  USICTL0 &= ~(USIGE | USIOE);
}

unsigned char i2c_writebyte(unsigned char byte)
{
  //I2C Write single byte
  //(slau144h.pdf 14.2.4.3)
  USISRL = byte;
  USICTL0 |= USIOE;
  USICNT = 8;
  while(!(USICTL1 & USIIFG)); //Wait for USIIFG to signify complete
  //Now to receive the ACK bit
  USICTL0 &= ~USIOE;
  USICNT = 1;
  while(!(USICTL1 & USIIFG)); //Wait for USIIFG to signify complete
  return USISRL & BIT0;       //Return ACK bit (First bit)
}

unsigned char i2c_readbyte(unsigned char ack)
{
  //I2C Read single byte
  //(slau144h.pdf 14.2.4.4)
  unsigned char byte=0;

  USICTL0 &= ~USIOE;
  USICNT = 8;
  while(!(USICTL1 & USIIFG)); //Wait for USIIFG to signify complete
  byte = USISRL;

  USICTL0 |= USIOE;

  if(ack){
    USISRL = 0x00;
  } else {
    USISRL = 0xFF;
  }

  USICNT = 1;
  while(!(USICTL1 & USIIFG)); //Wait for USIIFG to signify complete

  return byte;
}

void nunchuk_init()
{
  //Slave address is 0x52,
  //Write address is thus 0xA4

  i2c_start();
  i2c_writebyte(0xA4);
  //Disable encryption init
  i2c_writebyte(0xF0);
  i2c_writebyte(0x55);
  i2c_stop();
  delay(300); //Was 30000

  i2c_start();
  i2c_writebyte(0xFB);
  i2c_writebyte(0x00);
  i2c_stop();
  delay(300); //Was 30000
}

void nunchuk_request()
{
  //Slave address is 0x52,
  //Write address is thus 0xA4
  //Start conversion
  i2c_start();
  i2c_writebyte(0xA4);
  i2c_writebyte(0x00);
  i2c_stop();
  delay(200);
}

void nunchuk_read(int *x, int *y,
                  int *ax, int *ay, int *az, int *buttons)
{
  //Slave address is 0x52,
  //Read Address is thus 0xA5
  nunchuk_request();

  //Read
  i2c_start();
  i2c_writebyte(0xA5);
  *x = i2c_readbyte(1); //Ack
  *y = i2c_readbyte(1); //Ack
  *ax = i2c_readbyte(1); //Ack
  *ay = i2c_readbyte(1); //Ack
  *az = i2c_readbyte(1); //Ack
  *buttons = (BIT0 + BIT1) & i2c_readbyte(0); //No ack, done
  i2c_stop();
}

int main(void)
{
  signed int i=0, x=0, y=0, ax=0, ay=0, az=0, buttons=0;
  signed int x_zero=0, y_zero=0;

  init();
  servo_init();
  i2c_init();

  nunchuk_init();

  nunchuk_read(&x,&y,&ax,&ay,&az,&buttons);

  //Wait for C button pressed to start
  while( buttons != NUNCHUK_BUTTON_C ){
    nunchuk_read(&x,&y,&ax,&ay,&az,&buttons);
    delay(10000);
  }
  //Zero joystick
  x_zero = x;
  y_zero = y;

  _BIS_SR(GIE); //Enable interrupts to start servo control

  while(1){

    nunchuk_read(&x,&y,&ax,&ay,&az,&buttons);

    //This is a hack, every once in a while my cheap eBay Nunchuk
    //returns non-sensical data.  Ignore and retry straight away.
    if(az == 0xFF) continue;

    //If Z button pressed, zero joystick
    if( buttons == NUNCHUK_BUTTON_C ){
      //Z-button zeros the unit
      x_zero = x;
      y_zero = y;
    }

    //Calculate the movement of the joystick
    //Since the full range of joystick movement is 128 and full range
    //of servo control is 62, we are applying some rough scaling here
    x = (x - x_zero) / 2;
    y = (y - y_zero) / 2;

    if( (ABS(x) < 10) && (ABS(y) < 10)){
      //Change is too small, set all motors neutral (filter out noise)
      for(i=0;i<NUM_SERVOS;i++){
        servo_pos[i] = SERVO_CAP(187);
      }
    } else {
      //Change is non trivial, proceed
      if( buttons == NUNCHUK_BUTTON_Z ){
        //Z button is pressed, we are in rotate mode
        for(i=0;i<NUM_SERVOS;i++){
          servo_pos[i] = SERVO_CAP(CW[i] * x +
                                   servo_centre[i]);
        }
      } else {
        //Z button was not pressed, we are in normal mode
        for(i=0;i<NUM_SERVOS;i++){
          servo_pos[i] = SERVO_CAP(F[i] * y +
                                   R[i] * x +
                                   servo_centre[i]);
        }
      }
    }

    //Note: any faster and my cheap eBay Wireless Nunchuk gives bad data
    //or makes it lose sync randomly...
    while(delay_counter < 20); //Do nothing for 20 delay cycles (~400ms)
    delay_counter = 0;
  }
}
