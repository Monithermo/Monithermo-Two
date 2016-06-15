#!/usr/bin/env python
# -*- coding:Utf-8 -*-

import subprocess, os, time, sys

########################################################################################################################################################################
##
##                      Role : Programme permettant d'envoi sur le serveur le fichier contenant les donnees de temperature.
##
##                      Auteur : MoniThermo
##                      Creation : 05/11/2014
##                      Modification :
##                      License: GNU GPL v2 (cf : " license.txt " )
##
##
########################################################################################################################################################################

chemin = "/MoniThermo/debugage/copie_fichier.py"

###################################################################################
##										 ##
##				Programme principal				 ##
##										 ##
###################################################################################
try :
	# verification du fichier serveur
	if os.path.exists("/MoniThermo/tmp/fichier_serveur.txt") :
		lines = subprocess.check_output("wc -l /MoniThermo/tmp/fichier_serveur.txt", shell = True)
		lines = lines.split(" ")
		print lines[0]
		if eval(lines[0]) > 500 :
			 verif = False
			 while verif != True :
				reponse = raw_input("fichier serveur trop grand, voulez-vous lancer le programme de deblocage ? (o/n) : ")
				if (reponse == 'o') | (reponse == 'O') :
				 	verif = True
                        		process = subprocess.call("./MoniThermo/debugage/deblocage_serveur.py", shell = True)
	                        	while process != 0 :
        		                	try :
	        		                	chemin = raw_input("Erreur dans le lancement du programme.\nEntrez le chemin du programme de debugage serveur (ctrl+C pour quitter) : ")
	                		        	process = subprocess.call("./" + chemin, shell = True)
	
	                        		except KeyboardInterrupt :
	                        			print "\nfin du programme"
                                       			sys.exit()

				elif (reponse == 'n') | (reponse == 'N') :
					verif = True
				else : 
					verif = False	                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
        nb = 0
        files = subprocess.check_output("ls /MoniThermo/tmp/", shell = True)
        files = files.split('\n')
        print files
        while nb < len(files) :
        	try : 
                	if "fichier_serveur" in files[nb] : 
                		print files[nb]
                        	if files[nb] != "fichier_serveur.txt" :
                        		print "copie dans fichier serveur"
                        		subprocess.call("mv /MoniThermo/tmp/" + files[nb] + " /MoniThermo/tmp/fichier_serveur.txt", shell = True)
                        	if os.path.exists("/MoniThermo/tmp/fichier_serveur.txt") :
                        		lines = subprocess.check_output("wc -l /MoniThermo/tmp/fichier_serveur.txt", shell = True)
                        		lines = lines.split(" ")
                        		print lines[0]
                        		if eval(lines[0]) < 506 : 
                                		rep = subprocess.check_output(["curl", "--form", "f=@/MoniThermo/tmp/fichier_serveur.txt", "monserveur.com/post-temp-values-file.php"])
                                		print rep
                                		rep = rep.strip('\n')
                                		if rep == "OK" :
                                        		subprocess.call("rm /MoniThermo/tmp/fichier_serveur.txt", shell = True)
                                		else :
                                        		erreur("reponse serveur : " + rep)
                                        		print "error connexion"
                                        		break
                                        else : 
                                        	verif = False
                                        	while verif != True :
                                        		reponse = raw_input("fichier serveur trop grand, voulez-vous lancer le programme de deblocage ? (o/n) : ")
                                        		if (reponse == 'o') | (reponse == 'O') : 
                                        			verif = True
                                        			process = subprocess.call("./" + chemin, shell = True)
                                        			while process != 0 : 
                                        				try : 
                                        					chemin = raw_input("Erreur dans le lancement du programme.\nEntrez le chemin du programme de deblocage serveur svp (ctrl+C pour quitter) : ")
                      	  							process = subprocess.call("./" + chemin, shell = True)
                        						except KeyboardInterrupt :
                        					        	print "\nfin du programme"
                        					        	sys.exit()
   								nb = 0
                        					files = subprocess.check_output("ls /MoniThermo/tmp/", shell = True)
                        					files = files.split('\n')
                        					print files
                        				elif (reponse == 'n') | (reponse == 'N') :
                        					verif = True
                        					print "fin du programme"
                        					sys.exit()
                        				else : 
                        					verif = False
                        				
                        	else :
                        	        print "fichier serveur non existant"
                	else :
                        	print "pas d'occurence"
                        nb = nb + 1
		
		except Exception, e : 
			print "erreur occurences"
			nb = len(files)
			print "Erreur : %s", e

except Exception, e :
	print "Erreur : %s", e
