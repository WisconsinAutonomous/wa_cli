#
# MIT License
#
# Copyright (c) 2018-2021 Wisconsin Autonomous
#
# See https://wa.wisc.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# Imports from wa_cli
from wa_cli.utils.logger import LOGGER
from wa_cli.utils.files import file_exists, get_resolved_path
from wa_cli.utils.dependencies import check_for_dependency

# Docker imports
import docker
from docker.utils import convert_volume_binds
from docker.utils.ports import build_port_bindings

# General imports
import argparse
import pathlib

def _init_network(client, network, ip):
    try:
        client.networks.get(network)
    except docker.errors.NotFound as e:
        LOGGER.warn(f"{network} has not been created yet. Creating it...")

        import ipaddress
        network = ipaddress.ip_network(f"{ip}/255.255.255.0", strict=False)
        subnet = str(list(network.subnets())[0])

        ipam_pool = docker.types.IPAMPool(subnet=subnet)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

        LOGGER.info(
            f"Creating network with name '{network}' with subnet '{subnet}'.")
        client.networks.create(name=network, driver="bridge", ipam=ipam_config)

def _connect_to_network(client, container, network, ip):
        client.networks.get(network).connect(container, ipv4_address=ip) # noqa

def _init_image(client, image):
    try:
        client.images.get(image)
    except docker.errors.APIError as e:
        LOGGER.warn(
            f"{image} was not found locally. Pulling from DockerHub. This may take a few minutes...")
        client.images.pull(image)
        LOGGER.warn(
            f"Finished pulling {image} from DockerHub. Running command...")


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
    vols = []
    for data in args.data:
        split_data = data.split(':')
        hostfile = get_resolved_path(split_data[0], return_as_str=False)
        containerfile = split_data[1] if len(split_data) == 2 else f"/root/{hostfile.name}"
        vol = f"{hostfile}:{containerfile}"
        vols.append(vol)
    config["volumes"].extend(convert_volume_binds(vols))

    # Ports
    config["ports"] = {}
    ports = []
    for port in args.port:
        port = port if ":" in port else f"{port}:{port}"
        ports.append(port)
    config["ports"] = build_port_bindings(ports)

    # Networks
    config["network"] = args.network
    config["ip"] = args.ip

    # Environment variables
    config["environment"] = args.environment

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
    LOGGER.debug("Running 'docker run' entrypoint...")

    # Don't want to have install everything when wa_cli is installed
    # So check dependencies here
    LOGGER.info("Checking dependencies...")
    check_for_dependency('docker', install_method='pip install docker-py')
    
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
        args.port = up(args.port, ["5555:5555"], [])
        args.environment = up(args.environment, ["DISPLAY=novnc:0.0"], [])
        args.network = up(args.network, "wa")
        args.ip = up(args.ip, "172.20.0.3")

        # Try to find the data folder
        if args.data is None:
            LOGGER.warn("A data folder was not provided. You may want to pass one...")

    config = _parse_args(args)
    config["volumes"].append(f"{absfile}:/root/{filename}")  # The actual python file # noqa

    # Run the script
    LOGGER.info(f"Running '{cmd}' with the following settings:")
    LOGGER.info(f"\tImage: {config['image']}")
    LOGGER.info(f"\tVolumes: {config['volumes']}")
    LOGGER.info(f"\tPorts: {config['ports']}")
    LOGGER.info(f"\tNetwork: {config['network']}")
    LOGGER.info(f"\tIP: {config['ip']}")
    LOGGER.info(f"\tEnvironments: {config['environment']}")
    if not args.dry_run:
        try:
            # Get the client
            client = docker.from_env()

            # setup the signal listener to listen for the interrupt signal (ctrl+c)
            import signal
            import sys

            def signal_handler(sig, frame):
                if running_container is not None:
                    LOGGER.info(f"Stopping container.")
                    running_container.kill()
                sys.exit(0)
            signal.signal(signal.SIGINT, signal_handler)

            # Check if image is found locally
            running_container = None
            _init_image(client, config["image"])

            # Check if network has been created
            if config["network"] != "":
                _init_network(client, config["network"], config["ip"])

            # Run the command
            running_container = client.containers.run(
                    config["image"], run_cmd, volumes=config["volumes"], ports=config["ports"], remove=True, detach=True, tty=True, name=config["name"], auto_remove=True)
            if config["network"] != "":
                _connect_to_network(client, running_container, config["network"], config["ip"])
            result = running_container.exec_run(cmd, environment=config["environment"])
            print(result.output.decode())
            running_container.kill()
        except Exception as e:
            if running_container is not None:
                running_container.kill()

            raise e

def run_novnc(args):
    LOGGER.debug("Running 'docker novnc' entrypoint...")

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
    if not args.dry_run:
        # Get the client
        client = docker.from_env()

        # Initialize the image
        _init_image(client, config["image"])

        # Initialize the network
        _init_network(client, config["network"], config["ip"])

        # Run the container
        container = client.containers.run(config["image"], ports=config["ports"], remove=True, detach=True, name=config["name"], auto_remove=True, environment=config["environment"])
        _connect_to_network(client, container, config["network"], config["ip"])


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

    To see specific commands that are available, run the following command:

    .. highlight:: bash
    .. code-block:: bash

        wa docker -h

    Current subcommands:
    - `run`: Spins up a container and runs a python script in the created container.
    - `novnc`: Starts up a novnc container so gui windows can be visualized.
    """
    LOGGER.debug("Running 'docker' entrypoint...")

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
    run.add_argument("--wasim", action="store_true", help="Run the passed script with all the defaults for the wa_simulator")
    run.add_argument("script", help="The script to run up in the Docker container")
    run.add_argument("script_args", nargs=argparse.REMAINDER, help="The arguments for the [script]")
    run.set_defaults(cmd=run_run)

    # Subcommand that spins up the novnc container
    novnc = subparsers.add_parser("novnc", description="Starts up a novnc container to be able to visualize stuff in a browser")
    novnc.add_argument("--name", type=str, help="Name of the container.", default="novnc")
    novnc.add_argument("--network", type=str, help="The network to communicate with.", default="wa")
    novnc.add_argument("--ip", type=str, help="The static ip address to use when connecting to 'network'.", default="172.20.0.4")
    novnc.set_defaults(cmd=run_novnc)

    return subparser
