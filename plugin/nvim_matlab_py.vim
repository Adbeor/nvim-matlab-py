if exists('g:loaded_nvim_matlab_py') || &cp
  finish
endif
let g:loaded_nvim_matlab_py = 1

" Configuración predeterminada
if !exists('g:matlab_executable')
  if executable('matlab')
    let g:matlab_executable = 'matlab'
  else
    echohl WarningMsg | echom "nvim-matlab-py: No se encontró MATLAB. Configure g:matlab_executable" | echohl None
  endif
endif

" Inicializar el plugin Python
function! s:init_python() abort
  if has('nvim') && has('python3')
    python3 import nvim_matlab_py
  else
    echohl ErrorMsg | echom "nvim-matlab-py requiere Neovim con soporte Python3" | echohl None
    finish
  endif
endfunction

" Comandos
command! -nargs=0 MatlabRun python3 nvim_matlab_py.run_file()
command! -nargs=0 MatlabRunCell python3 nvim_matlab_py.run_cell()
command! -nargs=0 MatlabRunLine python3 nvim_matlab_py.run_line()
command! -range MatlabRunSelection python3 nvim_matlab_py.run_selection()
command! -nargs=0 MatlabToggleFile python3 nvim_matlab_py.toggle_file()
command! -nargs=0 MatlabStartServer python3 nvim_matlab_py.start_matlab_server()
command! -nargs=0 MatlabStopServer python3 nvim_matlab_py.stop_matlab_server()
command! -nargs=0 MatlabToggleWindow python3 nvim_matlab_py.toggle_matlab_window()

" Mapeos de teclas predeterminados
if !exists('g:matlab_disable_default_mappings') || !g:matlab_disable_default_mappings
  nnoremap <silent> <leader>rr :MatlabRun<CR>
  nnoremap <silent> <leader>rc :MatlabRunCell<CR>
  nnoremap <silent> <leader>rl :MatlabRunLine<CR>
  vnoremap <silent> <leader>rs :MatlabRunSelection<CR>
  nnoremap <silent> <leader>mt :MatlabToggleFile<CR>
  nnoremap <silent> <leader>ms :MatlabStartServer<CR>
  nnoremap <silent> <leader>mq :MatlabStopServer<CR>
  nnoremap <silent> <leader>mw :MatlabToggleWindow<CR>
endif

" Inicializar el plugin
call s:init_python()
