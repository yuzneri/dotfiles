" ============================================================
" 基本設定
" ============================================================
set encoding=utf-8
scriptencoding utf-8
set fileencodings=utf-8,cp932,euc-jp,sjis
set fileformats=unix,dos,mac
syntax enable                   " シンタックスハイライト
filetype plugin indent on       " ファイルタイプ別プラグイン/インデント

" ============================================================
" スペルチェック
" ============================================================
" cjk: 日本語などCJK文字を誤検出しない
set spelllang=en,cjk

" ============================================================
" 表示
" ============================================================
set number              " 行番号
set cursorline          " カーソル行をハイライト
set showmatch           " 対応する括弧を強調
set matchtime=1
set ruler
set showcmd
set laststatus=2        " ステータスラインを常時表示
set wildmenu            " コマンド補完
set wildmode=longest:full,full
set list                " 不可視文字表示
set listchars=tab:»·,trail:·,nbsp:␣,extends:»,precedes:«
set signcolumn=yes
set termguicolors

" ============================================================
" インデント
" ============================================================
set autoindent
set smartindent
set expandtab           " タブをスペースに展開
set tabstop=4
set shiftwidth=4
set softtabstop=4
set shiftround

" ============================================================
" 検索
" ============================================================
set hlsearch
set incsearch
set ignorecase
set smartcase           " 大文字を含む場合は区別
set wrapscan

" ============================================================
" 編集
" ============================================================
set backspace=indent,eol,start
set clipboard=unnamedplus   " システムクリップボード連携
set hidden                  " 未保存でもバッファ切替可
set autoread                " 外部変更を自動で読み込む
set mouse=a
set whichwrap=b,s,h,l,<,>,[,]
set virtualedit=block
set scrolloff=5             " 上下5行は常に見える
set sidescrolloff=8

" ============================================================
" ウィンドウ・分割
" ============================================================
set splitright
set splitbelow

" ============================================================
" バックアップ・スワップ
" ============================================================
set noswapfile
set nobackup
set nowritebackup
set undofile
set undodir=~/.local/state/nvim/undo
if !isdirectory(expand('~/.local/state/nvim/undo'))
  call mkdir(expand('~/.local/state/nvim/undo'), 'p')
endif

" ============================================================
" その他
" ============================================================
set updatetime=300
set timeoutlen=500
set history=1000
set belloff=all

" ============================================================
" キーマップ
" ============================================================
let mapleader = "\<Space>"

" ハイライト解除
nnoremap <silent> <Esc><Esc> :nohlsearch<CR>

" 表示行で移動
nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up> gk

" ウィンドウ移動
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" バッファ移動
nnoremap <silent> [b :bprevious<CR>
nnoremap <silent> ]b :bnext<CR>

" 保存・終了
nnoremap <Leader>w :w<CR>
nnoremap <Leader>q :q<CR>

" ============================================================
" オートコマンド
" ============================================================
augroup vimrc_autocmd
  autocmd!
  " カーソル位置を復元
  autocmd BufReadPost *
    \ if line("'\"") > 1 && line("'\"") <= line("$") |
    \   execute "normal! g`\"" |
    \ endif
  " yank時にハイライト
  autocmd TextYankPost * silent! lua vim.highlight.on_yank({timeout=200})

  " ファイルタイプ別インデント（2スペース系）
  autocmd FileType yaml,yml,json,jsonc,html,css,scss,sass,javascript,javascriptreact,typescript,typescriptreact,vue,svelte,ruby,lua,nix,toml,sh,zsh,bash
    \ setlocal shiftwidth=2 tabstop=2 softtabstop=2
  " Markdown: 2スペース、conceal無効、行末スペース保持（強制改行のため）
  autocmd FileType markdown setlocal shiftwidth=2 tabstop=2 softtabstop=2 conceallevel=0
  autocmd FileType markdown let b:keep_trailing_whitespace = 1
  " Go: タブ + 展開しない
  autocmd FileType go setlocal noexpandtab shiftwidth=4 tabstop=4 softtabstop=4
  " Makefile: タブ必須
  autocmd FileType make setlocal noexpandtab

  " テキスト系ファイルでスペルチェック有効
  autocmd FileType markdown,gitcommit,text,tex setlocal spell

  " 末尾空白を保存時に削除（b:keep_trailing_whitespace が立っているバッファは除外）
  autocmd BufWritePre * if !get(b:, 'keep_trailing_whitespace', 0) | %s/\s\+$//e | endif
augroup END
