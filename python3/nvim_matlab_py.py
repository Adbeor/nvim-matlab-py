import os
import re
import subprocess
import time
import threading
import pynvim

# Variables globales
matlab_process = None
matlab_output_buffer = None
matlab_output_window = None
thread_running = False

def _get_nvim():
    """Obtiene el objeto nvim actual"""
    try:
        return pynvim.api.nvim.Nvim.from_nvim()
    except:
        return None

def _create_output_buffer(nvim):
    """Crea o recupera el buffer de salida de MATLAB"""
    global matlab_output_buffer, matlab_output_window
    
    # Comprobar si ya existe un buffer para la salida de MATLAB
    for buf in nvim.buffers:
        if buf.name.endswith('MATLAB_OUTPUT'):
            matlab_output_buffer = buf
            break
    
    # Si no existe, crear uno nuevo
    if matlab_output_buffer is None:
        # Guardar la ventana actual
        current_window = nvim.current.window
        
        # Crear un nuevo buffer y ventana vertical
        nvim.command('vsplit MATLAB_OUTPUT')
        matlab_output_buffer = nvim.current.buffer
        matlab_output_window = nvim.current.window
        
        # Configurar el buffer
        nvim.command('setlocal buftype=nofile')
        nvim.command('setlocal noswapfile')
        nvim.command('setlocal syntax=matlab')
        
        # Volver a la ventana original
        nvim.current.window = current_window
    else:
        # Comprobar si hay una ventana mostrando este buffer
        window_found = False
        for window in nvim.windows:
            if window.buffer == matlab_output_buffer:
                matlab_output_window = window
                window_found = True
                break
        
        # Si no hay ventana mostrando el buffer, crear una
        if not window_found:
            current_window = nvim.current.window
            nvim.command('vsplit')
            nvim.command(f'buffer {matlab_output_buffer.number}')
            matlab_output_window = nvim.current.window
            nvim.current.window = current_window

def _update_output_buffer(nvim, text):
    """Actualiza el buffer de salida con nuevo texto"""
    global matlab_output_buffer
    
    if matlab_output_buffer is None:
        _create_output_buffer(nvim)
    
    # Añadir texto al final del buffer
    matlab_output_buffer.append(text.splitlines())
    
    # Desplazar a la última línea si la ventana está visible
    if matlab_output_window is not None:
        nvim.command('noautocmd call win_execute({}, "normal! G")'.format(matlab_output_window.handle))

def _read_matlab_output(nvim):
    """Lee la salida de MATLAB continuamente"""
    global matlab_process, thread_running
    
    # Marcar el hilo como en ejecución
    thread_running = True
    
    while thread_running and matlab_process and matlab_process.poll() is None:
        try:
            # Leer una línea de la salida de MATLAB
            line = matlab_process.stdout.readline()
            if line:
                # Programar la actualización del buffer en el hilo principal de Neovim
                nvim.async_call(_update_output_buffer, nvim, line)
        except Exception as e:
            nvim.async_call(nvim.command, f'echom "Error leyendo salida de MATLAB: {str(e)}"')
            break
    
    # Marcar el hilo como detenido
    thread_running = False

def start_matlab_server():
    """Inicia el servidor de MATLAB y muestra su salida en un buffer"""
    global matlab_process, thread_running
    
    nvim = _get_nvim()
    if not nvim:
        return
    
    # Detener cualquier proceso de MATLAB existente
    if matlab_process is not None and matlab_process.poll() is None:
        nvim.command('echom "MATLAB ya está en ejecución"')
        return
    
    # Preparar el buffer de salida
    _create_output_buffer(nvim)
    _update_output_buffer(nvim, "=== Iniciando MATLAB ===\n")
    
    # Iniciar MATLAB
    matlab_executable = nvim.vars.get('matlab_executable', 'matlab')
    
    try:
        args = [matlab_executable, '-nodesktop', '-nosplash']
        matlab_process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Iniciar un hilo para leer la salida
        output_thread = threading.Thread(target=_read_matlab_output, args=(nvim,))
        output_thread.daemon = True
        output_thread.start()
        
        # Enviar un comando inicial para verificar que MATLAB está funcionando
        matlab_process.stdin.write("disp('MATLAB iniciado correctamente');\n")
        matlab_process.stdin.flush()
        
        nvim.command('echom "Servidor MATLAB iniciado"')
    except FileNotFoundError:
        nvim.command('echoerr "No se encontró MATLAB en ' + matlab_executable + '"')
    except Exception as e:
        nvim.command('echoerr "Error al iniciar MATLAB: ' + str(e) + '"')

def stop_matlab_server():
    """Detiene el servidor MATLAB"""
    global matlab_process, thread_running
    
    nvim = _get_nvim()
    if not nvim:
        return
    
    if matlab_process is None or matlab_process.poll() is not None:
        nvim.command('echom "No hay servidor MATLAB en ejecución"')
        return
    
    try:
        # Detener el hilo de lectura
        thread_running = False
        
        # Enviar comando de salida a MATLAB
        matlab_process.stdin.write("exit;\n")
        matlab_process.stdin.flush()
        
        # Esperar a que termine
        for _ in range(10):  # Esperar hasta 1 segundo
            if matlab_process.poll() is not None:
                break
            time.sleep(0.1)
        
        # Si sigue en ejecución, terminarlo
        if matlab_process.poll() is None:
            matlab_process.terminate()
            time.sleep(0.5)
            if matlab_process.poll() is None:
                matlab_process.kill()
        
        matlab_process = None
        nvim.command('echom "Servidor MATLAB detenido"')
        
        # Actualizar el buffer de salida
        _update_output_buffer(nvim, "\n=== MATLAB detenido ===\n")
    except Exception as e:
        nvim.command('echoerr "Error al detener MATLAB: ' + str(e) + '"')

def _send_to_matlab(command):
    """Envía un comando a MATLAB"""
    global matlab_process
    
    nvim = _get_nvim()
    if not nvim:
        return
    
    # Comprobar si MATLAB está en ejecución
    if matlab_process is None or matlab_process.poll() is not None:
        nvim.command('echom "MATLAB no está en ejecución. Iniciando..."')
        start_matlab_server()
        # Esperar un momento para que MATLAB se inicie
        time.sleep(1)
    
    # Enviar el comando
    try:
        matlab_process.stdin.write(command + "\n")
        matlab_process.stdin.flush()
        nvim.command('echom "Comando enviado a MATLAB"')
        
        # Mostrar el comando en el buffer de salida
        _update_output_buffer(nvim, f"\n>> {command}\n")
    except Exception as e:
        nvim.command('echoerr "Error al enviar comando a MATLAB: ' + str(e) + '"')

def run_file():
    """Ejecuta el archivo MATLAB actual"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    current_file = nvim.current.buffer.name
    if not current_file.endswith('.m'):
        nvim.command('echoerr "El archivo actual no es un archivo MATLAB (.m)"')
        return
    
    directory = os.path.dirname(current_file)
    filename = os.path.basename(current_file)
    basename = os.path.splitext(filename)[0]
    
    # Comandos para MATLAB
    cd_cmd = f"cd('{directory.replace("'", "''")}');"
    run_cmd = f"run('{basename}');"
    
    _send_to_matlab(cd_cmd)
    _send_to_matlab(run_cmd)

def run_cell():
    """Ejecuta la celda actual (código entre %% delimitadores)"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    buffer = nvim.current.buffer
    cursor_row, _ = nvim.current.window.cursor
    
    # Ajustar cursor_row a índice base 0 para trabajar con el buffer
    cursor_row = cursor_row - 1
    
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
    
    # Enviar el contenido a MATLAB
    _send_to_matlab(cell_content)

def run_line():
    """Ejecuta la línea actual en MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    line = nvim.current.line
    if line.strip():
        _send_to_matlab(line)

def run_selection():
    """Ejecuta la selección visual en MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    buffer = nvim.current.buffer
    
    try:
        # Obtener marcas de selección visual
        start_row, start_col = buffer.mark('<')
        end_row, end_col = buffer.mark('>')
        
        # Ajustar índices basados en 1 a basados en 0
        start_row -= 1
        end_row -= 1
    except:
        nvim.command('echoerr "No hay selección visual activa"')
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
        _send_to_matlab(selection)

def toggle_file():
    """Alterna entre un archivo .m y su archivo de test correspondiente"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    current_file = nvim.current.buffer.name
    if not current_file.endswith('.m'):
        nvim.command('echoerr "El archivo actual no es un archivo MATLAB (.m)"')
        return
    
    directory = os.path.dirname(current_file)
    filename = os.path.basename(current_file)
    basename = os.path.splitext(filename)[0]
    
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
            nvim.command(f'echoerr "No se encontró el archivo principal: {main_file}"')
    else:
        # Es un archivo principal, buscar archivos de test
        test_prefix_file = os.path.join(directory, f"test_{basename}.m")
        test_suffix_file = os.path.join(directory, f"{basename}_test.m")
        
        if os.path.exists(test_prefix_file):
            nvim.command(f'edit {test_prefix_file}')
        elif os.path.exists(test_suffix_file):
            nvim.command(f'edit {test_suffix_file}')
        else:
            nvim.command(f'echoerr "No se encontraron archivos de test para {basename}.m"')

def toggle_matlab_window():
    """Muestra u oculta la ventana de salida de MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
    
    global matlab_output_buffer, matlab_output_window
    
    # Comprobar si existe el buffer de salida
    if matlab_output_buffer is None:
        # Si no existe, crearlo
        _create_output_buffer(nvim)
        return
    
    # Comprobar si hay alguna ventana mostrando el buffer
    window_found = False
    for window in nvim.windows:
        if window.buffer == matlab_output_buffer:
            window_found = True
            # Cerrar la ventana
            nvim.command(f'execute {window.number} . "wincmd c"')
            matlab_output_window = None
            break
    
    # Si no se encontró ninguna ventana, mostrar el buffer
    if not window_found:
        current_window = nvim.current.window
        nvim.command('vsplit')
        nvim.command(f'buffer {matlab_output_buffer.number}')
        matlab_output_window = nvim.current.window
        nvim.current.window = current_window
