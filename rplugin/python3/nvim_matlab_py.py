import os
import re
import subprocess
from pynvim import plugin, command

class MatlabProcess:
    """Clase para gestionar la comunicación con MATLAB"""
    
    def __init__(self, nvim):
        self.nvim = nvim
        self.process = None
        self.matlab_executable = nvim.vars.get('matlab_executable', 'matlab')
    
    def ensure_running(self):
        """Asegura que el proceso de MATLAB esté ejecutándose"""
        if self.process is None or self.process.poll() is not None:
            # Iniciar MATLAB en modo no interactivo
            args = [self.matlab_executable, '-nodesktop', '-nosplash']
            try:
                self.process = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=0
                )
                self.nvim.command('echom "MATLAB iniciado"')
            except FileNotFoundError:
                self.nvim.error(f"No se encontró MATLAB en {self.matlab_executable}")
                return False
        return True
    
    def send_command(self, command):
        """Envía un comando a MATLAB"""
        if not self.ensure_running():
            return
            
        # Formatear el comando para MATLAB
        matlab_cmd = f"{command}\n"
        
        try:
            self.process.stdin.write(matlab_cmd)
            self.process.stdin.flush()
            self.nvim.command(f'echom "Comando enviado a MATLAB: {command}"')
        except Exception as e:
            self.nvim.error(f"Error al enviar comando a MATLAB: {str(e)}")

@plugin
class NvimMatlabPy:
    def __init__(self, nvim):
        self.nvim = nvim
        self.matlab = MatlabProcess(nvim)
    
    @command('MatlabRun', nargs=0, sync=False)
    def run_file(self):
        """Ejecuta el archivo actual en MATLAB"""
        current_file = self.nvim.current.buffer.name
        if not current_file.endswith('.m'):
            self.nvim.error("El archivo actual no es un archivo MATLAB (.m)")
            return
            
        # Cambiar el directorio de trabajo de MATLAB al del archivo actual
        directory = os.path.dirname(current_file)
        filename = os.path.basename(current_file)
        basename = os.path.splitext(filename)[0]
        
        # Comandos para MATLAB
        cd_cmd = f"cd('{directory.replace("'", "''")}');"
        run_cmd = f"run('{basename}');"
        
        self.matlab.send_command(cd_cmd)
        self.matlab.send_command(run_cmd)
    
    @command('MatlabRunCell', nargs=0, sync=False)
    def run_cell(self):
        """Ejecuta la celda actual (código entre %% delimitadores)"""
        buffer = self.nvim.current.buffer
        cursor_row, _ = self.nvim.current.window.cursor
        
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
        self.matlab.send_command(cell_content)
    
    @command('MatlabRunLine', nargs=0, sync=False)
    def run_line(self):
        """Ejecuta la línea actual en MATLAB"""
        line = self.nvim.current.line
        if line.strip():
            self.matlab.send_command(line)
    
    @command('MatlabRunSelection', range='', nargs=0, sync=False)
    def run_selection(self):
        """Ejecuta la selección visual en MATLAB"""
        buffer = self.nvim.current.buffer
        start_row, start_col = self.nvim.current.buffer.mark('<')
        end_row, end_col = self.nvim.current.buffer.mark('>')
        
        if start_row == end_row:
            # Selección en una sola línea
            line = buffer[start_row-1]
            selection = line[start_col:end_col+1]
        else:
            # Selección multilínea
            lines = buffer[start_row-1:end_row]
            if lines:
                # Ajustar primera y última línea para considerar columnas
                lines[0] = lines[0][start_col:]
                lines[-1] = lines[-1][:end_col+1]
                selection = '\n'.join(lines)
            else:
                selection = ""
                
        if selection.strip():
            self.matlab.send_command(selection)
    
    @command('MatlabToggleFile', nargs=0, sync=True)
    def toggle_file(self):
        """Alterna entre un archivo .m y su archivo de test correspondiente"""
        current_file = self.nvim.current.buffer.name
        if not current_file.endswith('.m'):
            self.nvim.error("El archivo actual no es un archivo MATLAB (.m)")
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
                self.nvim.command(f'edit {main_file}')
            else:
                self.nvim.error(f"No se encontró el archivo principal: {main_file}")
        else:
            # Es un archivo principal, buscar archivos de test
            test_prefix_file = os.path.join(directory, f"test_{basename}.m")
            test_suffix_file = os.path.join(directory, f"{basename}_test.m")
            
            if os.path.exists(test_prefix_file):
                self.nvim.command(f'edit {test_prefix_file}')
            elif os.path.exists(test_suffix_file):
                self.nvim.command(f'edit {test_suffix_file}')
            else:
                self.nvim.error(f"No se encontraron archivos de test para {basename}.m")
