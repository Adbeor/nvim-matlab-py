#!/usr/bin/env python3
"""
Servidor para la comunicación con MATLAB.
Este script se ejecuta independientemente y mantiene una conexión con MATLAB.
La comunicación con el editor se realiza a través de un socket.
"""

import os
import sys
import socket
import subprocess
import threading
import time
import json
import tempfile
import argparse
import signal
import atexit

class MatlabServer:
    def __init__(self, matlab_executable, port=43889, host='127.0.0.1'):
        self.matlab_executable = matlab_executable
        self.port = port
        self.host = host
        self.socket = None
        self.matlab_process = None
        self.running = False
        self.log_file = os.path.join(tempfile.gettempdir(), 'nvim_matlab_py_server.log')
        
        # Configurar manejo de señales para cierre limpio
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        atexit.register(self.cleanup)
        
        # Iniciar el archivo de log
        with open(self.log_file, 'w') as f:
            f.write(f"Servidor MATLAB iniciado: puerto={port}, matlab={matlab_executable}\n")
    
    def log(self, message):
        """Escribe un mensaje en el archivo de log"""
        with open(self.log_file, 'a') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    
    def start_matlab(self):
        """Inicia el proceso de MATLAB"""
        try:
            args = [self.matlab_executable, '-nodesktop', '-nosplash']
            self.matlab_process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0
            )
            self.log(f"Proceso MATLAB iniciado (PID: {self.matlab_process.pid})")
            
            # Iniciar un hilo para monitorear la salida de MATLAB
            thread = threading.Thread(target=self.monitor_matlab_output, daemon=True)
            thread.start()
            
            return True
        except Exception as e:
            self.log(f"Error al iniciar MATLAB: {str(e)}")
            return False
    
    def monitor_matlab_output(self):
        """Monitorea la salida de MATLAB"""
        while self.matlab_process and self.running:
            try:
                line = self.matlab_process.stdout.readline()
                if not line:
                    break
                self.log(f"MATLAB: {line.strip()}")
            except Exception as e:
                self.log(f"Error al leer salida de MATLAB: {str(e)}")
                break
    
    def start_server(self):
        """Inicia el servidor de socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Reutilizar la dirección/puerto
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            self.log(f"Servidor escuchando en {self.host}:{self.port}")
            return True
        except Exception as e:
            self.log(f"Error al iniciar el servidor: {str(e)}")
            return False
    
    def handle_signal(self, signum, frame):
        """Maneja señales para cierre limpio"""
        self.log(f"Recibida señal {signum}, cerrando el servidor...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Limpia recursos al cerrar"""
        if self.matlab_process:
            try:
                self.log("Terminando proceso MATLAB...")
                self.matlab_process.terminate()
                self.matlab_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("MATLAB no respondió al cierre, forzando...")
                self.matlab_process.kill()
            except Exception as e:
                self.log(f"Error al cerrar MATLAB: {str(e)}")
        
        if self.socket:
            try:
                self.socket.close()
                self.log("Socket cerrado")
            except Exception as e:
                self.log(f"Error al cerrar socket: {str(e)}")
    
    def run(self):
        """Ejecuta el bucle principal del servidor"""
        if not self.start_matlab():
            self.log("No se pudo iniciar MATLAB, abortando...")
            return False
        
        if not self.start_server():
            self.log("No se pudo iniciar el servidor, abortando...")
            return False
        
        self.log("Servidor iniciado completamente")
        
        while self.running:
            try:
                # Configurar timeout para que el socket no bloquee permanentemente
                self.socket.settimeout(1.0)
                try:
                    client_socket, address = self.socket.accept()
                    self.log(f"Nueva conexión desde {address}")
                    self.handle_client(client_socket)
                except socket.timeout:
                    # Es normal que ocurra timeout, permite verificar si seguimos ejecutando
                    continue
            except Exception as e:
                self.log(f"Error en el bucle principal: {str(e)}")
                if not self.running:
                    break
        
        self.log("Servidor detenido")
        return True
    
    def handle_client(self, client_socket):
        """Maneja una conexión de cliente"""
        try:
            client_socket.settimeout(0.5)  # Timeout más corto para clientes
            
            # Recibir datos
            data = b""
            while self.running:
                try:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                    # Verificar si tenemos un mensaje completo (terminado en newline)
                    if data.endswith(b'\n'):
                        break
                except socket.timeout:
                    continue
            
            if not data:
                self.log("Conexión cerrada por el cliente sin datos")
                client_socket.close()
                return
            
            # Procesar el comando
            command = data.decode('utf-8').strip()
            self.log(f"Comando recibido: {command}")
            
            # Enviar el comando a MATLAB
            if self.matlab_process and self.matlab_process.poll() is None:
                try:
                    self.matlab_process.stdin.write(command + "\n")
                    self.matlab_process.stdin.flush()
                    
                    # Enviar respuesta de éxito al cliente
                    response = json.dumps({"status": "success"})
                    client_socket.sendall(response.encode('utf-8'))
                except Exception as e:
                    self.log(f"Error al enviar comando a MATLAB: {str(e)}")
                    response = json.dumps({"status": "error", "message": str(e)})
                    client_socket.sendall(response.encode('utf-8'))
            else:
                self.log("MATLAB no está en ejecución")
                response = json.dumps({"status": "error", "message": "MATLAB no está en ejecución"})
                client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            self.log(f"Error al manejar cliente: {str(e)}")
        finally:
            client_socket.close()

def main():
    parser = argparse.ArgumentParser(description='Servidor para comunicación con MATLAB')
    parser.add_argument('--matlab', dest='matlab_executable', default='matlab',
                      help='Ruta al ejecutable de MATLAB')
    parser.add_argument('--port', dest='port', type=int, default=43889,
                      help='Puerto para el servidor (predeterminado: 43889)')
    parser.add_argument('--host', dest='host', default='127.0.0.1',
                      help='Host para el servidor (predeterminado: 127.0.0.1)')
    
    args = parser.parse_args()
    
    server = MatlabServer(
        matlab_executable=args.matlab_executable,
        port=args.port,
        host=args.host
    )
    
    success = server.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
