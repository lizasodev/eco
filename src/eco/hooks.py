BASH = r'''
# --- eco: registro de comandos (bash) ---
__eco_last=""
__eco_prompt() {
    local code=$? cmd
    cmd=$(HISTTIMEFORMAT= history 1 | sed 's/^ *[0-9]* *//')
    if [ -n "$cmd" ] && [ "$cmd" != "$__eco_last" ]; then
        __eco_last="$cmd"
        ( eco record cmd --cwd "$PWD" --exit "$code" -- "$cmd" >/dev/null 2>&1 & )
    fi
    return $code
}
case ";$PROMPT_COMMAND;" in *";__eco_prompt;"*) ;; *) PROMPT_COMMAND="__eco_prompt${PROMPT_COMMAND:+;$PROMPT_COMMAND}";; esac
'''

ZSH = r'''
# --- eco: registro de comandos (zsh) ---
__eco_preexec() { __eco_cmd="$1"; }
__eco_precmd() {
    local code=$?
    [ -n "$__eco_cmd" ] && ( eco record cmd --cwd "$PWD" --exit "$code" -- "$__eco_cmd" >/dev/null 2>&1 & )
    __eco_cmd=""
}
autoload -Uz add-zsh-hook
add-zsh-hook preexec __eco_preexec
add-zsh-hook precmd __eco_precmd
'''
