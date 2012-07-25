// ======================================================================
// USBtiny template application
//
// Copyright 2006-2010 Dick Streefland
//
// This is free software, licensed under the terms of the GNU General
// Public License as published by the Free Software Foundation.
// ======================================================================

#include "usb.h"
#include<avr/io.h>
#define F_CPU 1500000UL
#include<util/delay.h>

#define INITPOS 530			// ocr value for zero degree position.
#define ENDPOS  2560		// ocr value for 180 degree position.
// Please note that INITPOS and ENDPOS must be adjusted according to the particular
// servo motor. It is NOT constant and needs to be determined by trial and error

void PWMinit(void)
{
	// fast PWM mode will be used for OCRA and OCRB
	// we have frequency of oscillations as 1MHz
	// The prescaling will be 1 to give higher resolution
	// To get 50Hz, we need the ICR1 value to be 19,999
	
	DDRB |= (1<<PB3)|(1<<PB4);			// make the pins output for the PWM channels
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

// ----------------------------------------------------------------------
// Handle a non-standard SETUP packet.
// ----------------------------------------------------------------------
extern	byte_t	usb_setup ( byte_t data[8] )
{
	return 8;	// simply echo back the setup packet
}

// ----------------------------------------------------------------------
// Handle an IN packet. (USBTINY_CALLBACK_IN==1)
// ----------------------------------------------------------------------
extern	byte_t	usb_in ( byte_t* data, byte_t len )
{
	return 0;
}

// ----------------------------------------------------------------------
// Handle an OUT packet. (USBTINY_CALLBACK_OUT==1)
// ----------------------------------------------------------------------
extern	void	usb_out ( byte_t* data, byte_t len )
{
	// Update the servo motor if the packets is correct. Glow an LED else.
	if(len == 9){
		// Switch off error LED and switch on busy LED.
		PORTB &= ~(1 << PB0);
		PORTB |= (1 << PB1);
		int angle1 = 0;
		int angle2 = 0;
		angle1 += data[3] - '0';			// convert the characters to angles
		angle1 += 10*(data[2] - '0');
		angle1 += 100*(data[1] - '0');

		angle2 += data[7] - '0';
		angle2 += 10*(data[6] - '0');
		angle2 += 100*(data[5] - '0');

		updateOCR1A(angle1);				// load the timer registers
		updateOCR1B(angle2);
		// Switch off busy LED
		PORTB &= ~(1 << PB1);
	}
	else{
		// The first LED is the red LED, which glows if an error
		DDRB |= (1 << PB0);
	}
		
}

// ----------------------------------------------------------------------
// Main
// ----------------------------------------------------------------------
extern	int	main ( void )
{
	PWMinit();
	usb_init();
	while(1){
		usb_poll();
	}
}
