# Usage

```{raw} html
---
---

<style>
	h4 {text-transform: lowercase;}
</style>
```

## `wa`

```{autosimple} wa_cli.wa.init
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
nosubcommands:
nodescription:
---
```

## Sub-commands

Subcommands immediately succeed the `wa` command. They implement additional logic. Having subcommands rather than arguments directly to `wa` increases expandability as it will allow for additional features to be implemented without convoluting the help menu of the base `wa` command.

### `script`

```{autosimple} wa_cli.script.init
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: script
nosubcommands:
nodescription:
---
```

#### `script license`

```{autosimple} wa_cli.script.run_license
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: script license
nosubcommands:
nodescription:
---
```

### `sim`

```{autosimple} wa_cli.sim.init
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: sim
nosubcommands:
nodescription:
---
```

#### `sim run`

```{autosimple} wa_cli.sim.run_run
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: sim run
nosubcommands:
nodescription:
---
```
