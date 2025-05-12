# nvim-matlab-py

Un plugin minimalista para Neovim que proporciona integración con MATLAB, inspirado en [vim-matlab](https://github.com/daeyun/vim-matlab/) pero escrito en Python3.

## Características

- Ejecutar código MATLAB directamente desde Neovim
- Enviar selección o línea actual a MATLAB
- Cambiar entre archivos .m y sus tests
- Ejecutar archivos MATLAB completos
- Servidor MATLAB independiente para una comunicación más estable

## Requisitos

- Neovim 0.5.0+
- Python 3.6+
- [pynvim](https://github.com/neovim/pynvim)
- MATLAB instalado y en el PATH

## Instalación

### Con [vim-plug](https://github.com/junegunn/vim-plug)

```vim
Plug 'usuario/nvim-matlab-py'
```

### Con [packer.nvim](https://github.com/wbthomason/packer.nvim)

```lua
use 'usuario/nvim-matlab-py'
```

## Configuración

En tu `init.vim` o `init.lua`:

```vim
" Configura el path de MATLAB si es necesario
let g:matlab_executable = '/ruta/a/matlab'

" Puerto para el servidor MATLAB (opcional)
let g:matlab_server_port = 43889

" Mapeos de teclas (opcional)
nnoremap <leader>rr :MatlabRun<CR>
nnoremap <leader>rc :MatlabRunCell<CR>
nnoremap <leader>rl :MatlabRunLine<CR>
vnoremap <leader>rs :MatlabRunSelection<CR>
nnoremap <leader>mt :MatlabToggleFile<CR>
nnoremap <leader>ms :MatlabStopServer<CR>
```

O en Lua:

```lua
vim.g.matlab_executable = '/ruta/a/matlab'
vim.g.matlab_server_port = 43889

vim.keymap.set('n', '<leader>rr', ':MatlabRun<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>rc', ':MatlabRunCell<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>rl', ':MatlabRunLine<CR>', { noremap = true, silent = true })
vim.keymap.set('v', '<leader>rs', ':MatlabRunSelection<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>mt', ':MatlabToggleFile<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>ms', ':MatlabStopServer<CR>', { noremap = true, silent = true })
```

## Uso

- `:MatlabRun` - Ejecuta el archivo actual en MATLAB
- `:MatlabRunCell` - Ejecuta la celda actual (código entre `%%` delimitadores)
- `:MatlabRunLine` - Ejecuta la línea actual en MATLAB
- `:MatlabRunSelection` - Ejecuta la selección visual en MATLAB
- `:MatlabToggleFile` - Cambia entre un archivo .m y su archivo de test correspondiente
- `:MatlabStopServer` - Detiene el servidor MATLAB si está en ejecución

## Funcionamiento interno

Este plugin utiliza un enfoque cliente-servidor para comunicarse con MATLAB:

1. Al ejecutar cualquier comando, el plugin verifica si el servidor MATLAB está en ejecución
2. Si es necesario, inicia un servidor Python que gestiona una instancia persistente de MATLAB
3. Los comandos se envían al servidor a través de un socket, que los reenvía a MATLAB
4. El servidor permanece activo en segundo plano hasta que se cierra Neovim o se detiene manualmente

Este enfoque proporciona una comunicación más estable y eficiente con MATLAB, similar al plugin original vim-matlab.

## Solución de problemas

Si experimentas problemas con el plugin:

1. Verifica que MATLAB esté instalado y en el PATH del sistema
2. Asegúrate de tener los permisos necesarios para ejecutar MATLAB
3. Comprueba los errores en `:checkhealth` de Neovim
4. Revisa el archivo de log del servidor: `/tmp/nvim_matlab_py_server.log` (en Linux/macOS)

## Licencia

MIT
