#!/usr/bin/env python
 
import os, string, random, argparse, sys, time
from prettytable import PrettyTable
from datetime import datetime
from mixcoatl.admin.account import Account
from mixcoatl.geography.region import Region
from mixcoatl.geography.datacenter import DataCenter
from mixcoatl.network.network import Network
from mixcoatl.infrastructure.machine_image import MachineImage
from mixcoatl.infrastructure.server_product import ServerProduct
from mixcoatl.admin.billing_code import BillingCode
from mixcoatl.infrastructure.server import Server
from mixcoatl.infrastructure.volume import Volume
from mixcoatl.infrastructure.snapshot import Snapshot
from mixcoatl.geography.subscription import Subscription
from mixcoatl.automation.configuration_management_account import ConfigurationManagementAccount
from mixcoatl.automation.script import Script
from mixcoatl.admin.job import Job

jobs = []
servers_launched = []
volumes_created = []
server_launch_avg = []
snapshots_created = []
images_created = []
averages = [int(time.time())]
cm_account_id = None
cm_scripts = None

# TODO:
# Cleanup ROOT-mounted Volumes.
# Show Agent Versions (and skip CM once API returns isRegistered status)

def name_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def watch_jobs():
	job_averages = []
	print("Processing jobs... Please hold.")
	job_table = PrettyTable(["ID", "Status", "Description", "Minutes to Complete"])
	
	while len(jobs) > 0:
		for i in jobs:
			if Job.wait_for(i) == True:
				the_job = Job(i)           
				start = datetime.strptime(the_job.start_date.split("+")[0], '%Y-%m-%dT%H:%M:%S.%f')
				end = datetime.strptime(the_job.end_date.split("+")[0], '%Y-%m-%dT%H:%M:%S.%f')
				min_to_comp = (end - start).seconds
				job_averages.append(min_to_comp)
				job_table.add_row([the_job.job_id, the_job.status, the_job.description, round((min_to_comp/60),3)])
				
				if 'Launch Server' in the_job.description:
					servers_launched.append(int(the_job.message))
				elif 'CREATE VOLUME' in the_job.description:
					volumes_created.append(int(the_job.message))
				elif 'Snapshot of' in the_job.description:
					snapshots_created.append(int(the_job.message))
				elif 'Create Image' in the_job.description:
					images_created.append(int(the_job.message))

				jobs.remove(i)

	#print "Averages:",job_averages
	average = round((sum(job_averages)/60)/len(job_averages),3)
	averages.append(average)
	job_table.add_row(["--","--","--",average])
	
	print job_table

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--account', '-a', help='Account ID')
	parser.add_argument('--region', '-r', help='Region ID')
	parser.add_argument('--servers', '-s', help='Total Servers to Launch')
	parser.add_argument('--product', '-p', help='Server Product (ie: t1.micro)')
	parser.add_argument('--datacenter', '-d', help='Datacenter ID')
	parser.add_argument('--machineimage', '-m', help='Machine Image ID')
	parser.add_argument('--network', '-n', help='Network ID')
	parser.add_argument('--cm_account_id', '-cm', help='Configuration Management Account ID')
	parser.add_argument('--cm_scripts', '-cs', help='Configuration Management Scripts (comma delimited - no spaces)')
	parser.add_argument('--budget', '-b', help='Budget Code ID')
	parser.add_argument('--noimaging', '-ni', help='Skip Server Imaging', action='store_true')
	parser.add_argument('--nosnapshots', '-ns', help='Skip Volume Snapshotting', action='store_true')
	parser.add_argument('--novolumes', '-nv', help='Skip Volume Creation/Attaching', action='store_true')
	cmd_args = parser.parse_args()
	
	if cmd_args.account is not None and cmd_args.region is not None and cmd_args.servers is not None and cmd_args.product is not None and cmd_args.datacenter is not None and cmd_args.machineimage is not None and cmd_args.budget is not None:
		account_id = cmd_args.account
		region_id = int(cmd_args.region)
		total_servers = int(cmd_args.servers)
		server_product_id = cmd_args.product
		data_center_id = cmd_args.datacenter
		machine_image_id = cmd_args.machineimage
		billing_code_id = cmd_args.budget
		network_id = cmd_args.network
		cm_account_id = cmd_args.cm_account_id
		cm_scripts = cmd_args.cm_scripts
	else:
		account_table = PrettyTable(["Account ID", "Account Name"]);
		start = time.time()
		
		for account in Account.all():
			if account.status == 'ACTIVE':
				account_table.add_row([account.account_id, account.name])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print account_table
		
		account_id = input("Enter an Account ID: ")
		
		region_table = PrettyTable(["Region ID", "Region Name"]);
		start = time.time()
		
		params = {'account_id':account_id}
		for region in Region(params).all():
			region_table.add_row([region.region_id, region.name])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print region_table
		
		region_id = input("Enter a Region ID: ")
		
		datacenter_table = PrettyTable(["Datacenter ID", "Datacenter Name"])
		start = time.time()
		
		for dc in DataCenter.all(region_id):
			datacenter_table.add_row([dc.data_center_id, dc.description])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print datacenter_table
		
		data_center_id = input("Enter a Datacenter ID: ")
		
		# TODO: allow agent_version via mixcoatl.
		machine_image_table = PrettyTable(["Machine Image ID", "Machine Image Name", "Provider ID"])
		start = time.time()
		
		for mi in MachineImage.all(region_id):
			machine_image_table.add_row([mi.machine_image_id, mi.description, mi.provider_id])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print machine_image_table
		
		machine_image_id = input("Enter a Machine Image ID: ")
		
		billing_code_table = PrettyTable(["Budget ID", "Budget Name", "Budget Code", "Status"])
		start = time.time()
		
		for budget in BillingCode.all():
			billing_code_table.add_row([budget.billing_code_id, budget.name, budget.finance_code, budget.budget_state])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print billing_code_table
		
		billing_code_id = input("Enter a Billing Code ID: ")
		
		server_product_table = PrettyTable(["Provider Product ID", "Name", "Platform", "Currency", "Hourly Rate"])
		start = time.time()
		
		for sp in ServerProduct.all(region_id):
			server_product_table.add_row([sp.provider_product_id, sp.name, sp.platform, sp.currency, sp.hourly_rate])
		
		print 'Results returned in', time.time()-start, 'seconds.'
		print server_product_table
		
		server_product_id = raw_input("Enter a Server Product: ")
		
		yes = set(['yes','y', 'ye', ''])
		no = set(['no','n'])

		do_network = raw_input("Would you like to launch with a specific Network? (type yes or no):")

		if do_network is not None and do_network in yes:
			if len(Network.all(region_id=region_id)) > 0:
				network_table = PrettyTable(["ID", "Name", "Network Range"])
				start = time.time()
				for n in Network.all(region_id=region_id):
					network_table.add_row([n.network_id, n.name, n.network_address])
			
				print network_table
	
				network_id = raw_input("Enter a Network (Hit Enter for None): ")
				
				if network_id is None:
					network_id = 0
			else:
				network_id = 0

		do_cm = raw_input("Would you like to launch with Configuration Management? (type yes or no):")

		if do_cm is not None and do_cm in yes:
			cm_account = PrettyTable(["Status", "CM ID#", "Name", "Endpoint"]);
			start = time.time()
			
			if len(ConfigurationManagementAccount.all()) > 0:
				for cm in ConfigurationManagementAccount.all():
					if cm.status == 'ACTIVE':
						cm_account.add_row([cm.status, cm.cm_account_id, cm.cm_service['name'], cm.cm_service['service_endpoint']])
				
				print 'Results returned in', time.time()-start, 'seconds.'
				print cm_account
				
				cm_account_id = input("Enter a Configuration Management Account ID (Hit Enter for None): ")
				
				if cm_account_id is not None:
					scripts = PrettyTable(["Script ID", "Name"]);
					start = time.time()
					for sc in Script().all(cm_account_id):
						if sc['status'] == 'ACTIVE':
							scripts.add_row([sc['sharedScriptCode'], sc['name']])
					
					print 'Results returned in', time.time()-start, 'seconds.'
					print scripts
					
					cm_scripts = raw_input("Enter Script IDs (comma delimited - no spaces): ")

		skip_volumes = raw_input("Would you like to skip volume creation and attachment? (type yes or no): ")
		
		if skip_volumes in yes:
			cmd_args.novolumes = True

		skip_snapshots = raw_input("Would you like to skip snapshot creation? (type yes or no): ")
		
		if skip_snapshots in yes:
			cmd_args.nosnapshots = True

		skip_imaging = raw_input("Would you like to skip machine imaging? (type yes or no): ")
		
		if skip_imaging in yes:
			cmd_args.noimaging = True
				
		total_servers = input("How many resources would you like to create at a time (ie: 3)? ")

print "###"
print "# Started:\t\t%s" % (time.strftime("%c"))
print "# Account:\t\t%s" % account_id
print "# Region:\t\t%s" % region_id
print "# Datacenter:\t\t%s" % data_center_id
print "# Machine Image:\t%s" % machine_image_id
print "# Server Product:\t%s" % server_product_id
print "# Budget Code:\t\t%s" % billing_code_id

if cm_account_id is not None:
	print "# CM Account:\t\t%s" % cm_account_id

if cm_scripts is not None:
	print "# CM Scripts:\t\t%s" % cm_scripts

if cmd_args.network == "0" or network_id == "0" or network_id is None:
	print "# Network:\t\tNone"
	network_id = None
else:
	print "# Network:\t\t%s" % network_id

print "###"

run = "# Run again with:\t./smoke_test.py -a ",str(account_id)," -r ",str(region_id)," -d ",str(data_center_id)," -m ",str(machine_image_id)," -b ",str(billing_code_id)," -p ",str(server_product_id)

run = ''.join(run)

if network_id is not None:
	run += " -n "+str(network_id)

if cm_account_id is not None:
	run += " -cm "+str(cm_account_id)

if cm_scripts is not None:
	run += ' -cs '+str(cm_scripts)

if cmd_args.novolumes:
	run += ' -nv'

if cmd_args.nosnapshots:
	run += ' -ns'

if cmd_args.noimaging:
	run += ' -ni'

run += ' -s '+str(total_servers)

print run

sys.exit(1)

print "###"
print "# Subscriptions:"

sub = Subscription.region(region_id)['subscriptions']

if sub[0]['subscribedServer']:
	print "# Server:\t\t[OK]"
else:
	print "# Server:\t\t[UNSUPPORTED]"

if sub[0]['subscribedVolume']:
	print "# Volumes:\t\t[OK]"
else:
	print "# Volumes:\t\t[UNSUPPORTED]"

if sub[0]['subscribedSnapshot']:
	print "# Snapshots:\t\t[OK]"
else:
	print "# Snapshots:\t\t[UNSUPPORTED]"

if sub[0]['subscribedMachineImage']:
	print "# Image:\t\t[OK]"
else:
	print "# Image:\t\t[UNSUPPORTED]"

print "###"

if sub[0]['subscribedServer']:
	for ts in range(0, total_servers):
		server_name = "test-server-"+name_generator()
		print "Launching server : %s" % (server_name)
		new_server = Server()
		new_server.provider_product_id = server_product_id
		new_server.machine_image = int(machine_image_id)
		new_server.data_center = int(data_center_id)
		new_server.description = server_name
		new_server.name = server_name
		
		if network_id is not None:
			new_server.vlan = int(network_id)
		new_server.budget = int(billing_code_id)
		
		if cm_account_id is not None:
			new_server.cmAccount = int(cm_account_id)
			
			if cm_scripts is not None:
				new_server.cm_scripts = cm_scripts

		job_id = new_server.launch()
		jobs.append(job_id)
	
	# Watch server launch jobs
	watch_jobs()

if sub[0]['subscribedVolume'] and cmd_args.novolumes is None:
	for vc in range(0, total_servers):
		name = "test-volume-"+name_generator()
		new_volume = Volume()
		new_volume.data_center = data_center_id
		new_volume.description = name
		new_volume.name = name
		new_volume.size_in_gb = 5
		new_volume.budget = billing_code_id
		result = new_volume.create()
		print("Creating Volume : %s" % name)
		jobs.append(result.job_id)
	
	# Watch volume create jobs
	watch_jobs()

	if sub[0]['subscribedServer']:
		si = 0
		for av in servers_launched:
			print "Attaching Volume #",volumes_created[si],"to Server #",av
			result = Volume(volumes_created[si]).attach(av)
			jobs.append(result.current_job)
			si += 1
		
		# Watch volume attach jobs
		watch_jobs()

if sub[0]['subscribedSnapshot'] and cmd_args.nosnapshots is None and cmd_args.novolumes is None:
	# TODO: Does not seem to change snapshot name during create.
	for sc in volumes_created:
		volume = Volume(sc)
		volume.name = "test-snapshot-"+name_generator()
		volume.budget = billing_code_id
		result = volume.snapshot()
		print "Snapshoting volume : #%s" % (sc)
		jobs.append(result.current_job)
	
	# Watch snapshot jobs
	watch_jobs()

if sub[0]['subscribedMachineImage'] and sub[0]['subscribedServer'] and cmd_args.noimaging is None:
	sv = 0
	for mi in servers_launched:
		m = MachineImage()
		m.server_id = servers_launched[sv]
		m.name = "test-machine-image-"+name_generator()
		m.budget = billing_code_id
		results = m.create()
		print "Imaging server : #%s" % (mi)
		jobs.append(results)
		sv += 1
		
	# Watch imaging jobs
	watch_jobs()

print "Cleaning up the mess..."

if sub[0]['subscribedServer']:
	for st in servers_launched:
		server = Server(st)
		result = server.destroy()
		print "Terminating server : #%s" % (st)

if sub[0]['subscribedVolume'] and cmd_args.novolumes is None:
	for vd in volumes_created:
	    volume = Volume(vd)
	    result = volume.destroy()
	    print "Deleting volume : #%s" % (vd)

if sub[0]['subscribedSnapshot'] and cmd_args.nosnapshots is None and cmd_args.novolumes is None:
	for sd in snapshots_created:
	    snapshot = Snapshot(sd)
	    result = snapshot.destroy()
	    print "Deleting snapshot : #%s" % (sd)

if sub[0]['subscribedMachineImage'] and cmd_args.noimaging is None:
	for md in images_created:
	    m = MachineImage(md)
	    result = m.destroy()
	    print "Deleting image : #%s" % (md)