.PHONY: test
# Offline native tests only. This does not touch the card.
test:
	python3 switch/test_lifetime.py
	python3 switch/test_stop.py
	python3 switch/test_concurrent.py
	python3 switch/test_lifecycle.py
	python3 switch/test_failed_teardown.py
	python3 switch/test_contain.py
	python3 switch/test_contain_cases.py
	python3 switch/test_contain_failures.py
	python3 control/test_framed.py
	python3 control/test_mu.py
	python3 control/test_control.py
	python3 control/demo.py
	python3 transport/test_wire.py
	python3 transport/test_visitors.py
	python3 transport/test_transport.py
	python3 test_network.py
	python3 transport/test_ipv6_gateway.py
	python3 autonomous/test_transport.py
