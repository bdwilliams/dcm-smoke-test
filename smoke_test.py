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
from mixcoatl.admin.job import Job

jobs = []
servers_launched = []
volumes_created = []
server_launch_avg = []
snapshots_created = []
images_created = []
averages = [int(time.time())]

# TODO:
# Use geography/Subscription before running unnecessary tests.
# Cleanup ROOT-mounted Volumes

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
				job_table.add_row([the_job.job_id, the_job.status, the_job.description, round((min_to_comp/60),2)])
				
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
	average = round((sum(job_averages)/60)/len(job_averages),2)
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
	parser.add_argument('--budget', '-b', help='Budget Code ID')	
	cmd_args = parser.parse_args()
	
	if cmd_args.account is not None and cmd_args.region is not None and cmd_args.servers is not None and cmd_args.product is not None and cmd_args.datacenter is not None and cmd_args.machineimage is not None and cmd_args.budget is not None:
		account_id = cmd_args.account
		region_id = cmd_args.region
		total_servers = int(cmd_args.servers)
		server_product_id = cmd_args.product
		data_center_id = cmd_args.datacenter
		machine_image_id = cmd_args.machineimage
		billing_code_id = cmd_args.budget
		network_id = cmd_args.network
	else:
		account_table = PrettyTable(["Account ID", "Account Name"]);
		start = time.time()
		
		# TODO: list the status or not show accounts with STATUS != 'ACTIVE'
		for account in Account.all():
			account_table.add_row([account.account_id, account.customer['business_name']])
		
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
		
		if len(Network.all(region_id=region_id)) > 0:
			network_id_table = PrettyTable(["Network ID", "Network Name"])
			for n in Network.all(region_id=region_id):
				n.pprint()
		
			network_id = input("Enter a Network (Type 0 for None): ")
		else:
			network_id = 0
		
		total_servers = input("How many resources would you like to create at a time (ie: 3)? ")

for ts in range(0, total_servers):
	server_name = "test-server-"+name_generator()
	print "Launching server : %s" % (server_name)
	new_server = Server()
	new_server.provider_product_id = server_product_id
	new_server.machine_image = machine_image_id
	new_server.data_center = data_center_id
	new_server.description = server_name
	new_server.name = server_name
	new_server.vlan = network_id
	new_server.budget = billing_code_id
	job_id = new_server.launch()
	jobs.append(job_id)

# Watch server launch jobs
watch_jobs()

for vc in range(0, total_servers):
	name = "test-volume-"+name_generator()
	new_volume = Volume()
	new_volume.data_center = data_center_id
	new_volume.description = name
	new_volume.name = name
	new_volume.size_in_gb = 10
	new_volume.budget = billing_code_id
	result = new_volume.create()
	print("Creating Volume : %s" % name)
	jobs.append(result.job_id)

# Watch volume create jobs
watch_jobs()

si = 0
for av in servers_launched:
	print "Attaching Volume #",volumes_created[si],"to Server #",av
	result = Volume(volumes_created[si]).attach(av)
	jobs.append(result.current_job)
	si += 1

# Watch volume attach jobs
watch_jobs()

# TODO: Does not seem to change snapshot name during create.
for sc in volumes_created:
	volume = Volume(sc)
	volume.name = "test-snapshot-"+name_generator()
	volume.budget = 10287
	result = volume.snapshot()
	print "Snapshoting volume : #%s" % (sc)
	jobs.append(result.current_job)

# Watch snapshot jobs
watch_jobs()

for mi in servers_launched:
	m = MachineImage()
	m.server_id = 458354
	m.name = "test-machine-image-"+name_generator()
	m.budget = 10287
	results = m.create()
	print "Imaging server : #%s" % (mi)
	jobs.append(results)

# Watch imaging jobs
watch_jobs()

print "Cleaning up the mess..."

for st in servers_launched:
	server = Server(st)
	result = server.destroy()
	print "Terminating server : #%s" % (st)

for vd in volumes_created:
    volume = Volume(vd)
    result = volume.destroy()
    print "Deleting volume : #%s" % (vd)

for sd in snapshots_created:
    snapshot = Snapshot(sd)
    result = snapshot.destroy()
    print "Deleting snapshot : #%s" % (sd)

for md in images_created:
    m = MachineImage(md)
    result = m.destroy()
    print "Deleting image : #%s" % (md)

# Write data for trending analysis.
if os.environ.has_key('ES_ENDPOINT'):
	parts = os.environ['ES_ENDPOINT'].split('//', 1)
	parts = parts[1].split('/', 1)[0]
	parts = parts.split(':', 1)[0]
	stat_dir = parts
else:
	stat_dir = "cloud.enstratius.com"

stat_path = 'stats/'+stat_dir
if not os.path.exists(stat_path):
	os.makedirs(stat_path)

file = stat_path+'/'+str(account_id)+'.csv'
list = [str(i) for i in averages]

if not os.path.exists(file):
	with open(file, 'a') as f:
		f.write('#date,servers,volumes,attach,snapshots,image\n')

with open(file, 'a') as f:
	f.write(','.join(list)+'\n')

with open(file) as f:
    hist_servers = []
    hist_volumes = []
    hist_attach = []
    hist_snapshots = []
    hist_images = []
    next(f)

    for line in f:
		results = line.rstrip('\n').split(',')
		hist_servers.append(float(results[1]))
		hist_volumes.append(float(results[2]))
		hist_attach.append(float(results[3]))
		hist_snapshots.append(float(results[4]))
		hist_images.append(float(results[5]))

print "Server(s) launched in "+str(averages[1])+" minutes.  Average is "+str(round(sum(hist_servers)/len(hist_servers), 2))+" minutes ( "+str(round(100 - ((averages[1] / round(sum(hist_servers)/len(hist_servers), 2) * 100)), 2))+"% change )"
print "Volume(s) created in "+str(averages[2])+" minutes. Average is "+str(round(sum(hist_volumes)/len(hist_volumes), 2))+" minutes ( "+str(round(100 - ((averages[2] / round(sum(hist_volumes)/len(hist_volumes), 2) * 100)), 2))+"% change )"
print "Volume(s) attached in "+str(averages[3])+" minutes.  Average is "+str(round(sum(hist_attach)/len(hist_attach), 2))+" minutes ( "+str(round(100 - ((averages[3] / round(sum(hist_attach)/len(hist_attach), 2) * 100)), 2))+"% change )"
print "Volume snapshot(s) completed in "+str(averages[4])+" minutes.  Average is "+str(round(sum(hist_snapshots)/len(hist_snapshots), 2))+" minutes ( "+str(round(100 - ((averages[4] / round(sum(hist_snapshots)/len(hist_snapshots), 2) * 100)), 2))+"% change )"
print "Server(s) imaged in "+str(averages[5])+" minutes.  Average is "+str(round(sum(hist_images)/len(hist_images), 2))+" minutes ( "+str(round(100 - ((averages[5] / round(sum(hist_images)/len(hist_images), 2) * 100)), 2))+"% change )"
