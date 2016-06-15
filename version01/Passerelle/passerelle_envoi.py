#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import subprocess, os, time

########################################################################################################################################################################
##
##                      Role : Programme permettant d'envoi sur le serveur le fichier contenant les donnees de temperature.
##
##                      Auteur : MoniThermo
##                      Creation : 05/11/2014
##                      Modification : 13/04/2015 -> ajout nettoyage espace disponible
##				       15/04/2015 -> ajout ping
##				       22/04/2015 -> debugage passerelle lors d'un "connection timed out" intempestif (reboot)
##				       23/04/2015 -> log erreur cURL
##				       07/08/2015 -> modification ping
##                      License: GNU GPL v2 (cf : " license.txt " )
##
##			Liste des definitions : -> def erreur (msg)
##						-> def IP(network)
##
########################################################################################################################################################################

###################################################################################
##										 ##
##	Role : Stocker l'erreur dans un fichier dedie	                	 ##
##										 ##
##	Entree : msg -> message d'erreur a stocker		        	 ##
##	Sortie : /							         ##
##										 ##
###################################################################################
def erreur (msg):
	time_erreur = time.strftime("%d-%m-%Y : %H:%M:%S : ", time.gmtime())
	erreur = open("/MoniThermo/suivi/erreur.txt", "append")
	erreur.write(time_erreur + """passerelle_envoi.py" : """ + msg + "\n")
	erreur.close()

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
				print ipSplit[0] 
	                        return ipSplit[0]
		nb = nb + 1
	return ""
	
###################################################################################
##										 ##
##				Programme principal				 ##
##										 ##
###################################################################################
try :
	# timestamp > 01/01/2014
	if time.time() > 1388530800 : 
		ping = subprocess.call("ping -c4 monserveur.com", shell = True)
		if ping == 0 :
			subprocess.call("blink-stop", shell = True)			
	      		nb = 0
        		files = subprocess.check_output("ls /MoniThermo/tmp/", shell = True)
	        	files = files.split('\n')
	        	print files
		        while nb < len(files) :
        			try : 
					if "fichier_serveur" in files[nb] : 
                				print files[nb]
                				if files[nb] != "fichier_serveur.txt" : 
	                        			espace = False
	        	                		nbListe = 0
        	        	        		while espace != True : 
                	        				clean = subprocess.call("mv /MoniThermo/tmp/" + files[nb] + " /MoniThermo/tmp/fichier_serveur.txt", shell = True)
                        					if clean != 0 : 
                        						liste = subprocess.check_output("ls /MoniThermo/suivi/", shell = True)
                        						liste = liste.split('\n')
	                        					subprocess.call("rm /MoniThermo/suivi/" + liste[nbListe], shell = True)
        	                					erreur("space => clean...")
	        	                			else : 
        	        	        				espace = True
                        			
                	        		if os.path.exists("/MoniThermo/tmp/fichier_serveur.txt") :
                        	        		try : 
                                				rep = subprocess.check_output(["curl", "--form", "f=@/MoniThermo/tmp/fichier_serveur.txt", "monserveur.com/post-temp-values-file.php"])
                                				print rep
	                                			rep = rep.strip('\n')
        	                        			if rep == "OK" :
                	                        			subprocess.call("rm /MoniThermo/tmp/fichier_serveur.txt", shell = True)
                        	        			else :
                                	        			erreur("reponse serveur : " + rep)
                                        				break
                                        			
		                                        except Exception, e : 
        		                                	print "erreur connexion"
                		                        	if "status 7" in str(e) : 
                		                        		erreur("connection timed out -> reboot")
                	        	                		#subprocess.call("reboot", shell = True)
                	                	        		subprocess.call("/etc/init.d/network restart", shell = True)
                	                	        	elif "status 56" in str(e) :                                                                                                                            
									erreur("Failure with receiving network data") 
                	                        		else :
                	                        			erreur(str(e))
		                        	else :
        		                	        print "fichier serveur non existant"
                			else :
                        			print "pas d'occurence"
	                        	nb = nb + 1
	
				except Exception, e : 
					print "erreur occurences"
					nb = len(files)
					print "Erreur : %s", e
					erreur("occurences")

		else :
			print "status ping : ", ping                                                                                                                                                            
			erreur("status ping : " + str(ping))  
			if ("192.168" in IP("eth1")) | (IP("wlan0") != "192.168.240.1") :
				subprocess.call("/etc/init.d/network restart", shell = True)
			else :
				subprocess.call("blink-start 400", shell = True)
except Exception, e :
	print "Erreur : %s", e
	erreur(str(e))
