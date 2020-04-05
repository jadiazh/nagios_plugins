#!/usr/local/Python-2.7.16/bin/python
# -*- coding: utf-8 -*-
""" Check Isilon quota status with True 'enforced' """

import sys
import optparse
import base64
import urllib2
import ssl
import json

##############################################
def check_options(options):
	""" Check options parameters """
	error = "UNKNOWN"
	if options.critical <= options.warning:
		error = error + " - Critical <= Warning"

	if len(error) > len("UNKNOWN"):
		print error
		sys.exit(3)

##############################################

def get_quotas_info(options):
	""" Get quotas info """
	def get_data(url,options):
		try:
			ssl._create_default_https_context = ssl._create_unverified_context
			request = urllib2.Request(url)
			base64string = base64.encodestring('%s:%s' % (options.user, options.passwd)).replace('\n', '')
			request.add_header("Authorization", "Basic %s" % base64string)   
			y = json.loads(urllib2.urlopen(request).read()) 
			return y
		except Exception as e:
			print e
			sys.exit(3)

	lQuotas = []

	# Protocolo https"
	protocol="https" if options.ssl else "http"

	url = protocol+"://"+options.host+':'+str(options.port)+"/platform/1/quota/quotas?resolve_names=true"

	datos = get_data(url,options)
	lQuotas = lQuotas + datos['quotas']

	while datos['resume']:
		url = protocol+"://"+options.host+':'+str(options.port)+"/platform/1/quota/quotas?resume="+datos['resume']
		datos = get_data(url,options)
		lQuotas = lQuotas + datos['quotas']

	return lQuotas

##############################################
##############################################
##############################################
##############################################

parser = optparse.OptionParser(version="0.1")
parser.add_option("--warning",			dest="warning",		type="int",				default=80,		help="warning percentage")
parser.add_option("--critical",			dest="critical",	type="int",				default=90,		help="critical percentage")
parser.add_option("--port",			dest="port",		type="int",				default=8080,		help="API connection port")
parser.add_option("--host",			dest="host",		type="string",				default="localhost",	help="connection Host/IP")
parser.add_option("--user",			dest="user",		type="string",				default="guest",	help="API connection user")
parser.add_option("--passwd",			dest="passwd",		type="string",				default="guest",	help="Password API connection user")
parser.add_option("--ssl",			dest="ssl",				action="store_true",	default=False,		help="Use https protocol, else use http protocol")
parser.add_option("--check-directory-quota",	dest="checkdirectoryquota",		action="store_true",	default=False,		help="Check thresholds with 'directory' quotas")
parser.add_option("--check-user-quota",		dest="checkuserquota",			action="store_true",	default=False,		help="Check thresholds with 'user' quotas")
parser.add_option("--show-directory-quota",	dest="showdirectoryquota",		action="store_true",	default=False,		help="Show alarmed 'directory' quotas at info")
parser.add_option("--show-user-quota",		dest="showuserquota",			action="store_true",	default=False,		help="Show alarmed 'user' quotas at info")

(options, args) = parser.parse_args()

check_options(options)

rQuotas = get_quotas_info(options)

status = 0
listResultadoOK = []
listResultadoWarning = []
listResultadoCritical = []

# Obtenemos los porcentajes de uso según tenga soft o hard. Si no tienen ni soft ni hard
for quota in rQuotas:
	if not quota['enforced']:
		continue

# Si no hay hard ni soft ir al siguiente
	if quota['thresholds']['soft']:
		porcentaje = quota['usage']['logical']*100/quota['thresholds']['soft']
	elif quota['thresholds']['hard']:
		porcentaje = quota['usage']['logical']*100/quota['thresholds']['hard']
	else:
		continue
		
# Obtenemos las salidas de las quotas
	usuario = ""
	if quota['type'] == 'user':
		if 'name' in quota['persona']:
			usuario = quota['persona']['name']
		else:
			usuario = quota['persona']['id']

	linea = "%s %s %s %s%%"%(quota['path'], quota['type'], usuario, porcentaje)
	
	if porcentaje < options.warning:
		listResultadoOK.append(linea)
		status = max(0,status)
		continue
	if porcentaje < options.critical:
		listResultadoWarning.append(linea)
		if (quota['type'] == 'user' and options.checkuserquota) or (quota['type'] == 'directory' and options.checkdirectoryquota):
			status = max(1,status)
		continue
	if porcentaje >= options.critical:
		listResultadoCritical.append(linea)
		if (quota['type'] == 'user' and options.checkuserquota) or (quota['type'] == 'directory' and options.checkdirectoryquota):
			status = max(2,status)
		continue

listResultadoOK.sort()
listResultadoWarning.sort()
listResultadoCritical.sort()

total = len(listResultadoOK) + len(listResultadoWarning) + len(listResultadoCritical)

print ("%s CRITICAL(>=%s%%)  ## %s WARNING(>=%s%% <%s%%) ## %s OK(<%s%%) | 'CRITICAL'=%s;%s;%s;0;%s 'WARNING'=%s;%s;%s;0;%s 'OK'=%s;%s;%s;0;%s"% ( \
	len(listResultadoCritical), options.critical, \
	len(listResultadoWarning), options.warning, options.critical, \
	len(listResultadoOK), options.warning, \
	len(listResultadoCritical), \
	0, 0, total, \
	len(listResultadoWarning), \
	0, 0, total, \
	len(listResultadoOK), \
	0, 0, total \
	))

print ("##################################################")
print ("#------------------ CRITICAL --------------------#")
print ("##################################################")
if options.showdirectoryquota:
	print ("-")
	print (">>> DIRECTORY quotas <<<")
	print ("-")
	for l in listResultadoCritical:
		if ' directory ' in l:
			print(l)

if options.showuserquota:
	print ("-")
	print (">>> USER quotas <<<")
	print ("-")
	for l in listResultadoCritical:
		if ' user ' in l:
			print(l)

print ("-")
print ("##################################################")
print ("#------------------- WARNING --------------------#")
print ("##################################################")
if options.showdirectoryquota:
	print ("-")
	print (">>> DIRECTORY quotas <<<")
	print ("-")
	for l in listResultadoWarning:
		if ' directory ' in l:
			print(l)

if options.showuserquota:
	print ("-")
	print (">>> USER quotas <<<")
	print ("-")
	for l in listResultadoWarning:
		if ' user ' in l:
			print(l)


# Return status
sys.exit(status)

