#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import time, httplib, urllib, subprocess, os

########################################################################################################################################################################
##
##                      Role : Programme permettant de recuperer la plage de tous les capteurs
##		
##                      Auteur : MoniThermo
##                      Creation : 05/03/2015
##                      Modification : 25/05/2015 -> ajout vidage memoire
##                      License: GNU GPL v2 (cf : " license.txt " )
##
##
##			Liste des definitions : -> def get (URL, ID)
##			  			-> def IP()
##			  			-> def IProot()
##						-> def ping_IP()
##			  			-> def erreur (msg)
##			  			-> def erreur_ping()
##			  			-> def log (lmsg)
##
########################################################################################################################################################################

# debugage httplib
httplib.HTTPConnection.debuglevel = 1

# Lecture du premier identifiant
file_ID = open("/MoniThermo/tmp/hostname", 'r')
ID_depart = file_ID.read()
file_ID.close()

# Liste des capteurs
liste_ID = range(eval(ID_depart), eval(ID_depart)+3)
print liste_ID

hote = "monserveur.com"                                                 
URLpl = "/min_max.php?id="


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
##	Role : Demander la plage du capteur au serveur				 ##
##										 ##
##	Entree : senspl : identifiant du capteur	       			 ##
##	Sortie : /								 ##
##										 ##
###################################################################################	
def plage(senspl) :
	try :
        	# demande de la plage de tension au serveur
                plage = get(URLpl, senspl)
		print len(plage)
                if "error" in plage :
	                print "error plage"
                        erreur("erreur plage")
        	elif plage == "" :
	                pass

                elif len(plage) == 9 :
	                try :
	                        print "ecrire fichier plage"
                                # ecrit le resultat dans les fichiers plage
				file_plage = open("/MoniThermo/plage/" + senspl, "write")
                                file_plage.write(plage[3] + ',' + plage[7] + ',\n')
                                file_plage.close()
			except :
				erreur("reponse plage")
				print "erreur plage"
	except Exception, e :
		erreur("plage")
		print "Exception %s", e
		try :
			erreur("erreur connexion plage : " + str(e))
		except :
			pass


			###################
			###	IP	###
			###################


###################################################################################
##										 ##
##	Role : Retouner l'adresse ip (wifi) du MoniThermo		         ##
##										 ##
##	Entree : /						        	 ##
##	Sortie : ip : chaine l'adresse ip du MoniThermo			         ##
##		        -> "" : Si pas d'adresse wifi (wlan)	        	 ##
##			-> sinon contient l'adresse ip du MoniThermo	         ##
##									         ##
###################################################################################	
def IP() :
	config = subprocess.check_output("ifconfig", shell = True)
        split = config.split('\n')
        nb = 0
        while nb < len(split) :
        	if "wlan0" in split[nb] :
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
                ip = IP()
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
	File_log = open("/MoniThermo/suivi/logPlage.txt", "append")
        File_log.write(time_log + """log prg "monithermo.py" : """ + lmsg + "\n")
        File_log.close()
                                
                                
				###########################
				### fin des definitions ###
				###########################
						
						
###################################################################################
##										 ##
##				Programme principal				 ##
##										 ##
##		Algorithme : -> Recuperation des identifiants capteur		 ##
##			     -> Recuperation des  plages			 ##
##										 ##
###################################################################################
try :
	space = subprocess.check_output("df -h", shell = True)
	space = space.split('\n')
	space = space[1].split('  ')
	nb = 0
	while nb < len(space) : 
		if '%' in space[nb] : 
			space = space[nb].split('%')
			print space
			if eval(space[0]) > 50 : 
				subprocess.call("rm /MoniThermo/suivi/log.txt", shell = True)
		nb = nb + 1
	# demande des plages
	log("plage...")
	nb = 0
	while nb < len(liste_ID) :
		ID = "sens_" + str(liste_ID[nb])
		plage(ID)
		nb = nb + 1
		
except Exception, e :
	print "Exception %s", e
	erreur("erreur prg" + str(e))

