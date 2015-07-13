from fabric.api import env, prompt, execute, sudo, run, put, append
from fabric.contrib import files
import boto.ec2
import time
import pprint


env.aws_region = 'us-west-2'
env.key_filename = '~/.ssh/KeepHair.pem'
git_user = 'tlake'
projname = 'learning-journal'
git_path = git_user + '/' + projname
appname = 'journal.py'


def get_ec2_connection():
    if 'ec2' not in env:
            conn = boto.ec2.connect_to_region(env.aws_region)
            if conn is not None:
                env.ec2 = conn
                print "Connected to EC2 region %s" % env.aws_region
            else:
                msg = "Unable to connect to EC2 region %s"
                raise IOError(msg % env.aws_region)
    return env.ec2


def provision_instance(wait_for_running=True, timeout=60, interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    conn = get_ec2_connection()
    instance_type = 't2.micro'
    key_name = 'Keep Hair'
    security_group = 'ssh-access'
    # tutorial uses 'ami-d0d8b8e0'
    image_id = 'ami-5189a661'

    reservations = conn.run_instances(
        image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group, ]
    )
    new_instances = [
        i for i in reservations.instances if i.state == u'pending'
    ]

    running_instance = []
    if wait_for_running:
        waited = 0
        while new_instances and (waited < timeout_val):
            time.sleep(wait_val)
            waited += int(wait_val)
            for instance in new_instances:
                instance.update()
                state = instance.state
                print "Instance %s is %s" % (instance.id, state)
                if state == 'running':
                    running_instance.append(
                        new_instances.pop(new_instances.index(i))
                    )


def list_aws_instances(verbose=True, state='all'):
    conn = get_ec2_connection()

    reservations = conn.get_all_reservations()
    instances = []
    for res in reservations:
        for inst in res.instances:
            if state == 'all' or inst.state == state:
                try:
                    inst_name = inst.tags['Name']
                except KeyError:
                    inst_name = "None"
                inst = {
                    'name': inst_name,
                    'id': inst.id,
                    'type': inst.instance_type,
                    'image': inst.image_id,
                    'state': inst.state,
                    'instance': inst,
                }
                instances.append(inst)
    env.instances = instances
    if verbose:
        pprint.pprint(env.instances)


def select_instance(state='running'):
    if env.get('active_instance', False):
        return

    list_aws_instances(state=state)

    prompt_text = "Please select from the following instances:\n"
    instance_template = " %(ct)d: %(state)s instance %(name)s %(id)s\n"

    for idx, instance in enumerate(env.instances):
        ct = idx + 1
        args = {'ct': ct}
        args.update(instance)
        prompt_text += instance_template % args

    prompt_text += "Choose an instance: "

    def validation(input):
        choice = int(input)
        if choice not in range(1, len(env.instances) + 1):
            raise ValueError("%d is not a valid instance" % choice)
        return choice

    choice = prompt(prompt_text, validate=validation)
    env.active_instance = env.instances[choice - 1]['instance']


def run_command_on_selected_server(command):
    select_instance()
    selected_hosts = [
        'ubuntu@' + env.active_instance.public_dns_name
    ]
    execute(command, hosts=selected_hosts)


def stop_instance():
    select_instance()
    print "Stopping instance %s.\n" % env.active_instance
    env.ec2.stop_instances(instance_ids=[env.active_instance.id, ])


def terminate_instance():
    select_instance(state='stopped')
    prompt_text = (
        "THIS WILL TERMINATE THE INSTANCE.\n"
        "THIS ACTION CANNOT BE UNDONE.\n"
        "ARE YOU SURE? (Y/n)\n"
    )

    def validation(input):
        choice = input
        if choice not in ['Y', 'n']:
            raise ValueError("%s is not a valid choice." % choice)
        return choice

    def terminate_selected_instance():
        termination_segment = [
            "Fetching axe and black hood...",
            "Dragging instance to execution stone...",
            "Ignoring pleas and protests from instance...",
            "Executing instance..."
        ]

        for act in termination_segment:
            print act
            time.sleep(1)

        env.ec2.terminate_instances(instance_ids=[env.active_instance.id, ])

        print "Comforting family of instance..."
        time.sleep(1)
        print "Instance terminated.\nYou monster."

    choice = prompt(prompt_text, validate=validation)
    if choice == 'Y':
        terminate_selected_instance()


def _setup_suite():
    # Update apt, install the stuff we need, and update pip
    sudo('apt-get update')
    sudo('apt-get install -y nginx git python-pip supervisor')
    sudo('pip install --upgrade pip')

    # Go ahead and stop supervisord from running; it will be
    # restarted everytime we deploy anyway
    sudo('service stop supervisor')

    # If this is a brand new instance, we'll make a copy of the
    # default nginx configuration for backup
    if not files.exists(
        '/etc/nginx/sites-available/original-default',
        use_sudo=True
    ):
        sudo(
            'cp /etc/nginx/sites-available/default '
            '/etc/nginx/sites-available/original-default'
        )

    # Here we upload our custom nginx config to the default
    # location on the instance
    put(local_path="~/projects/fabrictests/simple_nginx_config",
        remote_path="/etc/nginx/sites-available/default",
        use_sudo=True)

    # Create the directory which will house old versions of the
    # application whenever a new version is deployed
    if not files.exists("~/.previous/"):
        run('mkdir ~/.previous')

    # Create the default supervisord config file to be edited
    if files.exists(
        '/etc/supervisord.conf',
        use_sudo=True,
    ):
        sudo('rm -f /etc/supervisord.conf')
    sudo('echo_supervisord_conf > /etc/supervisord.conf')

    # Give supervisor the ability to run our app
    append(
        '/etc/supervisord.conf',
        '\n[program:{p}]\ncommand=python ~/{p}/{app}'.format(
            p=projname, app=appname),
        use_sudo=True,
    )

    # Startup nginx!
    sudo('service nginx start')


def _deploy():
    # Stop nginx and supervisor
    sudo('service nginx stop')
    sudo('service supervisor stop')

    # Prepare a datestamp
    from datetime import datetime
    now = datetime.now()
    d = now.strftime("%Y_%m_%e__%H_%M_%S")

    # If there's an existing version of the app, move it into
    # the `~/.previous` directory and datestamp it
    if files.exists('~/{p}'.format(p=projname)):
        run('mv ~/{p} ~/.previous/{d}'.format(p=projname, d=d))

    # Pull down the project on branch=master from GitHub and
    # store it in `~/{projname}` directory
    run(
        'git clone http://github.com/{gp} '
        '-b master --single-branch '
        '~/{p}'.format(
            gp=git_path,
            p=projname,
        )
    )

    # Start up supervisor and nginx
    sudo('service supervisor start')
    sudo('service nginx start')


def setup_suite():
    run_command_on_selected_server(_setup_suite)


def deploy():
    run_command_on_selected_server(_deploy)
