/*********************************************************************
Name: 			firmware.c
Target device: 	ATtiny2313
Written by:		Vishwanath
Dependencies:	None
Programmer:		USBtiny ISP or USBASP
*********************************************************************/

#include<avr/io.h>
#define F_CPU 1000000UL
#include<util/delay.h>
#include<inttypes.h>

// We will use 4800 bps and 1MHz frequency. that gives UBRR value as 12
// We will be using two pwm channels with timer1, ensuring very high resolution

#define INITPOS 530			// ocr value for zero degree position.
#define ENDPOS  2560		// ocr value for 180 degree position.
// Please note that INITPOS and ENDPOS must be adjusted according to the particular
// servo motor. It is NOT constant and needs to be determined by trial and error

void USARTinit(unsigned int ubrr_val)
{
	UBRRH = ubrr_val>>8;	// set the baud rate generator value
	UBRRL = ubrr_val;
	
	//enable the transmitter and receiver
	UCSRB |= (1<<TXEN)|(1<<RXEN);
	// select 8 bit transmission and one stop bit
	UCSRC |= (1<<USBS)|(3<<UCSZ0);
}

void serialWrite(unsigned char letter)
{
	while(!(UCSRA&(1<<UDRE)));	// dont do anything till the last transmission is complete
	UDR = letter;				// now write the letter
}

unsigned char serialRead(void)
{
	unsigned char letter;
	while(!(UCSRA&(1<<RXC)));	// wait till the buffer is ready
	letter = UDR;				// now read the data

	return letter;
}

void PWMinit(void)
{
	// fast PWM mode will be used for OCRA and OCRB
	// we have frequency of oscillations as 1MHz
	// The prescaling will be 1 to give higher resolution
	// To get 50Hz, we need the ICR1 value to be 19,999

	TCCR1A |= (1<<COM1A1)|(1<<COM1B1);		// clear OC1A,OC1B on match, set when TOP

	// We need fast PWM with TOP compared with ICR1
	// hence we need mode 14 in waveform generation mode
	TCCR1A |= (1<<WGM11);
	TCCR1B |= (1<<WGM13)|(1<<WGM12);

	TCCR1B |= (1<<CS10);					// no prescaling of clock											
	ICR1 = 19999;							// load 19999 into ICR1 register
	OCR1A = INITPOS;						// initialise to zero
	OCR1B = INITPOS;
}

void updateOCR1A(int angle)
{
	uint16_t ocr1a_val = 0;	
	// we can get a total of 100 steps in between, but we dont need so many

	ocr1a_val = INITPOS + angle *((ENDPOS-INITPOS)/180);
	OCR1A = ocr1a_val;
}

void updateOCR1B(int angle)
{
	uint16_t ocr1b_val = 0;	
	// we can get a total of 100 steps in between, but not sure we need so many

	ocr1b_val = INITPOS + angle *((ENDPOS-INITPOS)/180);
	OCR1B = ocr1b_val;
}

int refresh(void)
{
	// we will assume our data frame to be '#xxx:xxx@'
	// the '#' is the beginning character,next is the first angle
	// and the ':' character is the delimiter. The next 3 are the second angle
	// and '@' is the end of frame

	char frame[9];
	int i = 0;

	frame[0] = serialRead();
	if (frame[0] == '#')				// wait for the start of frame
	{
		for(i=1;i<9;i++)
		{
			frame[i] = serialRead();	// read into frame array
			serialWrite('r');
		}
	}

	else
	{	
		return 1;
	}

	if (frame[8] == '@')
	{
		serialWrite('D');				// if we get the end of frame, send D, telling the 
										// computer that the frame is recieved
	}
	int angle1 = 0;
	int angle2 = 0;
	angle1 += frame[3] - '0';			// convert the characters to angles
	angle1 += 10*(frame[2] - '0');
	angle1 += 100*(frame[1] - '0');

	angle2 += frame[7] - '0';
	angle2 += 10*(frame[6] - '0');
	angle2 += 100*(frame[5] - '0');

	updateOCR1A(angle1);				// load the timer registers
	updateOCR1B(angle2);

	serialWrite('U');					// The microcontroller is ready to accept commands once again
	
	return 0;	
			 	 
}

int main(void)
{
	DDRB |= (1<<PB3)|(1<<PB4);			// make the pins output for the PWM channels
	USARTinit(12);						// initialise serial port and PWM
	PWMinit();
	serialWrite('U');					// The device will respond to the host through this character

	while(1)
	{
		serialWrite('U');				// Keep refreshing the device for receiving
		refresh();						// keep polling the serial port for data
	}	
}
