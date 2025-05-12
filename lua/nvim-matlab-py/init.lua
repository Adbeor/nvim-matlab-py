-- nvim-matlab-py Lua API

local M = {}

-- Configura el plugin
M.setup = function(opts)
  opts = opts or {}
  
  -- Configurar la ruta ejecutable de MATLAB
  if opts.matlab_executable then
    vim.g.matlab_executable = opts.matlab_executable
  end
  
  -- Configurar el puerto del servidor
  if opts.server_port then
    vim.g.matlab_server_port = opts.server_port
  end
  
  -- Configurar mapeos de teclas
  if opts.setup_keymaps == true then
    vim.keymap.set('n', '<leader>rr', ':MatlabRun<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '<leader>rc', ':MatlabRunCell<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '<leader>rl', ':MatlabRunLine<CR>', { noremap = true, silent = true })
    vim.keymap.set('v', '<leader>rs', ':MatlabRunSelection<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '<leader>mt', ':MatlabToggleFile<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '<leader>ms', ':MatlabStopServer<CR>', { noremap = true, silent = true })
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

M.stop_server = function()
  vim.cmd('MatlabStopServer')
end

return M
