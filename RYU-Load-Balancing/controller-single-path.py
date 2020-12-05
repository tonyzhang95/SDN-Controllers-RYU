from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp


class SimpleSwitch13(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]


	def __init__(self, *args, **kwargs):
		super(SimpleSwitch13, self).__init__(*args, **kwargs)
		# hard-code arp table
		self.arp_table={}
		self.arp_table["10.0.0.1"] = "00:00:00:00:00:01"
		self.arp_table["10.0.0.2"] = "00:00:00:00:00:02"


	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		
		match = parser.OFPMatch()
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, actions)
		dpid = datapath.id

		# install ICMP routing ruless
		if dpid == 1: # switch S1
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
			
		elif dpid == 2:
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
			
		elif dpid == 3:
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)

		elif dpid == 4:
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 1)
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 2)
			
		elif dpid == 5:
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.1', 10, 2)
			self.add_layer4_rules(datapath, inet.IPPROTO_ICMP, '10.0.0.2', 10, 1)

		 

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
		msg = ev.msg
		datapath = msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		
		in_port = msg.match['in_port']
		pkt = packet.Packet(msg.data)
		eth = pkt.get_protocol(ethernet.ethernet)
		ethertype = eth.ethertype

		# process ARP 
		if ethertype == ether.ETH_TYPE_ARP:
			self.handle_arp(datapath, in_port, pkt)
			return

		# process IP
		if ethertype == ether.ETH_TYPE_IP:
			self.handle_ip(datapath, in_port, pkt)
			return

	# Function to install TCP/UDP/ICMP (layer 4) forwarding rules
	def add_layer4_rules(self, datapath, ip_proto, ipv4_dst = None, priority = 1, fwd_port = None):
		parser = datapath.ofproto_parser
		actions = [parser.OFPActionOutput(fwd_port)]
		match = parser.OFPMatch(eth_type = ether.ETH_TYPE_IP,ip_proto = ip_proto,ipv4_dst = ipv4_dst)
		self.add_flow(datapath, priority, match, actions)

	# Functin to install general rules
	def add_flow(self, datapath, priority, match, actions):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=priority,match=match, instructions=inst)
		datapath.send_msg(mod)

	

	def handle_arp(self, datapath, in_port, pkt):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		eth_pkt = pkt.get_protocol(ethernet.ethernet)
		arp_pkt = pkt.get_protocol(arp.arp)
		arp_resolv_mac = self.arp_table[arp_pkt.dst_ip]

		ether_hd = ethernet.ethernet(dst = eth_pkt.src, src = arp_resolv_mac, ethertype = ether.ETH_TYPE_ARP);
		arp_hd = arp.arp(hwtype=1, proto = 2048, hlen = 6, plen = 4,
			opcode = 2, src_mac = arp_resolv_mac, 
			src_ip = arp_pkt.dst_ip, dst_mac = eth_pkt.src,
			dst_ip = arp_pkt.src_ip)
		arp_reply = packet.Packet()
		arp_reply.add_protocol(ether_hd)
		arp_reply.add_protocol(arp_hd)
		arp_reply.serialize()
		
		# send the Packet Out mst to back to the host who is initilaizing the ARP
		actions = [parser.OFPActionOutput(in_port)];
		out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
			ofproto.OFPP_CONTROLLER, actions,
			arp_reply.data)
		datapath.send_msg(out)



	def handle_ip(self, datapath, in_port, pkt):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		eth_pkt = pkt.get_protocol(ethernet.ethernet)
		ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
		tcp_pkt = pkt.get_protocol(tcp.tcp)

		"""
		Becuase we define all traffic to go through s4-s1-s5 and reverse, so that we only define forwarding rules for them.
		At switch 4, we forward all traffic towards h2 to port2 to s1, and vise versa.
		At switch 5, we forward all traffic towards h1 to port2 to s1, and vise versa.
		At switch 1, we forward all traffic towards h1 to port1 to s4, or to port2 to s5 for h2's traffic.
		Notice that at s4 and s5, we do NOT perform any load balancing, that is to say that evene we have other equal length paths vai s2 and s3, we only use s1.
		"""

		if (datapath.id == 4):
			match=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.1', ipv4_dst='10.0.0.2', tcp_src=tcp_pkt.src_port, 
				tcp_dst=tcp_pkt.dst_port)
			actions=[parser.OFPActionOutput(2)]
			
			self.add_flow(datapath,10,match,actions)
			
			match1=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.1', tcp_src=tcp_pkt.src_port,
				tcp_dst=tcp_pkt.dst_port)
			actions1=[parser.OFPActionOutput(1)]
			self.add_flow(datapath,10,match1,actions1)
			
			if (in_port == 1):
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions, pkt.data)
			else:
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions1, pkt.data)
			datapath.send_msg(out)
			
		if (datapath.id == 5):
			match=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.1', ipv4_dst='10.0.0.2', tcp_src=tcp_pkt.src_port,
				tcp_dst=tcp_pkt.dst_port) 
			actions=[parser.OFPActionOutput(1)]
			self.add_flow(datapath,10,match,actions)
			match1=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.1',tcp_src=tcp_pkt.src_port,
				tcp_dst=tcp_pkt.dst_port)
			actions1=[parser.OFPActionOutput(2)]
			self.add_flow(datapath,10,match1,actions1)
			
			if (in_port == 1):
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions1, pkt.data)
			else:
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions, pkt.data)
			datapath.send_msg(out)
			
		if (datapath.id == 1):
			match=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.1', ipv4_dst='10.0.0.2', tcp_src=tcp_pkt.src_port, 
				tcp_dst=tcp_pkt.dst_port)
			actions=[parser.OFPActionOutput(2)]
			self.add_flow(datapath,10,match,actions)
			
			match1=parser.OFPMatch(eth_type=0x0800,ip_proto=6, ipv4_src='10.0.0.2', ipv4_dst='10.0.0.1', tcp_src=tcp_pkt.src_port,
				tcp_dst=tcp_pkt.dst_port)
			actions1=[parser.OFPActionOutput(1)]
			self.add_flow(datapath,10,match1,actions1)
			
			if (in_port == 1):
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions, pkt.data)
			else:
				out = parser.OFPPacketOut(datapath, ofproto.OFP_NO_BUFFER, 
					ofproto.OFPP_CONTROLLER, actions1$, pkt.data)
			datapath.send_msg(out)