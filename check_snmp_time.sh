#!/bin/bash
function ayuda()
{
	echo "$0 <host_ip> <comunidad> <warning_seconds> <critical_seconds>"
	echo "Output: OK < warning_seconds"
	echo "Output: WARNING >= warning_seconds and < critical_seconds"
	echo "Output: CRITICAL >= critical_seconds"
	exit 1
}

if [ $# -ne 4 -o $1 = "-h" ]; then
	ayuda
fi

host=$1
comunidad=$2
warning_seconds=$3
critical_seconds=$4

horaServidorRemoto=$(snmpget -v2c -c$comunidad  -OvQ $host .1.3.6.1.4.1.2021.100.4.0)
segundosServidorRemoto=$(date --date="$horaServidorRemoto" +%s)
segundosServidorLocal=$(date +%s)

if [ $segundosServidorLocal -gt $segundosServidorRemoto ]; then
	let diferenciaTiempo=$segundosServidorLocal-$segundosServidorRemoto
else
	let diferenciaTiempo=$segundosServidorRemoto-$segundosServidorLocal
fi

resto="- $diferenciaTiempo secs | diff_time=$diferenciaTiempo;$warning_seconds;$critical_seconds"

if [ $diferenciaTiempo -lt $warning_seconds ]; then
	echo "OK $resto"
	exit 0
elif [ $diferenciaTiempo -lt $critical_seconds ]; then
	echo "WARNING $resto"
	exit 1
else
	echo "CRITICAL $resto"
	exit 2
fi

echo "UNKNOWN $resto"
	exit 3
	
