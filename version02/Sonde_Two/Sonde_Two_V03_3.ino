/*
 * connectingStuff, Oregon Scientific v2.1 Emitter
 * http://connectingstuff.net/blog/encodage-protocoles-oregon-scientific-sur-arduino/
 *
 * Copyright (C) 2013 olivier.lebrun@gmail.com
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

// Sonde_Two
// Version 03.3
// Programme basé sur connectingStuff, Oregon Scientific v2.1 Emitter.
// Il permet d'envoyé des trames au format des Oregons.
// Le décodage lui est un peu différent au niveau des IDs.
//
// Creation : 21/07/2015 - MoniThermo
// Modification : 03/08/2015 -> Complémenter IDcapteur
// Modification : 12/08/2015 -> Niveau batterie
//-----------------------------------------------------------------------------------------


#include "OneWire.h"
#include "DallasTemperature.h"  // librairie du capteur DS18B20
#include "LowPower.h"

//#define T&RH
                      
// definition pins DS18B20
#define SENSORS_POWER_PIN 10
#define DS18B20_SENSOR_DATA_PIN 9

// definition tension batterie
#define BATTERY_VOLTAGE_UNDEFINED_VALUE  -1
#define ADC_REF_VOLTAGE 3.35
#define DEVICE_BATTERY_VOLTAGE_PIN  A0

// variables Globales DS18B20
float temperature = 0.00;// variable de stockage de la temperature

// variables Globales Batterie
float batterie = 0.00;  // variable de stockage de la temperature

// Variables Globales ID
unsigned char pinID[] = {2, 3, 5, 6, 7, 8, 11, 12};

OneWire oneWire(DS18B20_SENSOR_DATA_PIN);
DallasTemperature DS18B20Sensors(&oneWire);

const byte TX_PIN = 4;
 
const unsigned long TIME = 512;
const unsigned long TWOTIME = TIME*2;
 
#define SEND_HIGH() digitalWrite(TX_PIN, HIGH)
#define SEND_LOW() digitalWrite(TX_PIN, LOW)
 
// Buffer for Oregon message
#ifdef T&RH
  byte OregonMessageBuffer[9];
#else
  byte OregonMessageBuffer[8];
#endif

/**
 * \brief    Send logical "0" over RF
 * \details  azero bit be represented by an off-to-on transition
 * \         of the RF signal at the middle of a clock period.
 * \         Remenber, the Oregon v2.1 protocol add an inverted bit first
 */
inline void sendZero(void)
{
  SEND_HIGH();
  delayMicroseconds(TIME);
  SEND_LOW();
  delayMicroseconds(TWOTIME);
  SEND_HIGH();
  delayMicroseconds(TIME);
}
 
/**
 * \brief    Send logical "1" over RF
 * \details  a one bit be represented by an on-to-off transition
 * \         of the RF signal at the middle of a clock period.
 * \         Remenber, the Oregon v2.1 protocol add an inverted bit first
 */
inline void sendOne(void)
{
   SEND_LOW();
   delayMicroseconds(TIME);
   SEND_HIGH();
   delayMicroseconds(TWOTIME);
   SEND_LOW();
   delayMicroseconds(TIME);
}
 
/**
* Send a bits quarter (4 bits = MSB from 8 bits value) over RF
*
* @param data Source data to process and sent
*/
 
/**
 * \brief    Send a bits quarter (4 bits = MSB from 8 bits value) over RF
 * \param    data   Data to send
 */
inline void sendQuarterMSB(const byte data)
{
  (bitRead(data, 4)) ? sendOne() : sendZero();
  (bitRead(data, 5)) ? sendOne() : sendZero();
  (bitRead(data, 6)) ? sendOne() : sendZero();
  (bitRead(data, 7)) ? sendOne() : sendZero();
}
 
/**
 * \brief    Send a bits quarter (4 bits = LSB from 8 bits value) over RF
 * \param    data   Data to send
 */
inline void sendQuarterLSB(const byte data)
{
  (bitRead(data, 0)) ? sendOne() : sendZero();
  (bitRead(data, 1)) ? sendOne() : sendZero();
  (bitRead(data, 2)) ? sendOne() : sendZero();
  (bitRead(data, 3)) ? sendOne() : sendZero();
}
 
/******************************************************************/
/******************************************************************/
/******************************************************************/
 
/**
 * \brief    Send a buffer over RF
 * \param    data   Data to send
 * \param    size   size of data to send
 */
void sendData(byte *data, byte size)
{
  for(byte i = 0; i < size; ++i)
  {
    sendQuarterLSB(data[i]);
    sendQuarterMSB(data[i]);
  }
}
 
/**
 * \brief    Send an Oregon message
 * \param    data   The Oregon message
 */
void sendOregon(byte *data, byte size)
{
    sendPreamble();
    //sendSync();
    sendData(data, size);
    sendPostamble();
}
 
/**
 * \brief    Send preamble
 * \details  The preamble consists of 16 "1" bits
 */
inline void sendPreamble(void)
{
  byte PREAMBLE[]={0xFF,0xFF};
  sendData(PREAMBLE, 2);
}
 
/**
 * \brief    Send postamble
 * \details  The postamble consists of 8 "0" bits
 */
inline void sendPostamble(void)
{
#ifdef T&RH
  byte POSTAMBLE[]={0x00};
  sendData(POSTAMBLE, 1); 
#else
  sendQuarterLSB(0x00);
#endif
}
 
/**
 * \brief    Send sync nibble
 * \details  The sync is 0xA. It is not use in this version since the sync nibble
 * \         is include in the Oregon message to send.
 */
inline void sendSync(void)
{
  sendQuarterLSB(0xA);
}
 
/******************************************************************/
/******************************************************************/
/******************************************************************/
 
/**
 * \brief    Set the sensor type
 * \param    data       Oregon message
 * \param    type       Sensor type
 */
inline void setType(byte *data, byte* type)
{
  data[0] = type[0];
  data[1] = type[1];
}
 
/**
 * \brief    Set the sensor channel
 * \param    data       Oregon message
 * \param    channel    Sensor channel (0x10, 0x20, 0x30, 0x50 pour monithermo)
 */
inline void setChannel(byte *data, byte channel)
{
    data[2] = channel;
}//fin setChannel

 
//------------------------------------------------------------------
//      
//      Rôle : Lecture de l'ID défini par le switch physique
//
//      Entrée : buffer d'envoi
//      Sortie : /
//
//      //-----------------------------------------//
//      //| s1 | s2 | s3 | s4 | s5 | s6 | s7 | s8 |//
//      //-----------------------------------------//
//      //| 2  |  3 | 5  | 6  | 7  | 8  | 11 | 12 |//
//      //-----------------------------------------//
//
//      ex : 80 -> 0101 0000 => data[3] -> 0000 0101 (LSB en tete)
//------------------------------------------------------------------
inline void setId(byte *data)
{
  unsigned char IDcapteur = 0;
  for(unsigned char nb = 0; nb < sizeof(pinID); nb++)
  {
    IDcapteur |= digitalRead(pinID[nb]) << (sizeof(pinID) - (nb+1));
  }
  IDcapteur = ~IDcapteur;            // Complément IDcapteur
//  Serial.print("IDcapteur : ");
//  Serial.println(IDcapteur, BIN);
  data[3] |= 0x0F&IDcapteur >> 4;
  data[3] |= 0xF0&IDcapteur << 4;
//  Serial.print("data[3] : ");
//  Serial.println(data[3], HEX);
}// fin setId


/**
 * \brief    Set the sensor battery level
 * \param    data       Oregon message
 * \param    level      Battery level (pour cent)
 */
void setBatteryLevel(byte *data, byte level)
{
  if(level == 90)
  {
    data[4] = 0x09;
  }
  else if(level == 50)
  {
    data[4] = 0x05;
  }
  else if(level == 10)
  {
    data[4] = 0x01;
  }
}// fin setBatteryLevel

/**
 * \brief    Set the sensor temperature
 * \param    data       Oregon message
 * \param    temp       the temperature
 */
void setTemperature(byte *data, float temp)
{
  // Set temperature sign
  if(temp < 0)
  {
    data[6] = 0x08;
    temp *= -1; 
  }
  else
  {
    data[6] = 0x00;
  }
 
  // Determine decimal and float part
  int tempInt = (int)temp;
  int td = (int)(tempInt / 10);
  int tf = (int)round((float)((float)tempInt/10 - (float)td) * 10);
 
  int tempFloat =  (int)round((float)(temp - (float)tempInt) * 10);
 
  // Set temperature decimal part
  data[5] = (td << 4);
  data[5] |= tf;
 
  // Set temperature float part
  data[4] |= (tempFloat << 4);
}
 
/**
 * \brief    Set the sensor humidity
 * \param    data       Oregon message
 * \param    hum        the humidity
 */
void setHumidity(byte* data, byte hum)
{
    data[7] = (hum/10);
    data[6] |= (hum - data[7]*10) << 4;
}
 
/**
 * \brief    Sum data for checksum
 * \param    count      number of bit to sum
 * \param    data       Oregon message
 */
int Sum(byte count, const byte* data)
{
  int s = 0;
 
  for(byte i = 0; i<count;i++)
  {
    s += (data[i]&0xF0) >> 4;
    s += (data[i]&0xF);
  }
 
  if(int(count) != count)
    s += (data[count]&0xF0) >> 4;
 
  return s;
}
 
/**
 * \brief    Calculate checksum
 * \param    data       Oregon message
 */
void calculateAndSetChecksum(byte* data)
{
#ifdef T&RH
    data[8] = ((Sum(8, data) - 0xa) & 0xFF);
#else
    int s = ((Sum(6, data) + (data[6]&0xF) - 0xa) & 0xff);
 
    data[6] |=  (s&0x0F) << 4;     data[7] =  (s&0xF0) >> 4;
#endif
}
 
/******************************************************************/
/******************************************************************/
/******************************************************************/


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Mettre en sommeil le microcontroleur pendant x secondes
//
//  Entree : seconds : duree du sommeil en secondes
//  Sortie : /
//
//---------------------------------------------------------------------------------------------------------------------------------
void sleep(unsigned long seconds) 
{
  unsigned long counterStop = (unsigned long) (seconds / 1.08) + 1;

  for(unsigned long counter = 0 ; counter < counterStop; counter++) 
  {
    LowPower.powerDown(SLEEP_1S, ADC_OFF, BOD_OFF); // Mise en sommeil
  }
}// fin sleep


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Relever la température
//
//  Entrée : /
//  Sortie : /
//
//  Algorithme : -> Alimenter le capteur DS18B20
//               -> Récupérer la valeur de la température
//               -> éteindre le capteur
//
//---------------------------------------------------------------------------------------------------------------------------------
void Acquisition_Temp(void)
{
  // Prise de temp√©rature
  digitalWrite(SENSORS_POWER_PIN, HIGH);
  DS18B20Sensors.requestTemperatures();
  temperature = DS18B20Sensors.getTempCByIndex(0);
  digitalWrite(SENSORS_POWER_PIN, LOW);
  
  Serial.println(temperature);
}// fin Aquisition_Temp


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Envoi du message
//
//  Entrée : /
//  Sortie : /
//
//  Algorithme : -> Ajouter le niveau batterie
//               -> Ajouter la temperature
//               -> Calculer le Checksum
//               -> Afficher le message 
//               -> 1er envoi du message
//               -> Attente
//               -> 2ème envoi du message (protocole oregon V2.1)
//
//---------------------------------------------------------------------------------------------------------------------------------
void msg (void)
{
  // Niveau Batterie
  if(batterie >= 2.6)
  {
    setBatteryLevel(OregonMessageBuffer, 90);
  }
  else if((batterie > 2) && (batterie < 2.6))
  {
    setBatteryLevel(OregonMessageBuffer, 50);
  }
  else if (batterie <= 2)
  {
    setBatteryLevel(OregonMessageBuffer, 10);
  }

  setTemperature(OregonMessageBuffer, temperature);
 
  // Calculate the checksum
  calculateAndSetChecksum(OregonMessageBuffer);
 
  // Show the Oregon Message
  for (byte i = 0; i < sizeof(OregonMessageBuffer); ++i)   {     Serial.print(OregonMessageBuffer[i] >> 4, HEX);
    Serial.print(OregonMessageBuffer[i] & 0x0F, HEX);
  }
  Serial.println("");
  
  // Send the Message over RF
  sendOregon(OregonMessageBuffer, sizeof(OregonMessageBuffer));
  
  // Send a "pause"
  SEND_LOW();
  
  delayMicroseconds(TWOTIME*8);
  
  // Send a copie of the first message. The v2.1 protocol send the
  // message two time
  sendOregon(OregonMessageBuffer, sizeof(OregonMessageBuffer));
 
  // Wait for 30 seconds before send a new message
  SEND_LOW(); 

}//fin msg


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Recuperer la tension des piles
//
//  Entrée : /
//  Sortie : tension des piles (float)
//
//---------------------------------------------------------------------------------------------------------------------------------
float tension_pile (void)
{
  float deviceBatteryVoltage = BATTERY_VOLTAGE_UNDEFINED_VALUE;
  
  unsigned long accuAdcReadings = 0;
  
  // lecture de la valeur (x10)    
  for(byte i=0 ; i < 10; i++) {
    accuAdcReadings += analogRead(DEVICE_BATTERY_VOLTAGE_PIN);
  }
  
  // moyenne des valeurs
  if(accuAdcReadings > 0)
  { 
    deviceBatteryVoltage = accuAdcReadings * ADC_REF_VOLTAGE * 115.0 / (10 * 1024 * 33.0);
  }
  return deviceBatteryVoltage;
}// fin tension_pile

//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Initialisation des pins ID (switch) en sortie
//
//  Entrée : /
//  Sortie : /
//
//---------------------------------------------------------------------------------------------------------------------------------
void initID(void)
{
  for(unsigned char nb = 0; nb < (sizeof(pinID) - 1); nb++)
  {
    pinMode(pinID[nb], INPUT);
  }
}//fin initID


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
//    Initialisation
//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void setup()
{
  pinMode(TX_PIN, OUTPUT);
  
  Serial.begin(9600);
  Serial.println("*firmware capteur 433MHz - V03 -  22/07/2015*");
 
  // Initialisation Emetteur
  SEND_LOW(); 
 
// 1 : temp   ;  2 : T+RH
// A : obligatoire
// 1 : Yun    ;  2 : RPI
// 1 : non RF ;  2 : 433MHz  ;  3 : BLE
#ifdef T&RH 
  // Create the Oregon message for a temperature/humidity sensor (THGR2228N)
  byte ID[] = {0x2A,0x22};
#else
  // Create the Oregon message for a temperature only sensor (TNHN132N)
  byte ID[] = {0x1A,0x22};
#endif 

  // Identification sonde
  setType(OregonMessageBuffer, ID);       // ID MoniThermo
  setChannel(OregonMessageBuffer, 0x50);  // canal 4
  setId(OregonMessageBuffer);             // ID des switchs
  
  // initialisation DS18B20
  pinMode(SENSORS_POWER_PIN, OUTPUT);
  digitalWrite(SENSORS_POWER_PIN, HIGH);
  while(DS18B20Sensors.getDeviceCount() == 0)
  {
    DS18B20Sensors.begin();
    Serial.println("begin");
  }
  digitalWrite(SENSORS_POWER_PIN, LOW);
  
}//fin initialisation

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
//    Programme Principal : Relever la temperature et l'envoyer par RF toutes les minutes
//    
//    delay exprimé en ms
//    Algorigramme : -> Relever la température
//                   -> Relever la tension des piles
//                   -> Création du message
//                   -> Envoi du message
//                   -> Attente (sommeil)
//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void loop()
{
  Acquisition_Temp();
  batterie = tension_pile();
  Serial.print("batterie : ");
  Serial.println(batterie);
  msg();
  Serial.println("Attente...");
  delay(100);
  sleep(120);  // 2 min
//  delay(100);
}//fin programme principal

