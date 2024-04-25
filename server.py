import pyshark

# Sostituisci con il percorso effettivo al tuo file pcap
filename = "./cap5.pcap"
stream_number = 2271  # ID dello stream TCP da seguire

# Crea un oggetto FileCapture per analizzare il file pcap con un filtro per lo stream TCP specifico
capture = pyshark.FileCapture(filename, display_filter=f'tcp.stream eq {stream_number}')

# Ricostruzione della conversazione
conversation = ""

try:
    for packet in capture:
        # Prova a ottenere il payload in formato testo se esiste
        if 'TCP' in packet and hasattr(packet.tcp, 'payload'):
            # Il payload è in formato esadecimale, quindi prima convertilo
            try:
                hex_payload = packet.tcp.payload.replace(':', '')
                byte_payload = bytes.fromhex(hex_payload)
                # Prova a decodificare come ASCII o UTF-8, altrimenti usa la rappresentazione binaria
                try:
                    conversation += byte_payload.decode('ascii')
                except UnicodeDecodeError:
                    conversation += byte_payload.decode('utf-8', errors='replace')
            except ValueError:
                # Se ci sono caratteri non esadecimali nel payload, ignora questo pacchetto
                pass
except KeyboardInterrupt:
    pass  # Permette all'utente di interrompere l'analisi manualmente
finally:
    capture.close()  # Assicurati che la cattura sia chiusa correttamente

# Stampa la conversazione ricostruita
print("\nRicostruzione della conversazione:\n")
print(conversation)
