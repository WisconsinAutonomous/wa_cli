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
    if args.wasim or args.wasim_without_novnc:
        LOGGER.info("Updating args with 'wasim' defaults...")
        def up(arg, val, dval=None):
            return val if arg == dval else arg
        args.name = up(args.name, "wasim-docker")
        args.image = up(args.image, "wiscauto/wa_simulator:latest")
        args.port.insert(0, "5555:5555")
        if not args.wasim_without_novnc:
            args.environment.insert(0, "DISPLAY=novnc:0.0")
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
        try:
            print(docker.run(**config, command=cmd.split(" "), remove=True, tty=True))
        except docker_exceptions.DockerException as e:
            pass

def run_stack(args):
    """Command that essentially wraps `docker-compose` and can help spin up, attach, destroy, and build docker-compose based containers.

    This command is completely redudant; it simply will intelligently decide whether to build, spin up, attach or destroy a container. The usage here is for Wisconsin Autonomous members to quickly start and attach to control stack docker containers that are based on the typical docker-compose file that we use.

    To get started, go into whatever repo we'll call it REPO you're attempting to use and run the following command:

    ```bash
    wa docker stack repo-dev
    ```

    The first time this is run, if `repo-dev` isn't found, it will build it or pull it. 
    Then, it will spin up the container and attach to it (unless detach is passed).

    If desired, pass `--down` to stop the container. Further, if the container exists and changes are
    made to the repository, the container will _not_ be built automatically. To do that, add the 
    `--build` argument.
    """
    LOGGER.info("Running 'docker stack' entrypoint...")

    # Check docker-compose is installed
    assert docker.compose.is_installed()

    # Generate the config
    config = {}
    config["services"] = [args.name]
    config["build"] = args.build

    # Complete the arguments
    LOGGER.debug(f"Running docker container with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        if args.down:
            LOGGER.info(f"Tearing down {args.name}")
            docker.compose.down()
        else:
            LOGGER.info(f"Spinning up {args.name}")
            docker.compose.up(**config, detach=True)
            if not args.detach:
                usershell = [e for e in docker.container.inspect(args.name).config.env if "USERSHELL" in e][0]
                shellcmd = usershell.split("=")[-1]
                print(docker.execute(args.name, [shellcmd], interactive=True, tty=True))

def run_novnc(args):
    """Command to spin up a `novnc` docker container to allow the visualization of GUI apps in docker

    [noVNC](https://novnc.com/info.html) is a tool for using [VNC](https://en.wikipedia.org/wiki/Virtual_Network_Computing) in a browser.
    [docker-novnc](https://github.com/theasp/docker-novnc) is a docker container that's been created that runs novnc and can be used
    to visualize gui applications for other docker containers. There are a few requirements to ensure gui apps are correctly visualized, as seen below:

    - `network`: Docker networks are used to help containers communicate with other containers or with the host. When spinning up a container that you want to 
    visualize a gui app with novnc, you will need to make sure it is connected to the same network as the novnc container, i.e. make sure the original container is 
    connected to the same network that you passed to `--network` (or the default `wa` network).
    - `port`: The novnc instance can be visualized in your browser at [http://localhost:8080/vnc_auto.html](http://localhost:8080/vnc_auto.html). As seen in the url,
    the application is hosted on port 8080. This port must then be exposed from the container to the host. This is again done by the `wa docker novnc` command.
    - `DISPLAY`: The [DISPLAY](https://askubuntu.com/questions/432255/what-is-the-display-environment-variable) environment variable is used to help display
    applications in X window systems (used by any linux based container, like the ones we use). To make sure the gui apps are visualized in novnc when the aforementioned
    requirements are setup, you need to make sure the `DISPLAY` variable is set correctly. The variable should be set to `novnc:0.0` (assuming the novnc container that has
    been setup is named 'novnc').
    """
    LOGGER.info("Running 'docker novnc' entrypoint...")

    # Set the defaults
    def up(arg, val, dval=None):
        return val if arg == dval else arg
    args.image = "theasp/novnc:latest"
    args.name = up(args.name, "novnc")
    args.port = ["8080:8080"]
    args.network = up(args.network, "wa")
    args.ip = up(args.ip, "172.20.0.4")
    args.environment =[
        "DISPLAY_WIDTH=5000",
        "DISPLAY_HEIGHT=5000",
        "RUN_XTERM=no",
        "RUN_FLUXBOX=yes",
    ]
    args.data = []

    # Parse the arguments
    config = _parse_args(args)

    # Start up the container
    LOGGER.debug(f"Running docker container with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        print(docker.run(**config, detach=True, remove=True))

def run_network(args):
    """Command to start a docker network for use with WA applications

    To create complicated docker systems, [networks](https://docs.docker.com/network/) are a common mechanism. They
    allow multiple docker containers to be used together, where each implements its own features and is isolated,
    outside of its communication between each other. Example use cases are one container for `wa_simulator`, 
    one for `novnc` for visualizing gui apps, and one for `ros` to run control logic, where each communicator is
    on the same network and allows for each container to send data between each other.

    This command will initialize a container with defaults that are typical for WA applications.
    """
    LOGGER.info("Running 'docker network' entrypoint...")

    # Parse the args
    config = {}
    config["name"] = args.name
    config["driver"] = "bridge"

    # Determine the subnet from the ip
    import ipaddress
    ip_network = ipaddress.ip_network(f"{args.ip}/255.255.255.0", strict=False)
    config["subnet"] = str(list(ip_network.subnets())[0])

    LOGGER.debug(f"Creating docker network with the following arguments: {dumps_dict(config)}")
    if not args.dry_run:
        print(docker.network.create(driver="bridge", subnet=subnet, name=name))

def init(subparser):
    """Initializer method for the `docker` entrypoint.

    The entrypoint serves as a mechanism for running containers with `docker`. A common
    desireable usecase for simulations is to have it run in a containerized system; for instance, if a script
    requiries a certain package, the Docker image could be shipped without needing to install the package
    on a system locally. The scalability of using Docker over installing packages on a system is much greater.

    There are a few ports that may be exposed, and the _typical_ purpose of each port (for wa) is outlined below:
    - `8080`: `novnc` port to display gui apps in a browser.
    - `8888`: `rosboard` visualizer. See [their github](https://github.com/dheera/rosboard). This is used for visualizing ROS data
    - `5555`: Used by `wa_simulator` to communicate data over a bridge or to another external entity

    There are also a few ip addresses we use and how they are used is seen below:
    - `172.20.0.2`: Reserved for the control stack
    - `172.20.0.3`: Reserved for the simulation
    - `172.20.0.4`: Reserved for novnc

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

    group = run.add_mutually_exclusive_group()
    group.add_argument("--wasim", action="store_true", help="Run the passed script with all the defaults for the wa_simulator. Will set 'DISPLAY' to use novnc.")
    group.add_argument("--wasim-without-novnc", action="store_true", help="Run the passed script with all the defaults for the wa_simulator. Will not use novnc.")

    run.add_argument("script", help="The script to run up in the Docker container")
    run.add_argument("script_args", nargs=argparse.REMAINDER, help="The arguments for the [script]")
    run.set_defaults(cmd=run_run)

    # Subcommand that builds, spins up, attaches or shuts down docker container for our control stacks
    stack = subparsers.add_parser("stack", description="Command to simplify usage of docker-based development of control stacks. Basically wraps docker-compose.")
    stack.add_argument("-d", "--detach", action="store_true", help="Detach from the container.", default=False)
    stack.add_argument("--down", action="store_true", help="Tear down the container.", default=False)
    stack.add_argument("--build", action="store_true", help="Build the container.", default=False)
    stack.add_argument("name", type=str, help="Name of the container.")
    stack.set_defaults(cmd=run_stack)

    # Subcommand that spins up the novnc container
    novnc = subparsers.add_parser("novnc", description="Starts up a novnc container to be able to visualize stuff in a browser")
    novnc.add_argument("--name", type=str, help="Name of the container.", default="novnc")
    novnc.add_argument("--network", type=str, help="The network to communicate with.", default="wa")
    novnc.add_argument("--ip", type=str, help="The static ip address to use when connecting to 'network'.", default="172.20.0.4")
    novnc.set_defaults(cmd=run_novnc)

    network = subparsers.add_parser("network", description="Initializes a network to be used for WA docker applications.")
    network.add_argument("--name", type=str, help="Name of the network to create.", default="wa")
    network.add_argument("--ip", type=str, help="The ip address to use when creating the network. All containers connected to it must be in the subnet 255.255.255.0 of this value.", default="172.20.0.0")
    network.set_defaults(cmd=run_network)

    return subparser
