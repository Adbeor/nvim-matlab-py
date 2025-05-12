import os
import re
import subprocess
import time
import pynvim

# Variable global para el proceso de MATLAB
matlab_process = None
debug_mode = False

def _get_nvim():
    """Obtiene el objeto nvim actual"""
    try:
        return pynvim.api.nvim.Nvim.from_nvim()
    except:
        # No estamos en un contexto de plugin, probablemente llamado directamente
        return None

def _debug(nvim, message):
    """Muestra un mensaje de depuración si el modo debug está activado"""
    global debug_mode
    if debug_mode:
        nvim.command(f'echom "[MATLAB-DEBUG] {message}"')

def set_debug_mode(enabled=True):
    """Activa o desactiva el modo de depuración"""
    global debug_mode
    debug_mode = enabled
    nvim = _get_nvim()
    if nvim:
        nvim.command(f'echom "Modo de depuración {"activado" if enabled else "desactivado"}"')

def start_matlab_server(force=False):
    """Inicia el servidor de MATLAB explícitamente"""
    global matlab_process
    nvim = _get_nvim()
    if not nvim:
        return
        
    if matlab_process is not None and matlab_process.poll() is None and not force:
        nvim.command('echom "El servidor MATLAB ya está en ejecución"')
        return
        
    _ensure_matlab_running(nvim, force)
    
def stop_matlab_server():
    """Detiene el servidor MATLAB"""
    global matlab_process
    nvim = _get_nvim()
    if not nvim:
        return
        
    if matlab_process is None or matlab_process.poll() is not None:
        nvim.command('echom "No hay servidor MATLAB en ejecución"')
        return
        
    try:
        # Enviar comando de salida a MATLAB
        matlab_process.stdin.write("exit;\n")
        matlab_process.stdin.flush()
        
        # Esperar un poco a que MATLAB se cierre correctamente
        time.sleep(0.5)
        
        # Si aún está en ejecución, terminar el proceso
        if matlab_process.poll() is None:
            matlab_process.terminate()
            time.sleep(0.5)
            if matlab_process.poll() is None:
                matlab_process.kill()
                
        matlab_process = None
        nvim.command('echom "Servidor MATLAB detenido"')
    except Exception as e:
        nvim.error(f"Error al detener el servidor MATLAB: {str(e)}")

def _ensure_matlab_running(nvim, force=False):
    """Asegura que el proceso de MATLAB esté en ejecución"""
    global matlab_process
    
    matlab_executable = nvim.vars.get('matlab_executable', 'matlab')
    server_port = nvim.vars.get('matlab_server_port', '0')  # 0 = puerto aleatorio
    
    _debug(nvim, f"Verificando servidor MATLAB. Force={force}")
    
    if matlab_process is not None and matlab_process.poll() is None and not force:
        _debug(nvim, "El servidor MATLAB ya está en ejecución")
        return True
        
    if matlab_process is not None:
        _debug(nvim, "Deteniendo el servidor MATLAB existente")
        try:
            matlab_process.terminate()
            time.sleep(0.5)
        except:
            pass
        matlab_process = None
        
    try:
        _debug(nvim, f"Iniciando MATLAB desde: {matlab_executable}")
        args = [matlab_executable, '-nodesktop', '-nosplash']
        matlab_process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=0
        )
        
        # Esperar un momento para que MATLAB se inicie
        time.sleep(1)
        
        if matlab_process.poll() is not None:
            nvim.error(f"MATLAB no pudo iniciarse. Código de salida: {matlab_process.returncode}")
            return False
            
        # Verificar si MATLAB está respondiendo
        matlab_process.stdin.write("disp('MATLAB_SERVER_STARTED');\n")
        matlab_process.stdin.flush()
        
        # Intentar leer la salida para verificar que MATLAB está activo
        try:
            # Solo leer si hay datos disponibles (no bloquear)
            for _ in range(10):  # Intentar algunas veces
                line = matlab_process.stdout.readline()
                if "MATLAB_SERVER_STARTED" in line:
                    nvim.command('echom "Servidor MATLAB iniciado correctamente"')
                    return True
                time.sleep(0.2)
        except:
            pass
            
        nvim.command('echom "Servidor MATLAB iniciado, pero no se pudo verificar la respuesta"')
        return True
    except FileNotFoundError:
        nvim.error(f"No se encontró MATLAB en {matlab_executable}. Verifica la ruta en la configuración.")
        return False
    except Exception as e:
        nvim.error(f"Error al iniciar MATLAB: {str(e)}")
        return False

def _send_to_matlab(nvim, command):
    """Envía un comando a MATLAB"""
    if not _ensure_matlab_running(nvim):
        return
        
    _debug(nvim, f"Enviando comando: {command[:50]}...")
        
    try:
        matlab_process.stdin.write(command + "\n")
        matlab_process.stdin.flush()
        nvim.command(f'echom "Comando enviado a MATLAB"')
    except Exception as e:
        nvim.error(f"Error al enviar comando a MATLAB: {str(e)}")

def run_file():
    """Ejecuta el archivo MATLAB actual"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    current_file = nvim.current.buffer.name
    if not current_file.endswith('.m'):
        nvim.error("El archivo actual no es un archivo MATLAB (.m)")
        return
        
    directory = os.path.dirname(current_file)
    filename = os.path.basename(current_file)
    basename = os.path.splitext(filename)[0]
    
    _debug(nvim, f"Ejecutando archivo: {basename} desde {directory}")
    
    cd_cmd = f"cd('{directory.replace("'", "''")}');"
    run_cmd = f"run('{basename}');"
    
    _send_to_matlab(nvim, cd_cmd)
    _send_to_matlab(nvim, run_cmd)

def run_cell():
    """Ejecuta la celda actual (código entre %% delimitadores)"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    buffer = nvim.current.buffer
    cursor_row, _ = nvim.current.window.cursor
    
    # Ajustar cursor_row a índice base 0 para trabajar con el buffer
    cursor_row = cursor_row - 1
    
    _debug(nvim, f"Buscando celda en la línea {cursor_row+1}")
    
    # Buscar hacia atrás el inicio de la celda
    start_row = cursor_row
    while start_row > 0:
        if buffer[start_row-1].strip().startswith('%%'):
            break
        start_row -= 1
        
    # Buscar hacia adelante el final de la celda
    end_row = cursor_row
    while end_row < len(buffer):
        if end_row < len(buffer)-1 and buffer[end_row+1].strip().startswith('%%'):
            break
        end_row += 1
        
    # Obtener el contenido de la celda
    cell_content = '\n'.join(buffer[start_row:end_row+1])
    
    _debug(nvim, f"Celda encontrada desde línea {start_row+1} hasta {end_row+1}")
    
    # Enviar el contenido a MATLAB
    _send_to_matlab(nvim, cell_content)

def run_line():
    """Ejecuta la línea actual en MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    line = nvim.current.line
    if line.strip():
        _debug(nvim, f"Ejecutando línea: {line}")
        _send_to_matlab(nvim, line)

def run_selection():
    """Ejecuta la selección visual en MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    buffer = nvim.current.buffer
    
    # Obtener marcas de selección visual
    try:
        start_row, start_col = buffer.mark('<')
        end_row, end_col = buffer.mark('>')
        
        # Ajustar índices basados en 1 a basados en 0
        start_row -= 1
        end_row -= 1
        
        _debug(nvim, f"Selección desde ({start_row+1},{start_col+1}) hasta ({end_row+1},{end_col+1})")
        
    except:
        nvim.error("No hay selección visual activa")
        return
    
    if start_row == end_row:
        # Selección en una sola línea
        line = buffer[start_row]
        selection = line[start_col:end_col+1]
    else:
        # Selección multilínea
        lines = buffer[start_row:end_row+1]
        if lines:
            # Ajustar primera y última línea
            lines[0] = lines[0][start_col:]
            lines[-1] = lines[-1][:end_col+1]
            selection = '\n'.join(lines)
        else:
            selection = ""
            
    if selection.strip():
        _send_to_matlab(nvim, selection)

def toggle_file():
    """Alterna entre un archivo .m y su archivo de test correspondiente"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    current_file = nvim.current.buffer.name
    if not current_file.endswith('.m'):
        nvim.error("El archivo actual no es un archivo MATLAB (.m)")
        return
        
    directory = os.path.dirname(current_file)
    filename = os.path.basename(current_file)
    basename = os.path.splitext(filename)[0]
    
    _debug(nvim, f"Alternando archivo: {basename}")
    
    # Detectar si es un archivo de test o un archivo normal
    test_pattern = r'^test_(.+)$|^(.+)_test$'
    match = re.match(test_pattern, basename)
    
    if match:
        # Es un archivo de test, cambiar al archivo principal
        if match.group(1):  # formato test_archivo
            main_file = os.path.join(directory, f"{match.group(1)}.m")
        else:  # formato archivo_test
            main_file = os.path.join(directory, f"{basename[:-5]}.m")
            
        if os.path.exists(main_file):
            nvim.command(f'edit {main_file}')
        else:
            nvim.error(f"No se encontró el archivo principal: {main_file}")
    else:
        # Es un archivo principal, buscar archivos de test
        test_prefix_file = os.path.join(directory, f"test_{basename}.m")
        test_suffix_file = os.path.join(directory, f"{basename}_test.m")
        
        if os.path.exists(test_prefix_file):
            nvim.command(f'edit {test_prefix_file}')
        elif os.path.exists(test_suffix_file):
            nvim.command(f'edit {test_suffix_file}')
        else:
            nvim.error(f"No se encontraron archivos de test para {basename}.m")

def get_matlab_status():
    """Obtiene el estado actual del servidor MATLAB"""
    global matlab_process
    nvim = _get_nvim()
    if not nvim:
        return
        
    if matlab_process is None:
        nvim.command('echom "Estado del servidor MATLAB: No iniciado"')
    elif matlab_process.poll() is None:
        nvim.command('echom "Estado del servidor MATLAB: En ejecución"')
    else:
        nvim.command(f'echom "Estado del servidor MATLAB: Detenido (código de salida: {matlab_process.returncode})"')
