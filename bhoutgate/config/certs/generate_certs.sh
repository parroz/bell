#!/bin/bash

# Generate CA certificate
openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/C=PT/ST=Lisbon/L=Lisbon/O=BHOUTGate/OU=Development/CN=BHOUTGate CA"

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -config openssl.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -extensions v3_req -extfile openssl.cnf

# Generate client certificate
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -config openssl.cnf
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650 -extensions v3_req -extfile openssl.cnf

# Set proper permissions
chmod 600 *.key
chmod 644 *.crt 