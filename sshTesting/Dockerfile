# Usa un'immagine base di Ubuntu
FROM ubuntu:latest

# Installa SSH e altre utilità necessarie
RUN apt-get update && apt-get install -y \
    openssh-server \
    tcpdump \
    rsync \
    curl

# Imposta la password per l'utente root (cambia questa in un ambiente reale)
RUN echo 'root:password' | chpasswd

# Configura SSH per accettare le connessioni (disabilita alcune pratiche non sicure per produzione)
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

RUN mkdir -p /pcap


# SSH login fix. Otherwise user is kicked off after login
RUN mkdir /var/run/sshd

# Espone la porta 22 per il servizio SSH
EXPOSE 22

# Avvia il server SSH
CMD ["/usr/sbin/sshd", "-D"]
