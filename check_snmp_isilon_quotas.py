#!/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
import optparse

parser = optparse.OptionParser()
parser.add_option("-w", "--warning",	dest="warning",		type="int",	default=80,		help="Porcentaje para warning")
parser.add_option("-c", "--critical",	dest="critical",	type="int",	default=90,		help="Porcentaje para critical")
parser.add_option("-C", "--community",	dest="community",	type="string",	default="isilonpublic",	help="Community de conexion snmp")
parser.add_option("-P", "--port",	dest="port",		type="int",	default=161,		help="Puerto de conexion snmp")
parser.add_option("-H", "--host",	dest="host",		type="string",	default="localhost",	help="Host/IP de conexion snmp")

(options, args) = parser.parse_args()

listTiposDeCampos = ["quotaType","quotaID","quotaIncludesSnapshotUsage","quotaPath","quotaHardThresholdDefined","quotaHardThreshold","quotaSoftThresholdDefined","quotaSoftThreshold","quotaAdvisoryThresholdDefined","quotaAdvisoryThreshold","quotaGracePeriod","quotaUsage","quotaUsageWithOverhead","quotaInodeUsage","quotaIncludesOverhead"]

def EjecutarComando(comando='echo Hola'):
	""" Ejecutamos un comando y obtenemos la salida. """
	p = subprocess.Popen(comando,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).communicate()
	return p

# Obtenemos la informacion desde la cabina
strComando = 'snmpbulkwalk -OsQ -Cc -mALL -t300 -r50 -c ' + options.community + ' -v2c ' + options.host + ' .1.3.6.1.4.1.12124.1.12'
c = EjecutarComando(strComando)

dictDatos = {}

for strLinea in c[0].splitlines():
	(campo, clave, resto) = strLinea.split('.',3)
	if not clave in dictDatos:
		dictDatos[clave] = {}
	for strTipo in listTiposDeCampos:
		if strTipo == campo:
			dictDatos[clave][strTipo]=resto.split('=')[1].strip()

status = 0
listResultadoOK = []
listResultadoWarning = []
listResultadoCritical = []

# Obtenemos loas porcentajes de uso
for key in dictDatos:
	if dictDatos[key]['quotaSoftThresholdDefined'] == 'yes':
		tamano = int(dictDatos[key]['quotaSoftThreshold'])
	elif dictDatos[key]['quotaHardThresholdDefined'] == 'yes':
		tamano = int(dictDatos[key]['quotaHardThreshold'])
	else:
		tamano = 0 # No hay definido ni hard ni soft
	if tamano > 0:
		porcentaje = int(dictDatos[key]['quotaUsage'])*100/tamano
	else:
		porcentaje = 0

	dictDatos[key]['porcentaje'] = porcentaje

# Obtenemos las salidas de las quotas
	if porcentaje < options.warning:
		listResultadoOK.append("%s %s %s %s%%"%(dictDatos[key]['quotaPath'], dictDatos[key]['quotaType'], dictDatos[key]['quotaID'], dictDatos[key]['porcentaje']))
		status = max(0,status)
		continue
	if porcentaje < options.critical:
		listResultadoWarning.append("%s %s %s %s%%"%(dictDatos[key]['quotaPath'], dictDatos[key]['quotaType'], dictDatos[key]['quotaID'], dictDatos[key]['porcentaje']))
		status = max(1,status)
		continue
	if porcentaje >= options.critical:
		listResultadoCritical.append("%s %s %s %s%%"%(dictDatos[key]['quotaPath'], dictDatos[key]['quotaType'], dictDatos[key]['quotaID'], dictDatos[key]['porcentaje']))
		status = max(2,status)
		continue

listResultadoOK.sort()
listResultadoWarning.sort()
listResultadoCritical.sort()


print ("CRITICAL(>=%s%%) - %s; WARNING(>=%s%% <%s%%) - %s; OK(<%s%%) - %s | CRITICAL=%s;0;0;0; WARNING=%s;0;0;0; OK=%s;0;0;0;"% ( \
	options.critical, len(listResultadoCritical), \
	options.warning, options.critical, len(listResultadoWarning), \
	options.warning, len(listResultadoOK), \
	len(listResultadoCritical), \
	len(listResultadoWarning), \
	len(listResultadoOK)))

print ("############")
print ("# CRITICAL #")
print ("############")
for l in listResultadoCritical:
	print(l)

print ("###########")
print ("# WARNING #")
print ("###########")
for l in listResultadoWarning:
	print (l)

#print('|')

#for key in dictDatos:
#	print("'%s %s %s'=%s%%;%s;%s;; "%(dictDatos[key]['quotaPath'], dictDatos[key]['quotaType'], dictDatos[key]['quotaID'], dictDatos[key]['porcentaje'], options.warning, options.critical))

sys.exit(status)

