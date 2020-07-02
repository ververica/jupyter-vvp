# 3 - Code Completion

## Context
VVP offers code completion for SQL scripts. As Jupyter Notebooks also provide code completion it would be expected by
 users to also have code completion for the flink_sql magic. 

## Decision
There are two functions that allow to hook into the code completion mechanism of the interactive shell, 
`set_hook('complete_command', completer, '<regex_to_match>'` and `set_custom_completer(completer)`.
Both do not work work us, because we need the content of the complete cell.
Another way to hook into the code completion mechanism is to create a new kernel, e.g. extending IPyKernel,
and overriding the `do_complete` function.

## Consequences
Code completion will only work if the Flink SQL kernel is used, users can use the magics with the standard Python 
kernel, but will not get auto-complete.  