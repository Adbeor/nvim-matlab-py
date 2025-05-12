-- nvim-matlab-py Lua API

local M = {}

-- Configura el plugin
M.setup = function(opts)
  opts = opts or {}
  
  -- Configurar la ruta ejecutable de MATLAB
  if opts.matlab_executable then
    vim.g.matlab_executable = opts.matlab_executable
  end
  
  -- Deshabilitar mapeos predeterminados
  if opts.disable_default_mappings then
    vim.g.matlab_disable_default_mappings = true
  end
  
  -- Configurar mapeos de teclas personalizados
  if opts.keymaps then
    if opts.keymaps.run_file then
      vim.keymap.set('n', opts.keymaps.run_file, ':MatlabRun<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.run_cell then
      vim.keymap.set('n', opts.keymaps.run_cell, ':MatlabRunCell<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.run_line then
      vim.keymap.set('n', opts.keymaps.run_line, ':MatlabRunLine<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.run_selection then
      vim.keymap.set('v', opts.keymaps.run_selection, ':MatlabRunSelection<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.toggle_file then
      vim.keymap.set('n', opts.keymaps.toggle_file, ':MatlabToggleFile<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.start_server then
      vim.keymap.set('n', opts.keymaps.start_server, ':MatlabStartServer<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.stop_server then
      vim.keymap.set('n', opts.keymaps.stop_server, ':MatlabStopServer<CR>', { noremap = true, silent = true })
    end
    if opts.keymaps.toggle_window then
      vim.keymap.set('n', opts.keymaps.toggle_window, ':MatlabToggleWindow<CR>', { noremap = true, silent = true })
    end
  end
end

-- Funciones directas para usar en Lua
M.run_file = function()
  vim.cmd('MatlabRun')
end

M.run_cell = function()
  vim.cmd('MatlabRunCell')
end

M.run_line = function()
  vim.cmd('MatlabRunLine')
end

M.run_selection = function()
  vim.cmd('MatlabRunSelection')
end

M.toggle_file = function()
  vim.cmd('MatlabToggleFile')
end

M.start_server = function()
  vim.cmd('MatlabStartServer')
end

M.stop_server = function()
  vim.cmd('MatlabStopServer')
end

M.toggle_window = function()
  vim.cmd('MatlabToggleWindow')
end

return M
