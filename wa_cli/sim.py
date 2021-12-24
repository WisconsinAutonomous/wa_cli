# Imports from wa_cli
from wa_cli.utils.logger import LOGGER
from wa_cli.utils.json import load_json, check_field
from wa_cli.utils.files import file_exists, get_resolved_path
from wa_cli.utils.dependencies import check_for_dependency

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



def run_run(args):
    """The run command will spin up a Docker container that runs a python script with the desired image.

    The use case for the run command is when we'd like to run a `wa_simulator` script with a certain
    operating system configuration or in a way that's distributable across computers. Everyone's setup is different,
    i.e. OS, development environment, packages installed. Using Docker, you can simply run `wa sim run...`
    and run `wa_simulator` agnostic from your local system.

    The run command requires one argument: a python script to run in the container.
    The python script is the actual file we'll run from within the
    container. After the python script, you may add arguments that will get passed to the script
    when it's run in the container.

    Optionally, you may provide a JSON configuration file. The JSON file defines various settings we'll
    use when spinning up the container. If a JSON configuration file is not provided, you must pass these options
    via the command line. There are many default values, so not all configurations are necessarily needed through
    the command line.

    JSON Settings:

    - `Container Name` (str, optional): Identifies the name that should be used for the container. If no name is passed, JSON will provide one. Defaults to "wasim-docker".

    - `Image` (str, optional): The image the container will use. If the image has not been downloaded, it will be fetched at runtime. Defaults to "wiscauto/wa_simulator:latest".

    - `Data` (list, optional): The folder that has all of the data files that will be used in the simulation. If you're familiar with docker, these will become [volumes](https://docs.docker.com/storage/volumes/). By default, no volumes will be created if `Data` is left empty. Each entry in the `Data` list will be made a `volumes` and may have the following attributes:

        - `Host Path` (str, required): The path to the local folder that will be copied to the container. If `Host Path Is Relative To JSON` is not set to True (see below), it will be assumed as a global path

        - `Host Path Is Relative To JSON` (bool, optional): If set to True, the `Host Path` entry will be evaluated as if it were relative to the location of the JSON file provided. Defaults to False.

        - `Container Path` (str, optional): The path in the container to link the host path to. Defaults to `/root/<file/folder name>`.

    - `Port` (str, optional): The port to expose between the docker container and the host machine. This is the port that the server and client may communicate over. Ensure this is consistent with both your server and client code, as this will be the only port exposed. Default is 5555.

    - `Network` (dict, optional): The network that the container should use for communication. See Docker [networks](https://docs.docker.com/network). The `Network` dict must include a `Name`, representing the name of the network, and optionally an `IPv4` field, representing the static ip to assign to the container. If no `IPv4` field is provided, a default value of 172.20.0.3 will be used. Further, if a network must be created because `Name` hasn't been created, the submask will be generated from `IPv4`.

    Example JSON file:

    ```json
    {
        "Name": "Demo bridge",
        "Type": "Bridge",

        "Container Name": "wasim-docker",
        "Image": "wiscauto/wa_simulator:latest",
        "Data": [
            {
                "Path": "../data",
                "Path Is Relative To JSON": true
            }
        ],
        "Network": {
            "Name": "wa",
            "IPv4": "172.30.0.3"
        }
    }
    ```

    Example cli commands:

    ```bash
    # ---------
    # With JSON
    # ---------

    # Run from within wa_simulator/demos/bridge
    wa sim run --json demo_bridge.json demo_bridge_server.py

    # With more verbosity
    wa -vv sim run --json demo_bridge.json demo_bridge_server.py

    # With some script arguments
    wa -vv sim run --json demo_bridge.json demo_bridge_server.py --step_size 2e-3

    # ------------
    # Without JSON
    # ------------

    # Run from within wa_simulator/demos/bridge
    # Running wa_simulator/demos/bridge/demo_bridge_server.py using command line arguments rather than json
    # This should be used to communicate with a client running on the host
    wa sim run \\
            --name wasim-docker \\
            --image wiscauto/wa_simulator \\
            --data "../data:/root/data" \\
            --data "/usr/local:/usr/local" \\ # Each entry serves as a new volume
            --port "5555:5555" \\
            demo_bridge_server.py --step_size 2e-3

    # Running wa_simulator/demos/bridge/demo_bridge_server.py using command line arguments rather than json
    # This should be used to communicate with another client in a container
    wa sim run \\
            --name wasim-docker \\
            --image wiscauto/wa_simulator \\
            --data "../data:/root/data" \\
            --data "/usr/local:/usr/local" \\ # Each entry serves as a new volume
            --network "wa" \\
            demo_bridge_server.py --step_size 2e-3

    # Same thing as above, but leverages defaults
    wa -vv sim run demo_bridge_server.py --step_size 2e-3
    ```
    """
    LOGGER.debug("Running 'sim run' entrypoint...")

    # Don't want to have install everything when wa_cli is installed
    # So check dependencies here
    LOGGER.info("Checking dependencies...")
    check_for_dependency('docker', install_method='pip install docker-py')
    
    global docker
    import docker
    from docker.utils import convert_volume_binds
    from docker.utils.ports import build_port_bindings

    # Grab the args to run
    script = args.script
    script_args = args.script_args

    # Grab the file path
    absfile = get_resolved_path(script, return_as_str=False)
    file_exists(absfile, throw_error=True)
    filename = absfile.name

    # Create the command
    cmd = f"python {filename} {' '.join(script_args)}"

    # First, populate a config dictionary with the command line arguments
    # Since we do this first, all of the defaults will be entered into the config dict
    # Then, if a json overrides the default, it can just override the dict
    # Further, if a command line argument is provided, it will just be added to the dict here
    # instead of the default
    config: dict = {}

    # Image
    config["name"] = args.name
    config["image"] = args.image

    # Data folders
    config["volumes"] = []
    config["volumes"].append(f"{absfile}:/root/{filename}")  # The actual python file # noqa
    config["volumes"].extend(convert_volume_binds(args.data))

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

    # Now, parse the json if one is provided
    if args.json is not None:
        j = load_json(args.json)

        # Validate the json file
        check_field(j, "Type", value="Bridge")
        check_field(j, "Container Name", field_type=str, optional=True)
        check_field(j, "Image", field_type=str, optional=True)
        check_field(j, "Data", field_type=list, optional=True)
        check_field(j, "Port", field_type=str, optional=True)
        check_field(j, "Network", field_type=dict, optional=True)

        # Parse the json file
        config["name"] = j.get("Container Name", args.name)
        config["image"] = j.get("Image", args.image)

        if "Data" in j:
            for data in j["Data"]:
                # Validate the data
                check_field(data, "Host Path", field_type=str)
                check_field(data, "Host Path Is Relative To JSON",
                             field_type=bool, optional=True)
                check_field(data, "Container Path",
                             field_type=bool, optional=True)

                # Create the volume string
                host = data["Host Path"]
                relative_to_json = data.get("Host Path", False)
                container = data.get("Container Path",
                                     f"/root/{pathlib.PurePath(host).name}")

                if relative_to_json:
                    host = str((pathlib.Path(args.json).parent / pathlib.Path(host)).resolve()) # noqa
                else:
                    host = get_resolved_path(host)

                config["volumes"].append(f"{host}:{container}")

        if "Port" in j:
            port = j["Port"]
            config["ports"] = build_port_bindings([f"{port}:{port}"])

        if "Network" in j:
            n = j["Network"]

            # Validate the network
            check_field(n, "Name", field_type=str)
            check_field(n, "IP", field_type=str, optional=True)

            config["network"] = n["Name"]
            config["ip"] = n.get("IP", args.ip)

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
                    config["image"], "/bin/bash", volumes=config["volumes"], ports=config["ports"], remove=True, detach=True, tty=True, name=config["name"], auto_remove=True)
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
    LOGGER.debug("Running 'sim novnc' entrypoint...")

    # Don't want to have install everything when wa_cli is installed
    # So check dependencies here
    LOGGER.info("Checking dependencies...")
    check_for_dependency('docker', install_method='pip install docker-py')
    
    global docker
    import docker
    from docker.utils.ports import build_port_bindings

    # General config
    image = "theasp/novnc:latest"
    name = args.name

    # Ports
    ports = build_port_bindings(["8080:8080"])

    # Networks
    network = args.network
    ip = args.ip

    # Environment variables
    environment = [
        "DISPLAY_WIDTH=5000",
        "DISPLAY_HEIGHT=5000",
        "RUN_XTERM=no",
        "RUN_FLUXBOX=yes",
    ]

    # Start up the container
    if not args.dry_run:
        # Get the client
        client = docker.from_env()

        # Initialize the image
        _init_image(client, image)

        # Initialize the network
        _init_network(client, network, ip)

        # Run the container
        container = client.containers.run(image, ports=ports, remove=True, detach=True, name=name, auto_remove=True, environment=environment)
        _connect_to_network(client, container, network, ip)

def init(subparser):
    """Initializer method for the `sim` entrypoint.

    The entrypoint serves as a mechanism for running containers with `wa_simulator`. It may be
    desireable to have a containerized system for running `wa_simulator`; for instance, if a script
    requiries a certain package, the Docker image could be shipped without needing to install the package
    on a system locally. The scalability of using Docker over installing packages on a system is much greater.

    To see specific commands that are available, run the following command:

    .. highlight:: bash
    .. code-block:: bash

        wa sim -h

    Current subcommands:

        - `run`: Spins up a container and runs a python script in the created container.

        - `novnc`: Starts up a novnc container so gui windows can be visualized.
    """
    LOGGER.debug("Running 'sim' entrypoint...")

    # Ensure wa_simulator is installed
    check_for_dependency('wa_simulator', install_method='pip install wa_simulator')

    # Create some entrypoints for additional commands
    subparsers = subparser.add_subparsers(required=False)

    # Subcommand that runs a script in a docker container
    run = subparsers.add_parser("run", description="Run wa_simulator script in a Docker container")
    run.add_argument("--json", type=str, help="JSON file with docker configuration", default=None)
    run.add_argument("--name", type=str, help="Name of the container.", default="wasim-docker")
    run.add_argument("--image", type=str, help="Name of the image to run.", default="wiscauto/wa_simulator:latest")
    run.add_argument("--data", type=str, action="append", help="Data to pass to the container as a Docker volume. Multiple data entries can be provided.", default=[])
    run.add_argument("--port", type=str, action="append", help="Ports to expose from the container.", default=[])
    run.add_argument("--env", type=str, action="append", dest="environment", help="Environment variables.", default=[])
    run.add_argument("--network", type=str, help="The network to communicate with.", default="")
    run.add_argument("--ip", type=str, help="The static ip address to use when connecting to 'network'. Used as the server ip.", default="172.20.0.3")
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
