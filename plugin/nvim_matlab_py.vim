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

if !exists('g:matlab_server_port')
  let g:matlab_server_port = 0  " 0 = puerto aleatorio
endif

if !exists('g:matlab_debug_mode')
  let g:matlab_debug_mode = 0  " 0 = desactivado, 1 = activado
endif

" Inicializar el plugin Python
function! s:init_python() abort
  if has('nvim') && has('python3')
    python3 import nvim_matlab_py
    
    " Configurar modo de depuración
    if g:matlab_debug_mode
      python3 nvim_matlab_py.set_debug_mode(True)
    endif
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
command! -nargs=0 MatlabStatus python3 nvim_matlab_py.get_matlab_status()
command! -nargs=0 MatlabToggleDebug python3 nvim_matlab_py.set_debug_mode(not nvim_matlab_py.debug_mode)

" Inicializar el plugin
call s:init_python()
