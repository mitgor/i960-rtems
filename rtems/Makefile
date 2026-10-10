.PHONY: test
# Offline native tests only. This does not touch the card.
test:
	python3 transport/test_wire.py
	python3 transport/test_transport.py
	python3 test_network.py
	python3 transport/test_ipv6_gateway.py
