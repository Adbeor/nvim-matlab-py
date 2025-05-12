import os
import re
import subprocess
import pynvim

# Variable global para el proceso de MATLAB
matlab_process = None

def _get_nvim():
    """Obtiene el objeto nvim actual"""
    try:
        return pynvim.api.nvim.Nvim.from_nvim()
    except:
        # No estamos en un contexto de plugin, probablemente llamado directamente
        return None

def _ensure_matlab_running(nvim):
    """Asegura que el proceso de MATLAB esté en ejecución"""
    global matlab_process
    
    matlab_executable = nvim.vars.get('matlab_executable', 'matlab')
    
    if matlab_process is None or matlab_process.poll() is not None:
        try:
            args = [matlab_executable, '-nodesktop', '-nosplash']
            matlab_process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0
            )
            nvim.command('echom "MATLAB iniciado"')
            return True
        except FileNotFoundError:
            nvim.error(f"No se encontró MATLAB en {matlab_executable}")
            return False
    return True

def _send_to_matlab(nvim, command):
    """Envía un comando a MATLAB"""
    if not _ensure_matlab_running(nvim):
        return
        
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
    
    # Buscar los límites de la celda
    start_row = cursor_row
    end_row = cursor_row
    
    # Buscar hacia atrás el inicio de la celda
    while start_row > 1:
        if buffer[start_row-2].strip().startswith('%%'):
            break
        start_row -= 1
        
    # Buscar hacia adelante el final de la celda
    while end_row < len(buffer):
        if end_row < len(buffer)-1 and buffer[end_row].strip().startswith('%%'):
            break
        end_row += 1
        
    # Obtener el contenido de la celda
    cell_content = '\n'.join(buffer[start_row-1:end_row])
    
    # Enviar el contenido a MATLAB
    _send_to_matlab(nvim, cell_content)

def run_line():
    """Ejecuta la línea actual en MATLAB"""
    nvim = _get_nvim()
    if not nvim:
        return
        
    line = nvim.current.line
    if line.strip():
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
    except:
        nvim.error("No hay selección visual activa")
        return
    
    # Ajustar índices basados en 0 a basados en 1
    start_row -= 1
    end_row -= 1
    
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
