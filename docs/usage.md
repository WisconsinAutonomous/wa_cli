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

### `docker`

```{autosimple} wa_cli.docker_cli.init
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: docker
nosubcommands:
nodescription:
---
```

#### `docker run`

```{autosimple} wa_cli.docker_cli.run_run
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: docker run
nosubcommands:
nodescription:
---
```

#### `docker stack`

```{autosimple} wa_cli.docker_cli.run_stack
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: docker stack
nosubcommands:
nodescription:
---
```

#### `docker vnc`

```{autosimple} wa_cli.docker_cli.run_vnc
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: docker vnc
nosubcommands:
nodescription:
---
```

#### `docker network`

```{autosimple} wa_cli.docker_cli.run_network
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: docker network
nosubcommands:
nodescription:
---
```

### `wiki`

```{autosimple} wa_cli.wiki.init
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: wiki
nosubcommands:
nodescription:
---
```

#### `wiki post`

```{autosimple} wa_cli.wiki.run_post
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: wiki post
nosubcommands:
nodescription:
---
```

#### `wiki dev`

```{autosimple} wa_cli.wiki.run_dev
```

```{argparse}
---
module: wa_cli.wa
func: init
prog: wa
path: wiki dev
nosubcommands:
nodescription:
---
```
