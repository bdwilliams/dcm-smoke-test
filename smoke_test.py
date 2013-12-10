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
from mixcoatl.admin.job import Job

jobs = []
job_averages = []
servers_launched = []
server_launch_avg = []

def name_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def watch_jobs(jobs):
	print("Processing jobs... Please hold.")
	job_table = PrettyTable(["ID", "Status", "Description", "Minutes to Complete"])
	
	while len(jobs) > 0:
		for i in jobs:
			if Job.wait_for(i) == True:
				the_job = Job(i)           
				start = datetime.strptime(the_job.start_date.split("+")[0], '%Y-%m-%dT%H:%M:%S.%f')
				end = datetime.strptime(the_job.end_date.split("+")[0], '%Y-%m-%dT%H:%M:%S.%f')
				min_to_comp = "{0:.2}".format(((end - start).total_seconds() / 60))
				job_averages.append(float(min_to_comp))
				job_table.add_row([the_job.job_id, the_job.status, the_job.description, min_to_comp])
				
				if 'Launch Server' in the_job.description:
					servers_launched.append(int(the_job.message))

				jobs.remove(i)
	
	job_table.add_row(["--","--","--","{0:.2}".format(sum(job_averages)/len(job_averages))])
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
		
		total_servers = input("How many servers would you like to launch? ")

for ts in range(0, total_servers):
	server_name = "test-"+name_generator()
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
watch_jobs(jobs)

for st in servers_launched:
	server = Server(st)
	result = server.destroy()
	print "Terminating server : #%s" % (st)