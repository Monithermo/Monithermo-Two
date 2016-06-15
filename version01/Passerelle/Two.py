#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import time, httplib, urllib, subprocess, os

########################################################################################################################################################################
##
##                      Role : Programme permettant de traiter le fichier " stock " cree par le micro-controleur.
##			       Le fichier stock est constitue de la maniere suivante : 
##			        	- nom du capteur,
##					- timestamp,
##					- temperature
##		
##                      Auteur : MoniThermo
##                      Creation : 05/11/2014
##                      Modification : 05/03/2015 -> mise en place du heartbeat
##                      	       13/04/2015 -> suprime logHeaders
##				       10/07/2015 -> Valeurs aberrantes
##				       07/08/2015 -> Modification IP() et ping_IP()
##
##			License: GNU GPL v2 (cf : " license.txt " )
##
##
##			Liste des definitions : -> def get (URL, ID)
## 			  			-> def post(URL)
##			  			-> def alerte(alert)
##			  			-> def IP(network)
##			  			-> def IProot()
##						-> def ping_IP()
##			  			-> def erreur (msg)
##			  			-> def erreur_ping()
##			  			-> def log (lmsg)
##
########################################################################################################################################################################

# debugage httplib
httplib.HTTPConnection.debuglevel = 1

# Del bleu
blink = False
timedOut = False

# fichier copie serveur
nb = 0

# Lecture du premier identifiant
file_ID = open("/MoniThermo/tmp/hostname", 'r')
ID_depart = file_ID.read()
file_ID.close()

# Liste des capteurs
liste_ID = range(eval(ID_depart), eval(ID_depart)+3)
print liste_ID

# URLs
hote = "monserveur.com"                                                 
URL_Alerte = "http://monserveur.com/post-alert.php"    
URLpl = "/min_max.php?id="

# Variable globale contenant les informations du capteur
data = ""

# definitions pour l'encodage du post alerte
ordre = []
ordre.append('TIMESTAMP_ALERT')
ordre.append('STATION_ID')
ordre.append('TEMPERATURE')
ordre.append('TEMPERATURE_ALERT_THRESHOLD_MIN')
ordre.append('TEMPERATURE_ALERT_THRESHOLD_MAX')


                                ###################
				### definitions ###
				###################

				
###################################################################################
##										 ##
##	Role : Effectuer une requete get sur le serveur				 ##
##										 ##
##	Entree : URL -> chaine contenant l'URL voulant etre consultee		 ##
##		 id  -> chaine contenant le nom du capteur traite      		 ##
##	Sortie : resultat : chaine de caractere 				 ##
##				-> "" : pas de reponse du serveur		 ##
##				-> sinon chaine reponse du serveur		 ##
##										 ##
###################################################################################
def get (URL, id) :
	try :
                resultat = ""
	        pingGet = subprocess.call("ping -c4 " + hote, shell = True)
		if pingGet == 0 :
			log("ping = OK")
		        requeteGet = httplib.HTTPConnection(hote, timeout = 10)
	        	requeteGet.request("GET", URL+id)
		        response = requeteGet.getresponse()
	        	data = response.read()
	        	requeteGet.close()
		        log("reponse : " + data)
        		resultat = data.split('"')
		        return resultat

		else : 
			erreur("ping Get")
			ping_IP()
			
	except Exception, e :
		erreur("get")
        	print "Exception %s", e
        	try :
			erreur("erreur connexion plage : ", str(e))
	        except :
			pass
		ping_IP()

	return resultat

###################################################################################
##										 ##
##	Role : Effectuer une requete post sur le serveur			 ##
##										 ##
##	Entree : URL -> chaine contenant l'URL sur laquelle on postera           ##
##               id  -> chaine contenant le nom du capteur traite                ##
##	Sortie : /								 ##
##										 ##
###################################################################################
def post(URL, id) :
	try :
		pingPost = subprocess.call("ping -c4 " + hote, shell = True)
        	if pingPost == 0 : 
	        	log("ping = OK")
	        	print "params : ", params
		        post = urllib.urlopen(URL, params)
        		rep = post.read()
		        repStrip = rep.strip('\n')
		        print "repStrip : ", repStrip
		        if (repStrip == "ALERT ENTER : OK") | (repStrip == "ALERT UPDATE : OK") :
        			Alt("True", id)
			elif (repStrip == "ALERT EXIT : OK") | (repStrip == "ALERT STATUS : UNCHANGED (NO ALERT)") :
				Alt("False", id)
		        else :
        			erreur("reponse serveur : " + repStrip)

		        post.close()
        		log("reponse serveur : " + repStrip)
			timedOut = False
		else : 
			erreur("ping Post")
			ping_IP()
				
	except Exception, e :
        	print "Exception : %s", e
        	try :
			if "timed out" in str(e) : 
				erreur("timed out")
				if timedOut == False : 
					subprocess.call("blink-start 1", shell = True)
					timedOut = True
					blink = True
			else : 
				erreur(str(e))
        	except :
			pass
                ping_IP()


###################################################################################
##										 ##
##	Role : Changer la valeur de l'alerte : 					 ##
##										 ##
##	Entree : alert : chiffre contenant l'etat de l'alerte	 		 ##
##				-> 0 : Pas d'alerte				 ##
##				-> 1 : Alerte en cours		 		 ##
##				-> 2 : Attente de la prochaine mesure avant	 ##
##				       de donner l'alerte                        ##
##		 id : identifiant du capteur	              			 ##
##	Sortie : /								 ##
##										 ##
###################################################################################
def Alt(alert, id) :
	print "type alert : ", type(alert)
	print "open..."
	file_alerte = open("/MoniThermo/tmp/" + id, 'w') 
        print "write..."
        file_alerte.write(alert)
        print "close..."
        file_alerte.close()
		

###################################################################################
##										 ##
##	Role : Comparer les seuils avec la temperature actuelle du capteur	 ##
##										 ##
##	Entree : id : identifiant du capteur	       		        	 ##
##	Sortie : booleen -> True : alerte				         ##
##			 -> False : pas d'alerte                                 ##
##                                                                               ##
###################################################################################
def comparaison(id) :
	try :
		if (os.path.exists("/MoniThermo/plage/" + str(id))) == True : 
                	# Ouverture du fichier plage
			file_plage = open("/MoniThermo/plage/" + str(id), "read")
			seuils = file_plage.readline()
			file_plage.close()
			# Extraction des seuils
			splitSeuils = seuils.split(',')
			print "plage : ", splitSeuils[0], ",", splitSeuils[1]
			# comparaison temperature avec seuils : seuils[3] = tmin ; seuils[7] = tmax ;
			if (float(donnees[3]) < float(splitSeuils[0])) | (float(donnees[3]) > float(splitSeuils[1])) :
				# alerte
           			return True
			else :
        		   	return False
        	else : 
			date = subprocess.check_output("date +%s", shell = True)
			# timestamp RPI > 01/01/2014
			if date > 1388530800 :
				subprocess.call("./MoniThermo/prg/heartbeat.py", shell = True)
			else : 
				erreur("bad timestamp Yun")
	except Exception, e :
	    	print "Erreur : %s", e
		erreur("comparaison : " + str(e))
		return False


			###################
			###	IP	###
			###################


###################################################################################
##										 ##
##	Role : Retourner l'adresse ip (wifi) du MoniThermo		         ##
##										 ##
##	Entree : /						        	 ##
##	Sortie : ip : chaine l'adresse ip du MoniThermo			         ##
##		        -> "" : Si pas d'adresse wifi (wlan)	        	 ##
##			-> sinon contient l'adresse ip du MoniThermo	         ##
##									         ##
###################################################################################	
def IP(network) :
	config = subprocess.check_output("ifconfig", shell = True)
        split = config.split('\n')
        nb = 0
        while nb < len(split) :
        	if network in split[nb] :
        		lineIP = split[nb + 1]
	              	lineSplit = lineIP.split(':')
                      	if "inet addr" in lineSplit[0] :
        	              	ip = lineSplit[1]
				ipSplit = ip.split(' ')
                                return ipSplit[0]
       		nb = nb + 1
	return ""

###################################################################################
##										 ##
##	Role : Retourner l'adresse ip de la passerelle				 ##
##										 ##
##	Entree : /				 	 			 ##
##	Sortie : ip : chaine l'adresse ip de la passerelle	 		 ##
##			-> "" : Si pas d'adresse passerelle 	        	 ##
##			-> sinon contient l'adresse ip de la passerelle		 ##
##										 ##
###################################################################################
def IProot() : 
	route = subprocess.check_output("route", shell=True)
	splitRoute = route.split("\n")
	nb = 0
	while nb < len(splitRoute) :
	       	if "default" in splitRoute[nb] :
	       		print splitRoute[nb]
                        ipSplit = splitRoute[nb].split(" ")
               	        print ipSplit[9]
                       	return ipSplit[9]
        	nb = nb + 1
	return ""

###################################################################################
##                                                                               ##
##      Role : Effectuer un ping sur la passerelle et le MoniThermo              ##
##                                                                               ##
##      Entree : /                                                               ##
##      Sortie : /					                         ##
##                                                                               ##
###################################################################################
def ping_IP() :
        try : 
                # Extraire l'adresse ip du MoniThermo et celle de la passerelle
		if IP("eth1") != "" : 
			ip = IP("eth1")
		elif IP("wlan0") != "192.168.240.1" :
			ip = IP("wlan0")
		else : 
			ip = ""
		if ip != "" :
			erreur("ip : " + ip)
			ipBox = IProot()
			erreur("ipBox : " + ipBox)
			# Verification de la communication avec la passerelle
			pingBox = subprocess.call("ping -c4 " + ipBox, shell = True)
			if pingBox == 0 :
				# Ping sur la passerelle -> OK
				log("pingBox = OK")
			else :
				# Ping sur la passerelle -> NOK
				log("pingBox = NOK")
				erreur("pingBox = NOK")
				# Ping sur MoniThermo
				pingMoniThermo = subprocess.call("ping -c4 " + ip, shell = True)
                	        if pingMoniThermo == 0 :
                       		        # Ping MoniThermo -> OK
        	               		log("pingMoniThermo = OK")
		        	else :
        		        	# Ping MoniThermo -> NOK
                	                log("pingMoniThermo = NOK")
                			erreur("pingMoniThermo = NOK")
		else : 
                	erreur("pas de connexion reseau")
	except : 
		erreur("demande IP")


                        ######################
			### Log et Erreurs ###
                        ######################

                                                                        
###################################################################################
##										 ##
##		Role : Stocker l'erreur dans un fichier dedie	        	 ##
##										 ##
##		Entree : msg -> message d'erreur a stocker			 ##
##		Sortie : /							 ##
##										 ##
###################################################################################
def erreur (msg):
	time_erreur = time.strftime("%d-%m-%Y : %H:%M:%S : ", time.gmtime())
	erreur = open("/MoniThermo/suivi/erreur.txt", "append")
	erreur.write(time_erreur + """monithermo_433MHz.py" : """ + msg + "\n")
	erreur.close()

###################################################################################
##			        						 ##
##		Role : Logger dans un fichier le deroulement du programme	 ##
##										 ##
##		Entree : lmsg -> message de log	 				 ##
##		Sortie : /							 ##
##										 ##
###################################################################################	
def log (lmsg):
        time_log = time.strftime("%d-%m-%Y : %H:%M:%S : ", time.gmtime())
	File_log = open("/MoniThermo/suivi/log.txt", "append")
        File_log.write(time_log + """log prg "monithermo.py" : """ + lmsg + "\n")
        File_log.close()
                                
                                
				###########################
				### fin des definitions ###
				###########################
						
						
###################################################################################
##										 ##
##				Programme principal				 ##
##										 ##
##		Algorithme : -> Recuperation des donnees du capteur		 ##
##			     -> Mise a jour de la plage du capteur		 ##
##			     -> Comparaison des temperatures			 ##
##			     -> Envoi d'alerte si necessaire			 ##
##			     -> Stockage des donnees				 ##
##			     -> Envoi du fichier de temperature au serveur       ##
##										 ##
###################################################################################
while True : 

	try :
                # Si fichier de temperature existe
		if (os.path.exists("/MoniThermo/tmp/dataFile.txt")) == True :
			# ouvrir le fichier contenant les donnees
			fdata = open("/MoniThermo/tmp/dataFile.txt", 'r')

			# lecture des donnees
			donnees = fdata.readline()
			fdata.close()
				
			# traitement des donnees
			## ID|channel|battery|ts|temperature|humidity ##
			donnees = donnees.split('|')
			if (len(donnees) == 7) | (len(donnees) == 6) :
				# timestamp > 01/01/2014
				if eval(donnees[3]) > 1388530800 :
					if (float(donnees[4]) < 80) & (float(donnees[4]) > -50): 
	                                	print "temperature valide"
	                                        # Verification de l'acces a internet et au serveur
						rep = subprocess.call("ping -c4 monserveur.com", shell = True)
						if rep != 0 :
                        	                        # Ping sur serveur -> NOK
							erreur("erreur ping")
							# Faire clignoter la led bleu (WLAN) pour indiquer un probleme sur le reseau
							if (blink == False) & (timedOut != True) : 
								subprocess.call("blink-start 400", shell = True)
								blink = True
							ping_IP()
						else :
        	                                        # Ping sur serveur -> OK
							if (blink == True) & (timedOut == False) : 
								subprocess.call("blink-stop", shell = True)
								blink = False
                                        	# Verification de la validite des donnees
						print donnees
						log(str(donnees))
						if (int(donnees[1]) == 1) | (int(donnees[1]) == 2) | (int(donnees[1]) == 3) == True :
                        	                        # Recuperation ID capteur
							n = int(donnees[1]) - 1
							ID = "sens_" + str(liste_ID[n])
							print ID
							log(str(ID))
							# Verification de l'existence du fichier " alerte "
							if os.path.exists("/MoniThermo/tmp/" + ID) :
								file_alerte = open("/MoniThermo/tmp/" + ID, "read")
								data = file_alerte.read()
								file_alerte.close()
								print data, type(data)
							else : 
        	                                                # Si le fichier alerte n'existe pas le creer
								Alt("False", ID)
								data = "False"
							
							# Comparaison
							log("comparaison")
							alerte = comparaison(ID)
							if alerte != None : 
								log("alerte : " + str(alerte))
								# Headers
								fseuil = open("/MoniThermo/plage/" + ID, 'r')
								seuil = fseuil.readline()
								fseuil.close()
								seuil = seuil.split(',')
								value = { "STATION_ID" : ID, "TEMPERATURE_ALERT_THRESHOLD_MIN" : seuil[0], "TEMPERATURE_ALERT_THRESHOLD_MAX" : seuil[1], "TEMPERATURE" : donnees[4], "TIMESTAMP_ALERT" : donnees[3] }
								params = "&".join([item+'='+urllib.quote_plus(value[item]) for item in ordre])
								headers = {"Content-type" : "application/x-www-form-encoded"}
								# Temperature hors plage
								if alerte == True :
  									try : 
  										# Post alerte	
  										post(URL_Alerte, ID)
									except Exception, e :
										print "except alerte"
   										print "Erreur : %s", e
										erreur("alerte : " + str(e))
						
								# Temperature dans la plage 
								elif alerte == False : 
									# si alerte du capteur en cours
									if data == "True" :
										# fin d'alerte
										try : 
											log("post FA")
   	          									post(URL_Alerte, ID)
							
										except Exception, e :
											print "Erreur : %s", e
											erreur("FA : " + str(e))
									elif data == "False" : 
										print "pas d'alerte"
									
									else : 
										print "pb variable data"
										erreur("data : " + data)
	
							# Enregistrement des donees
							print "stockage des donnees"
							log("stockage des donnees")
							try :
                                        	        	# enregistrement dans fichier serveur
								log("fichier serveur")
								valid = False
	                                                	while valid != True :
        	                                			if os.path.exists("/MoniThermo/tmp/fichier_serveur" + str(nb)) == True :
                	                                                	lignes = subprocess.check_output("wc -l /MoniThermo/tmp/fichier_serveur" + str(nb), shell = True)
                        	                                        	lignes = lignes.split(" ")
                                	                                	print lignes
	                                	                                if eval(lignes[0]) >= 500 :
        	                                	                                nb = nb + 1
                	                                	                        valid = False
                        	                                	        else :
                                	                                	        valid = True
	                                        	                else :	
        	                                        	                valid = True
		
        		                                        serveur_T_RH = open("/MoniThermo/tmp/fichier_serveur" + str(nb), "append")
                		                                serveur_T_RH.write(donnees[3] + ',' + str(ID) + ',' +  donnees[2] + ',' + donnees[4] +  '\n')
                        		                        serveur_T_RH.close()
							
							except Exception, e :
   								print "Erreur : %s", e
								erreur("fichier serveur : " + str(e))
							try :
        		                                        # enregistrement dans fichier suivi
								log("fichier suivi") 
								fdata = open("/MoniThermo/suivi/" + str(ID) + ".txt", "append")
        	       						fdata.write("heure UTC : " + time.strftime("%d-%m-%Y : %H:%M:%S", time.gmtime(eval(donnees[3]))) + ", Station : " + str(ID) + ", Batterie : " + str(donnees[2]) + ", Temperature : " + str(donnees[4]) +  "\n")
                						fdata.close()
						
							except Exception, e :
								print "Erreur : %s", e
								erreur("data : " + str(e))
					else : 
						print "temperature non valide"			
		
				else :
                       	               	# Si timestamp < 01/01/2014 -> alumer la del bleu (WLAN)
					subprocess.call("blink-start 1", shell = True)
				log("fin du programme\n----------------------------------------------------------------------------------------------------------")
				subprocess.call("rm /MoniThermo/tmp/dataFile.txt", shell = True)
	except Exception, e :
		print "Exception %s", e
		erreur("erreur prg" + str(e))

