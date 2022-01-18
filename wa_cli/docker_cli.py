# Imports from wa_cli
from wa_cli.utils.logger import LOGGER, dumps_dict
from wa_cli.utils.files import file_exists, get_resolved_path
from wa_cli.utils.dependencies import check_for_dependency

# Docker imports
from python_on_whales import docker, exceptions as docker_exceptions

# General imports
import argparse
import pathlib

def _parse_args(args):
    # First, populate a config dictionary with the command line arguments
    # Since we do this first, all of the defaults will be entered into the config dict
    # Further, if a command line argument is provided, it will just be added to the dict here
    # instead of the default
    config: dict = {}

    # Image
    config["name"] = args.name
    config["image"] = args.image

    # Data folders
    config["volumes"] = []
    # If the path doesn't have a ':', make the container dir at /root/<dir>
    # Also, resolve the paths to be absolute
    for data in args.data:
        split_data = data.split(':')
        hostfile = get_resolved_path(split_data[0], return_as_str=False)
        containerfile = split_data[1] if len(split_data) == 2 else f"/root/{hostfile.name}"
        vol = (str(hostfile), containerfile)
        config["volumes"].append(vol)

    # Ports
    config["publish"] = []
    for port in args.port:
        port = port if ":" in port else f"{port}:{port}"
        config["publish"].append(port.split(":"))

    # Networks
    config["networks"] = [args.network]
    config["ip"] = args.ip

    # Environment variables
    # Expects all variables to be in the following format: "<variable>=<value>"
    config["envs"] = {}
    for e in args.environment:
        variable, value = e.split("=")
        config["envs"][variable] = value

    return config

def _try_create_network(name, driver="bridge", ip="172.20.0.0", **kwargs):
    if len(docker.network.list({"name": name})) == 0:
        # If the network doesn't exist, create it

        # Determine the subnet from the ip
        import ipaddress
        ip_network = ipaddress.ip_network(f"{ip}/255.255.255.0", strict=False)
        subnet = str(list(ip_network.subnets())[0])

        return docker.network.create(name=name, driver=driver, subnet=subnet, **kwargs)
    return f"Network with name '{name}' has already been created."

def _does_container_exist(name):
    return len(docker.container.list(filters={"name": name})) != 0

def _try_create_default_vnc(parse_args, log=False):
    from types import SimpleNamespace
    args = SimpleNamespace()
    args.dry_run = parse_args.dry_run
    args.name = "vnc"
    args.network = "wa"
    args.ip = "172.20.0.4"
    run_vnc(args, log_if_created=log)

def run_run(args, run_cmd="/bin/bash"):
    """The run command will spin up a Docker container that runs a python script with the desired image.

    The use case for the run command is when we'd like to run a simulation script with a certain
    operating system configuration or in a way that's distributable across computers. Everyone's setup is different,
    i.e. OS, development environment, packages installed. Using Docker, you can simply run `wa docker run...`
    and run any script agnostic from your local system.

    The run command requires one argument: a python script to run in the container.
    The python script is the actual file we'll run from within the
    container. After the python script, you may add arguments that will get passed to the script
    when it's run in the container.

    Example cli commands:

    ```bash
    # Run from within wa_simulator/demos/bridge
    # Running wa_simulator/demos/bridge/demo_bridge_server.py using command line arguments 
    # This should be used to communicate with a client running on the host
    wa docker run \\
            --name wasim-docker \\
            --image wiscauto/wa_simulator:latest \\
            --network "wa" \\
            --data "../data:/root/data" \\ # ':root/data' not really necessary
            --data "pid_controller.py" \\  # Will be resolved to an absolute path automatically
            --port "5555:5555" \\
            demo_bridge_server.py --step_size 2e-3

    # Or more simply, leveraging provided by 'wasim'
    wa docker run \\
            --wasim \\
            --data "../data:/root/data" \\ 
            --data "pid_controller.py" \\ 
            demo_bridge_server.py --step_size 2e-3

    # Leverage defaults, but using the develop image
    wa docker run \\
            --wasim \\
            --image wiscauto/wa_simulator:develop \\
            --data "../data:/root/data" \\ 
            --data "pid_controller.py" \\ 
            demo_bridge_server.py --step_size 2e-3
    ```
    """
    LOGGER.info("Running 'docker run' entrypoint...")
    
    # Grab the args to run
    script = args.script
    script_args = args.script_args

    # Grab the file path
    absfile = get_resolved_path(script, return_as_str=False)
    file_exists(absfile, throw_error=True)
    filename = absfile.name

    # Create the command
    cmd = f"python {filename} {' '.join(script_args)}"

    # If args.wasim is True, we will use some predefined values that's typical for wa_simulator runs
    if args.wasim:
        LOGGER.info("Updating args with 'wasim' defaults...")
        def up(arg, val, dval=None):
            return val if arg == dval else arg
        args.name = up(args.name, "wasim-docker")
        args.image = up(args.image, "wiscauto/wa_simulator:latest")
        args.port.insert(0, "5555:5555") # For bridge communication
        if not args.no_vnc:
            args.environment.insert(0, "DISPLAY=vnc:0.0")
        args.environment.insert(0, "WA_DATA_DIRECTORY=/root/data")
        args.network = up(args.network, "wa")
        args.ip = up(args.ip, "172.20.0.3")

        # Try to find the data folder
        if args.data is None:
            LOGGER.warn("A data folder was not provided. You may want to pass one...")

    config = _parse_args(args)
    config["volumes"].append((str(absfile),f"/root/{filename}"))  # The actual python file # noqa
    config["command"] = cmd.split(" ")

    # Run the script
    LOGGER.debug(f"Running docker container with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        _try_create_network(config["networks"])
        if not args.no_vnc:
            _try_create_default_vnc(args)
        try:
            print(docker.run(**config, remove=True, tty=True))
        except docker_exceptions.DockerException as e:
            pass

def run_stack(args):
    """Command that essentially wraps `docker-compose` and can help spin up, attach, destroy, and build docker-compose based containers.

    This command is completely redundant; it simply combines all the build, spin up, attach or destroy 
    logic in a single command. The usage here is for Wisconsin Autonomous members to quickly start 
    and attach to control stack docker containers that are based on the typical docker-compose file that we use.

    There are four possible commands that can be used using the `stack` subcommand: 
    `build`, `up`, `down`, and `attach`. For example, if you'd like to build the container, you'd run 
    the following command:

    ```bash
    wa docker stack --build
    ```

    If you'd like to build, start the container, then attach to it, run the following command:

    ```bash
    wa docker stack --build --up --attach
    # OR (shorthand)
    wa docker stack -b -u -a
    # OR
    wa docker stack -bua
    ```

    If no arguments are passed, this is equivalent to the following command:

    ```bash
    wa docker stack --up --attach
    ```

    If desired, pass `--down` to stop the container. Further, if the container exists and changes are
    made to the repository, the container will _not_ be built automatically. To do that, add the 
    `--build` argument.
    """
    LOGGER.info("Running 'docker stack' entrypoint...")

    # Check docker-compose is installed
    assert docker.compose.is_installed()

    # If no command is passed, start up the container and attach to it
    cmds = [args.build, args.up, args.down, args.attach] 
    if all(not c for c in cmds):
        args.up = True
        args.attach = True

    # Get the config
    try:
        config = docker.compose.config()
    except docker_exceptions.DockerException as e:
        if "no configuration file provided: not found" in str(e):
            LOGGER.fatal("No docker-compose.yml configuration was found. Make sure you are running this command in the correct repository.")
            return
        else:
            raise e

    # Determine the service name
    if args.name is None:
        assert len(config.services.keys()) == 1
        name = list(config.services.keys())[0]
    else:
        name = args.name
        if not name in config.services.keys():
            LOGGER.fatal(f"A service with name '{name}' not found in the docker-compose.yml configuration file. Check if the provided name is correct.")
            return

    # Complete the arguments
    if not args.dry_run:
        _try_create_network("wa")
        _try_create_default_vnc(args)

        if args.down:
            LOGGER.info(f"Tearing down {name}...")
            docker.compose.down()
        if args.build:
            LOGGER.info(f"Building {name}...")
            docker.compose.build()
        if args.up:
            LOGGER.info(f"Spinning up {name}...")
            docker.compose.up(detach=True)
        if args.attach:
            LOGGER.info(f"Attaching to {name}...")
            try:
                usershell = [e for e in docker.container.inspect(name).config.env if "USERSHELL" in e][0]
                shellcmd = usershell.split("=")[-1]
                shellcmd = [shellcmd, "-c", f"{shellcmd}; echo"]
                print(docker.execute(name, shellcmd, interactive=True, tty=True))
            except docker_exceptions.NoSuchContainer as e:
                LOGGER.fatal(f"{name} has not been started. Please run again with the 'up' command.")

def run_vnc(args, log_if_created=True):
    """Command to spin up a `vnc` docker container to allow the visualization of GUI apps in docker

    [noVNC](https://novnc.com/info.html) is a tool for using [VNC](https://en.wikipedia.org/wiki/Virtual_Network_Computing) in a browser.
    [docker-vnc](https://github.com/wisconsinautonomous/docker-vnc) is a docker container that's been created that runs vnc and can be used
    to visualize gui applications for other docker containers in a browser or via a vnc viewer. There are a few requirements to ensure gui apps are correctly visualized, as seen below:

    - `network`: Docker networks are used to help containers communicate with other containers or with the host. When spinning up a container that you want to 
    visualize a gui app with vnc, you will need to make sure it is connected to the same network as the vnc container, i.e. make sure the original container is 
    connected to the same network that you passed to `--network` (or the default `wa` network).
    - `port`: The novnc instance can be visualized in your browser at [http://localhost:8080/vnc_auto.html](http://localhost:8080/vnc_auto.html). As seen in the url,
    the application is hosted on port 8080. This port must then be exposed from the container to the host. This is again done by the `wa docker novnc` command. Furthermore, to visualzie the apps in a vnc viewer, 5900 also has to be exposed.
    - `DISPLAY`: The [DISPLAY](https://askubuntu.com/questions/432255/what-is-the-display-environment-variable) environment variable is used to help display
    applications in X window systems (used by any linux based container, like the ones we use). To make sure the gui apps are visualized in vnc when the aforementioned
    requirements are setup, you need to make sure the `DISPLAY` variable is set correctly. The variable should be set to `vnc:0.0` (assuming the vnc container that has
    been setup is named 'vnc').
    """
    LOGGER.info("Running 'docker vnc' entrypoint...")

    # Set the defaults
    def up(arg, val, dval=None):
        return val if arg == dval else arg
    args.image = "wiscauto/vnc:latest"
    args.name = up(args.name, "vnc")
    args.port = ["8080:8080", "5900:5900"]
    args.network = up(args.network, "wa")
    args.ip = up(args.ip, "172.20.0.4")
    args.environment = []
    args.data = []
    args.stop = args.stop if hasattr(args, 'stop') else False

    # Parse the arguments
    config = _parse_args(args)

    # Start up the container
    LOGGER.debug(f"Running docker container with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        # First check if the network has been created
        # If it hasn't, make it
        _try_create_network(args.network)
        if args.stop:
            if _does_container_exist(config["name"]):
                LOGGER.info(f"Stopping vnc container with name '{config['name']}'")
                docker.stop(config["name"])
            else:
                LOGGER.warn(f"A vnc container with name '{config['name']}' doesn't exist. Nothing to do.")
        elif _does_container_exist(config["name"]):
            if log_if_created:
                LOGGER.warn(f"A vnc container with name '{config['name']}' already exists. You can probably ignore this error.")
        else:
            LOGGER.info(f"Creating vnc container with name '{config['name']}")
            print(docker.run(**config, detach=True, remove=True))

def run_network(args):
    """Command to start a docker network for use with WA applications

    To create complicated docker systems, [networks](https://docs.docker.com/network/) are a common mechanism. They
    allow multiple docker containers to be used together, where each implements its own features and is isolated,
    outside of its communication between each other. Example use cases are one container for `wa_simulator`, 
    one for `vnc` for visualizing gui apps, and one for `ros` to run control logic, where each communicator is
    on the same network and allows for each container to send data between each other.

    This command will initialize a container with defaults that are typical for WA applications.
    """
    LOGGER.info("Running 'docker network' entrypoint...")

    # Parse the args
    config = {}
    config["name"] = args.name
    config["driver"] = "bridge"

    LOGGER.debug(f"Creating docker network with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        print(_try_create_network(**config))

def init(subparser):
    """Initializer method for the `docker` entrypoint.

    The entrypoint serves as a mechanism for running containers with `docker`. A common
    desireable usecase for simulations is to have it run in a containerized system; for instance, if a script
    requiries a certain package, the Docker image could be shipped without needing to install the package
    on a system locally. The scalability of using Docker over installing packages on a system is much greater.

    There are a few ports that may be exposed, and the _typical_ purpose of each port (for wa) is outlined below:
    - `8080`: `novnc` port to display gui apps in a browser.
    - `5900`: `vnc` port for displaying gui apps in a vnc viewer
    - `8888`: `rosboard` visualizer. See [their github](https://github.com/dheera/rosboard). This is used for visualizing ROS data
    - `5555`: Used by `wa_simulator` to communicate data over a bridge or to another external entity

    There are also a few ip addresses we use and how they are used is seen below:
    - `172.20.0.2`: Reserved for the control stack
    - `172.20.0.3`: Reserved for the simulation
    - `172.20.0.4`: Reserved for vnc

    To see specific commands that are available, run the following command:

    ```bash
    wa docker -h
    ```
    """
    LOGGER.debug("Initializing 'docker' entrypoint...")

    # Create some entrypoints for additional commands
    subparsers = subparser.add_subparsers(required=False)

    # Subcommand that runs a script in a docker container
    run = subparsers.add_parser("run", description="Run python script in a Docker container")
    run.add_argument("--name", type=str, help="Name of the container.", default=None)
    run.add_argument("--image", type=str, help="Name of the image to run.", default=None)
    run.add_argument("--data", type=str, action="append", help="Data to pass to the container as a Docker volume. Multiple data entries can be provided.", default=[])
    run.add_argument("--port", type=str, action="append", help="Ports to expose from the container.", default=[])
    run.add_argument("--env", type=str, action="append", dest="environment", help="Environment variables.", default=[])
    run.add_argument("--network", type=str, help="The network to communicate with.", default=None)
    run.add_argument("--ip", type=str, help="The static ip address to use when connecting to 'network'. Used as the server ip.", default=None)
    run.add_argument("--wasim", action="store_true", help="Run the passed script with all the defaults for the wa_simulator. Will set 'DISPLAY' to use vnc.")
    run.add_argument("--no-vnc", action="store_true", help="Don't implicitly create a vnc server. Not to be confused with noVNC.", default=False)
    run.add_argument("script", help="The script to run up in the Docker container")
    run.add_argument("script_args", nargs=argparse.REMAINDER, help="The arguments for the [script]")
    run.set_defaults(cmd=run_run)

    # Subcommand that builds, spins up, attaches or shuts down docker container for our control stacks
    stack = subparsers.add_parser("stack", description="Command to simplify usage of docker-based development of control stacks. Basically wraps docker-compose.")
    stack.add_argument("-n", "--name", type=str, help="Name of the container.")
    stack.add_argument("-b", "--build", action="store_true", help="Build the stack.", default=False)
    stack.add_argument("-u", "--up", action="store_true", help="Spin up the stack.", default=False)
    stack.add_argument("-d", "--down", action="store_true", help="Tear down the stack.", default=False)
    stack.add_argument("-a", "--attach", action="store_true", help="Attach to the stack.", default=False)
    stack.set_defaults(cmd=run_stack)

    # Subcommand that spins up the vnc container
    vnc = subparsers.add_parser("vnc", description="Starts up a vnc container to be able to visualize stuff in a browser")
    vnc.add_argument("--name", type=str, help="Name of the container.", default="vnc")
    vnc.add_argument("--network", type=str, help="The network to communicate with.", default="wa")
    vnc.add_argument("--ip", type=str, help="The static ip address to use when connecting to 'network'.", default="172.20.0.4")
    vnc.add_argument("--stop", action="store_true", help="Stop the vnc container.", default=False)
    vnc.set_defaults(cmd=run_vnc)

    # Subcommand that starts a docker network
    network = subparsers.add_parser("network", description="Initializes a network to be used for WA docker applications.")
    network.add_argument("--name", type=str, help="Name of the network to create.", default="wa")
    network.add_argument("--ip", type=str, help="The ip address to use when creating the network. All containers connected to it must be in the subnet 255.255.255.0 of this value.", default="172.20.0.0")
    network.set_defaults(cmd=run_network)

    return subparser
