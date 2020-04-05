#!/usr/local/Python-2.7.16/bin/python
# -*- coding: utf-8 -*-

import subprocess
import sys
import optparse

#################################################################
#################################################################
#################################################################

OID                 = ".1.3.6.1.2.1.6.19.1.7"
intExitStatus       = 0
listSocketStatus    = ['closed','listen','synSent','synReceived','established','finWait1','finWait2','closeWait','lastAck','closing','timeWait','deleteTCB']
listSocketStatus.sort()
dictSocketCountINIT = {a:0 for a in listSocketStatus}

#################################################################
#################################################################
#################################################################

#----------------------------------------------------------------
def EjecutarComando(comando='echo Hola'):
	""" Ejecutamos un comando y obtenemos la salida. """
	p = subprocess.Popen(comando,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).communicate()
	return p

#----------------------------------------------------------------
def fCalcularPorcentaje(n='',total=''):
    """ Calcula el porcentaje si es necesario si n termina en la cadena '%' y el resto en un número. Si nó se sale
    con UNKNOWN."""
    n       = str(n)
    total   = str(total)
    if n.isdigit(): return int(n)
    
    if len(n)< 1 or n[-1] != '%':
        print 'UNKNOWN - Valor "' + n +'" incorrecto.' 
        sys.exit(3)

    n1 = n[:-1]
    if n1.isdigit() and total.isdigit():
        return int(n1)*int(total)/100

    print 'UNKNOWN - Valor "' + n +'" incorrecto.' 
    sys.exit(3)

#----------------------------------------------------------------
def fGenerarREsumenConexiones(listConexiones=[]):
    """ Genera el resumen por cada tipo de conexión según la estructura."""
   
    dictSocketStatus = {'synSent':2,'synReceived':1}

    for stringSocketStatus in  dictSocketStatus:
        print "#### %s ####"%stringSocketStatus
        listSockets=[] # Inicializamos la lista de sockets para el tipo en cuestión.
        for l in listConexiones:
            if ' '+stringSocketStatus in l:
                if 'ipv4' in l:  s = l.replace('".',':').replace('."','.').replace('.ipv4.',' ').split()[dictSocketStatus[stringSocketStatus]]
                if 'ipv6' in l:  s = l.replace('.ipv6.',' ').split()[dictSocketStatus[stringSocketStatus]]
                listSockets.append(s)

        listSockets.sort()
        dictSockets = { a:listSockets.count(a) for a in set(listSockets) } # Dict con contadores
        for s in dictSockets:
            if dictSockets[s] > 0:
                print "%s (%s conexiones)"%(s,dictSockets[s])

        print "--"
    

#----------------------------------------------------------------


#################################################################
#################################################################
#################################################################

parser = optparse.OptionParser()
parser.add_option("--w_synSent",	dest="w_synSent",	type="string",	default="100%",	help="Numero de conexiones SYN_SENT para WARNING")
parser.add_option("--c_synSent",	dest="c_synSent",	type="string",	default="100%",	help="Numero de conexiones SYN_SENT para CRITICAL")
parser.add_option("--w_synReceived",	dest="w_synReceived",	type="string",	default="100%",	help="Numero de conexiones SYN_RECV para WARNING")
parser.add_option("--c_synReceived",	dest="c_synReceived",	type="string",	default="100%",	help="Numero de conexiones SYN_RECV para CRITICAL")
parser.add_option("--community",	dest="community",	type="string",	default="public",	help="Community de conexion snmp")
parser.add_option("--host",	        dest="host",		type="string",	default="localhost",	help="Host/IP de conexion snmp")

(options, args) = parser.parse_args()


#################################################################


# Obtenemos la informacion desde el servidor, primero probamos con la comunidad 'public' y si falla se usa la pasada en los parámetros. 
strComando = 'snmpbulkwalk -Oq -Cc -mALL -t3 -r2 -c public -v2c ' + options.host + ' ' + OID
c = EjecutarComando(strComando)
if len(c[1]) > 0 or "No Such Object available on this agent at this OID" in c[0]:
    strComando = 'snmpbulkwalk -Oq -Cc -mALL -t10 -r2 -c ' + options.community + ' -v2c ' + options.host + ' ' + OID
    c = EjecutarComando(strComando)
    if len(c[1]) > 0:
        print 'UNKNOWN - ' + c[1]
        sys.exit(3)
# Comprobamos error de no existencia de OID
if "No Such Object available on this agent at this OID" in c[0]:
    print 'UNKNOWN - ' + c[0]
    sys.exit(3)


# Inicializamos el dict de conexiones.
listConexiones = c[0].splitlines()
l = [a.split()[1] for a in listConexiones]
d = {x:l.count(x) for x in set(l)}
dictSocketCount = dictSocketCountINIT.copy()
for a in d.keys():
    dictSocketCount[a]=d[a]

# Calculamos el total de conexiones para calcular los porcentajes si es necesario.
intTotalConnections = sum([dictSocketCount[a] for a in dictSocketCount])

# Calculamos los porcentajes a número entero de los parámetros
options.w_synSent = fCalcularPorcentaje(options.w_synSent,intTotalConnections)
options.c_synSent = fCalcularPorcentaje(options.c_synSent,intTotalConnections)
if options.w_synSent > options.c_synSent:
    print 'UNKNOWN - warning mayor que critical en synSent'
    sys.exit(3)

options.w_synReceived = fCalcularPorcentaje(options.w_synReceived,intTotalConnections)
options.c_synReceived = fCalcularPorcentaje(options.c_synReceived,intTotalConnections)
if options.w_synReceived > options.c_synReceived:
    print 'UNKNOWN - warning mayor que critical en synReceived'
    sys.exit(3)

# Calculamos el estado salida.
if dictSocketCount['synSent'] >= options.w_synSent: intExitStatus = max(intExitStatus,1)
if dictSocketCount['synSent'] >= options.c_synSent: intExitStatus = max(intExitStatus,2) 

if dictSocketCount['synReceived'] >= options.w_synReceived: intExitStatus = max(intExitStatus,1)
if dictSocketCount['synReceived'] >= options.c_synReceived: intExitStatus = max(intExitStatus,2)

# Cadena de informacion
strExitInfo = ' '.join([ k+'='+str(dictSocketCount[k]) for k in sorted(dictSocketCount.keys()) if dictSocketCount[k] > 0 ]) + ' Total='+ str(intTotalConnections)
# Cadena de performance
strExitPerf = ' '.join([ k+'='+str(dictSocketCount[k])+';;;0;'+str(intTotalConnections) for k in sorted(dictSocketCount.keys()) ]) + ' Total='+ str(intTotalConnections)


if intExitStatus == 0: strExitInfo = 'OK - '       + strExitInfo
if intExitStatus == 1: strExitInfo = 'WARNING - '  + strExitInfo
if intExitStatus == 2: strExitInfo = 'CRITICAL - ' + strExitInfo

print strExitInfo + ' | ' + strExitPerf

fGenerarREsumenConexiones(listConexiones)

sys.exit(intExitStatus)

