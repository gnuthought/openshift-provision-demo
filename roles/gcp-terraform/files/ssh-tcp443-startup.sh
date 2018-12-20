#!/bin/sh

if systemctl is-active -q firewalld
then
  firewall-cmd --add-forward-port=port=443:proto=tcp:toport=22
  firewall-cmd --permanent --add-forward-port=port=443:proto=tcp:toport=22
else
  iptables -t nat -I PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports=22
fi
