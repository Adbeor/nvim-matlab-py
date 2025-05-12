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

call s:init_python()
