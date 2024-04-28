import pyshark


filename = "./cap5.pcap"
stream_number = 2271

capture = pyshark.FileCapture(filename, display_filter=f'tcp.stream eq {stream_number}')


conversation = ""

try:
    for packet in capture:
        if 'TCP' in packet and hasattr(packet.tcp, 'payload'):
            try:
                hex_payload = packet.tcp.payload.replace(':', '')
                byte_payload = bytes.fromhex(hex_payload)
                try:
                    conversation += byte_payload.decode('ascii')
                except UnicodeDecodeError:
                    conversation += byte_payload.decode('utf-8', errors='replace')
            except ValueError:
                pass
except KeyboardInterrupt:
    pass
finally:
    capture.close()


print("\nRicostruzione della conversazione:\n")
print(conversation)
