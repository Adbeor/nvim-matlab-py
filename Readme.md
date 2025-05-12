# nvim-matlab-py

Un plugin minimalista para Neovim que proporciona integración con MATLAB, inspirado en [vim-matlab](https://github.com/daeyun/vim-matlab/) pero escrito en Python3.

## Características

- Ejecutar código MATLAB directamente desde Neovim
- Enviar selección o línea actual a MATLAB
- Cambiar entre archivos .m y sus tests
- Ejecutar archivos MATLAB completos

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

" Mapeos de teclas (opcional)
nnoremap <leader>rr :MatlabRun<CR>
nnoremap <leader>rc :MatlabRunCell<CR>
nnoremap <leader>rl :MatlabRunLine<CR>
vnoremap <leader>rs :MatlabRunSelection<CR>
nnoremap <leader>mt :MatlabToggleFile<CR>
```

O en Lua:

```lua
vim.g.matlab_executable = '/ruta/a/matlab'

vim.keymap.set('n', '<leader>rr', ':MatlabRun<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>rc', ':MatlabRunCell<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>rl', ':MatlabRunLine<CR>', { noremap = true, silent = true })
vim.keymap.set('v', '<leader>rs', ':MatlabRunSelection<CR>', { noremap = true, silent = true })
vim.keymap.set('n', '<leader>mt', ':MatlabToggleFile<CR>', { noremap = true, silent = true })
```

## Uso

- `:MatlabRun` - Ejecuta el archivo actual en MATLAB
- `:MatlabRunCell` - Ejecuta la celda actual (código entre `%%` delimitadores)
- `:MatlabRunLine` - Ejecuta la línea actual en MATLAB
- `:MatlabRunSelection` - Ejecuta la selección visual en MATLAB
- `:MatlabToggleFile` - Cambia entre un archivo .m y su archivo de test correspondiente
