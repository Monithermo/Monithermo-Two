// Oregon V2 decoder modfied - Olivier Lebrun
// Oregon V2 decoder added - Dominique Pierre
// New code to decode OOK signals from weather sensors, etc.
// 2010-04-11 <jcw@equi4.com> http://opensource.org/licenses/mit-license.php
// $Id: ookDecoder.pde 5331 2010-04-17 10:45:17Z jcw $
//
// MoniThermo_Two
// Version 01.2
// Programme basé sur ookDecoder. Adapté à l'Arduino Yun
// Il permet de décoder les trames au format Oregon.
//
// Adaptation : 05/10/2014 - MoniThermo
//-----------------------------------------------------------------------------------------

#include <Bridge.h>
#include <FileIO.h>
#include <SoftwareSerial.h> 

// definition soft serial
#define DEBUG_TX_PIN 5
#define DEBUG_RX_PIN 255

SoftwareSerial softSerialDebug(DEBUG_RX_PIN, DEBUG_TX_PIN);

unsigned long int ts;
boolean blue_led = false;

//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Mettre en forme la trame
//
//---------------------------------------------------------------------------------------------------------------------------------
class DecodeOOK {
protected:
    byte total_bits, bits, flip, state, pos, data[25];
 
    virtual char decode (word width) =0;
 
public:
 
    enum { UNKNOWN, T0, T1, T2, T3, OK, DONE };
 
    DecodeOOK () { resetDecoder(); }
 
    bool nextPulse (word width) {
        if (state != DONE)
 
            switch (decode(width)) {
                case -1: resetDecoder(); break;
                case 1:  done(); break;
            }
        return isDone();
    }
 
    bool isDone () const { return state == DONE; }
 
    const byte* getData (byte& count) const {
        count = pos;
        return data;
    }
 
    void resetDecoder () {
        total_bits = bits = pos = flip = 0;
        state = UNKNOWN;
    }
 
    // add one bit to the packet data buffer

virtual void gotBit (char value)
{
  if(!(total_bits & 0x01))
  {
    data[pos] = (data[pos] >> 1) | (value ? 0x80 : 00);
  }
  total_bits++;
  pos = total_bits >> 4;
  
  if(pos == 2)
  {
    // Taille de trame par défaut (utilisée dans la majorité des sondes)
    unsigned char max_bits = 160;
 
    // Exceptions :
    if(data[0] == 0xEA)
    {
      if(data[1] == 0x4C) max_bits = 136; // TH132N : 68 * 2
      else if(data[1] == 0x7C) max_bits = 240; // UV138 : 120 * 2
    }
    else if(data[0] == 0x5A)
    {
      if(data[1] == 0x5D) max_bits = 176; // THGR918 : 88 * 2
      else if(data[1] == 0x6D)max_bits = 192; // BTHR918N : 96 * 2
    }
    else if(data[0] == 0x1A  && data[1] == 0x99)
      max_bits = 176; // WTGR800 : 88 * 2
    else if(data[0] == 0xDA  && data[1] == 0x78)
      max_bits = 144; // UVN800 : 72 * 2
    else if((data[0] == 0x8A || data[0] == 0x9A) && data[1] == 0xEC)
      max_bits = 208; // RTGR328N 104 * 2
    else if(data[0] == 0x2A)
    { 
      if(data[1] == 0x19) max_bits = 184; // RCR800 : 92 * 2
      else if(data[1] == 0x1d) max_bits = 168; // WGR918 : 84 * 2
    }
   }
 
   if (pos >= sizeof data)
   {
     softSerialDebug.println("sizeof data");
     resetDecoder();
     return;
   }
   state = OK;
}

 
    // store a bit using Manchester encoding
    void manchester (char value) {
        flip ^= value; // manchester code, long pulse flips the bit
        gotBit(flip);
    }
 
    // move bits to the front so that all the bits are aligned to the end
    void alignTail (byte max =0) {
        // align bits
        if (bits != 0) {
            data[pos] >>= 8 - bits;
            for (byte i = 0; i < pos; ++i)
                data[i] = (data[i] >> bits) | (data[i+1] << (8 - bits));
            bits = 0;
        }
        // optionally shift bytes down if there are too many of 'em
        if (max > 0 && pos > max) {
            byte n = pos - max;
            pos = max;
            for (byte i = 0; i < pos; ++i)
                data[i] = data[i+n];
        }
    }
 
    void reverseBits () {
        for (byte i = 0; i < pos; ++i) {
            byte b = data[i];
            for (byte j = 0; j < 8; ++j) {
                data[i] = (data[i] << 1) | (b & 1);
                b >>= 1;
            }
        }
    }
 
    void reverseNibbles () {
        for (byte i = 0; i < pos; ++i)
            data[i] = (data[i] << 4) | (data[i] >> 4);
    }
 
    void done () {
        while (bits)
            gotBit(0); // padding
        state = DONE;
    }
};
 
class OregonDecoderV2 : public DecodeOOK {
  public:  
 
    OregonDecoderV2() {}
 
    // add one bit to the packet data buffer
    virtual void gotBit (char value) {
        if(!(total_bits & 0x01))
        {
            data[pos] = (data[pos] >> 1) | (value ? 0x80 : 00);
        }
        total_bits++;
        pos = total_bits >> 4;
        if (pos >= sizeof data) {
            softSerialDebug.println("sizeof data");
            resetDecoder();
            return;
        }
        state = OK;
    }
 
    virtual char decode (word width) {
       if (200 <= width && width < 1200) {
            //softSerialDebug.println(width);
            byte w = width >= 700;
 
            switch (state) {
                case UNKNOWN:
                    if (w != 0) {
                        // Long pulse
                        ++flip;
                    } else if (w == 0 && 24 <= flip) {
                        // Short pulse, start bit
                        flip = 0;
                        state = T0;
                    } else {
                        // Reset decoder
                        return -1;
                    }
                    break;
                case OK:
                    if (w == 0) {
                        // Short pulse
                        state = T0;
                    } else {
                        // Long pulse
                        manchester(1);
                    }
                    break;
                case T0:
                    if (w == 0) {
                      // Second short pulse
                        manchester(0);
                    } else {
                        // Reset decoder
                        return -1;
                    }
                    break;
              }
        } else if (width >= 2500  && pos >= 8) {
            return 1;
        } else {
            return -1;
        }
        return 0;
    }
};
 
OregonDecoderV2 orscV2;
 
volatile word pulse;
 
void ext_int_1(void)
{
    static word last;
    // determine the pulse length in microseconds, for either polarity
    pulse = micros() - last;
    last += pulse;
}

//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Mettre en forme les données et les stocker
//
//  Entrée : data     -> buffer reçu
//  Sortie : température (float)
//
//---------------------------------------------------------------------------------------------------------------------------------
void reportSerial (const char* s, class DecodeOOK& decoder)
{
  byte pos;
  const byte* data = decoder.getData(pos);
//  softSerialDebug.print(s);
//  softSerialDebug.print(' ');
//  for (byte i = 0; i < pos; ++i) {
//      softSerialDebug.print(data[i] >> 4, HEX);
//      softSerialDebug.print(data[i] & 0x0F, HEX);
//  }
  
  date(); 
  // timestamp > 01/01/2014
  if (ts > 1388530800)
  { 
    // éteindre la del bleu si allumé
    if (blue_led == true)
    {
      Process led_OFF;
      led_OFF.runShellCommand("blink-stop");
      while(led_OFF.running());
      blue_led = false;
    }
    
    // Si le capteur est un THN132N (temperature)
    if(data[0] == 0xEA && data[1] == 0x4C)
    {
      File fichier_serveur = FileSystem.open("/MoniThermo/tmp/dataFile.txt", FILE_WRITE);
      fichier_serveur.print(data[3], HEX);
      fichier_serveur.print("|");
      fichier_serveur.print(channel(data));
      fichier_serveur.print("|");
      fichier_serveur.print(battery(data));
      fichier_serveur.print("|");
      fichier_serveur.print(ts);
      fichier_serveur.print("|");
      fichier_serveur.print(temperature(data));
      fichier_serveur.println("|");
      fichier_serveur.close();
      
      softSerialDebug.print(data[3], HEX);
      softSerialDebug.print("|");
      softSerialDebug.print(channel(data));
      softSerialDebug.print("|");
      softSerialDebug.print(battery(data));
      softSerialDebug.print("|");
      softSerialDebug.print(ts);
      softSerialDebug.print("|");
      softSerialDebug.print(temperature(data));
      softSerialDebug.println("|");
    } 
    
    // Si le capteur est un THGR228N (temperature + humidité)
    else if(data[0] == 0x1A && data[1] == 0x2D)
    {
      File fichier_serveur = FileSystem.open("/MoniThermo/tmp/dataFile.txt", FILE_WRITE);
      fichier_serveur.print(data[3], HEX);
      fichier_serveur.print("|");
      fichier_serveur.print(channel(data));
      fichier_serveur.print("|");
      fichier_serveur.print(battery(data));
      fichier_serveur.print("|");
      fichier_serveur.print(ts);
      fichier_serveur.print("|");
      fichier_serveur.print(temperature(data));
      fichier_serveur.print("|");
      fichier_serveur.print(humidity(data));
      fichier_serveur.println("|");
      fichier_serveur.close();
      
      softSerialDebug.print(data[3], HEX);
      softSerialDebug.print("|");
      softSerialDebug.print(channel(data));
      softSerialDebug.print("|");
      softSerialDebug.print(battery(data));
      softSerialDebug.print("|");
      softSerialDebug.print(ts);
      softSerialDebug.print("|");
      softSerialDebug.print(temperature(data));
      softSerialDebug.print("|");
      softSerialDebug.print(humidity(data));
      softSerialDebug.println("|");
    }
  }
  else
  {
    softSerialDebug.println("process led...");
    Process led_ON;
    led_ON.runShellCommand("blink-start 1");
    while(led_ON.running());
    softSerialDebug.println("fin process led");
    softSerialDebug.println("Attente...");
    blue_led = true;
    delay(300000);
  }
  decoder.resetDecoder();
}//fin reportSerial


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Extraire la température
//
//  Entrée : data     -> buffer reçu
//  Sortie : température (float)
//
//---------------------------------------------------------------------------------------------------------------------------------
float temperature(const byte* data)
{
    int sign = (data[6]&0x8) ? -1 : 1;
    float temp = ((data[5]&0xF0) >> 4)*10 + (data[5]&0xF) + (float)(((data[4]&0xF0) >> 4) / 10.0);
    return sign * temp;
}//fin temperature


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Extraire le pourcentage d'humidité
//
//  Entrée : data     -> buffer reçu
//  Sortie : pourcentage humidité
//
//---------------------------------------------------------------------------------------------------------------------------------
byte humidity(const byte* data)
{
    return (data[7]&0xF) * 10 + ((data[6]&0xF0) >> 4);
}//fin humidity


//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Retourne un apercu de l'etat de la baterie : 10 = faible
//
//  Entrée : data     -> buffer reçu
//  Sortie : indicateur batterie -> 10 => niveau faible
//                               -> 90 => niveau bon
//
//---------------------------------------------------------------------------------------------------------------------------------
byte battery(const byte* data)
{
    return (data[4] & 0x4) ? 10 : 90;
}//fin battery

//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Extraire de la tramme reçu le canal d'envoi
//
//  Entrée : data     -> buffer reçu
//  Sortie : channel  -> canal
//
//---------------------------------------------------------------------------------------------------------------------------------
byte channel(const byte* data)
{
    byte channel;
    switch (data[2])
    {
        case 0x10:
            channel = 1;
            break;
        case 0x20:
            channel = 2;
            break;
        case 0x40:
            channel = 3;
            break;
        default : 
            channel = 0;
     }
 
     return channel;
}//fin channel

//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Calculer le cheksum
//
//---------------------------------------------------------------------------------------------------------------------------------
byte checksum(const byte* data)
{
  int c = ((data[6]&0xF0) >> 4) + ((data[7]&0xF)<<4);
  int s = ((Sum(6, data) + (data[6]&0xF) - 0xa) & 0xff);
  return s == c;
}//fin checksum
 
byte checksum2(const byte* data)
{
  return data[8] == ((Sum(8, data) - 0xa) & 0xff);
}//fin checksum2 
 
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
}//fin Sum



//---------------------------------------------------------------------------------------------------------------------------------
//
//  Rôle : Recuperer le timestamp
//
//  Entrée : /
//  Sortie : /
//
//---------------------------------------------------------------------------------------------------------------------------------
void date (void)
{
  Process date;
  
  // timestamp par "date"
  date.runShellCommand("date +%s");
  while (date.running());

  if (date.available())
  {
    ts = date.parseInt();
  }
//  softSerialDebug.print(ts);
  date.flush();
}//fin date


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
//    Initialisation
//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void setup ()
{
    softSerialDebug.begin(9600);
    softSerialDebug.println("bridge");    
    pinMode(13, OUTPUT);
    digitalWrite(13, LOW);
    Bridge.begin();
    digitalWrite(13, HIGH);
    FileSystem.begin();
    softSerialDebug.println("* MoniThermo Two firmware V01.2 - 10/08/2015 *"); 
    delay(60000);
    softSerialDebug.println("Go ! ");
    
    attachInterrupt(1, ext_int_1, CHANGE);
    
    //DDRE  &= ~_BV(PE5); //input with pull-up
    //PORTE &= ~_BV(PE5);
}//fin initialisation


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//
//    Programme Principal : Décoder les trames arrivant du capteur oregon et stocker les valeurs dans le linino
//    Algorigramme : -> Attendre une trame
//                   -> Décoder la trame
//                   -> Récupérer le timestamp
//                   -> Stocker les valeurs dans un fichier                  
//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
void loop () {
    static int i = 0;
    cli();
    word p = pulse;
 
    pulse = 0;
    sei();
 
    if (p != 0)
    {
        if (orscV2.nextPulse(p))
            reportSerial("OSV2", orscV2);
    }
}//fin programme principal
