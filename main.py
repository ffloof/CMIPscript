import urllib.request
from urllib.parse import quote
import json
from pathlib import Path
import time

# Support for command line arugments
import argparse
parser = argparse.ArgumentParser(description="Script to download data from CMIP")
parser.add_argument("-u", "--url", type=str, help="Query URL for data to be downloaded, more info in README.md", default="https://aims2.llnl.gov/search/?project=CMIP6&activeFacets=%7B%22experiment_id%22%3A%221pctCO2-rad%22%2C%22variable_id%22%3A%22gpp%22%7D")
parser.add_argument("-o", "--output", type=str, help="Path of folder/directory that files will be downloaded to", default="./cmipdata/") 
args = parser.parse_args()

# Any dataset from this search url will be pulled
# For more info check README.md
searchurl = args.url
print(searchurl)
#print(searchurl.split("activeFacets"))

# Have to do a bit of manipulation to reformat it into the format that gets us .json metadata

params = json.loads(searchurl.split("activeFacets=")[1].replace("%22", "\"").replace("%7B", "{").replace("%3A", ":").replace("%2C", ",").replace("%7D", "}"))

templateurl = "https://aims2.llnl.gov/metagrid-backend/proxy/search?project=CMIP6&offset=0&limit=10000&type=Dataset&format=application%2Fsolr%2Bjson&facets=activity_id%2C+data_node%2C+source_id%2C+institution_id%2C+source_type%2C+experiment_id%2C+sub_experiment_id%2C+nominal_resolution%2C+variant_label%2C+grid_label%2C+table_id%2C+frequency%2C+realm%2C+variable_id%2C+cf_standard_name&latest=true&query=*"  #&experiment_id=1pctCO2-rad&variable_id=cVeg



templateaddon = ""
for (key, value) in params.items():
	templateaddon += "&" + key + "=" + value

searchurl = templateurl + quote(templateaddon, safe="&=")
#print(searchurl)


# First searches esgf metagrid for datasets matching given the paramaters
# Then for each dataset it finds the download urls
download_urls = []
with urllib.request.urlopen(searchurl) as query:
	query_info = json.load(query)["response"]


	print("Query found:", query_info["numFound"], "nodes")
	print("Indexing files...")

	# For each dataset in query...
	for dataset_info in query_info["docs"]:
		# Get the id of each dataset and make another request to get the download urls
		id = dataset_info["id"]
		with urllib.request.urlopen("https://aims2.llnl.gov/metagrid-backend/proxy/search?dataset_id="+id+"&format=application%2Fsolr%2Bjson&limit=10&offset=0&type=File&") as subquery:
			dataset_metadata = json.load(subquery)
			# For each file in the dataset, we add the download url to our list of downloard_urls
			for file_metadata in dataset_metadata["response"]["docs"]:
				# Each file has several download urls for different protocols ie HTTP, OpenDAP, Globus, we will only use HTTP
				for download_url in file_metadata["url"]:
					if download_url.startswith("http"):
						download_urls.append(download_url.split('|')[0])
						# TODO: add flag to filter files meta with .html


# Folder to download to, if it doesn't exist create it
path = args.output
Path(path).mkdir(parents=True, exist_ok=True)


# There are duplicate files since there are often duplicates hosted by different regions/servers
# We map filename to possible urls, so we only download it once
# And if the download doesn't work we can move on to the next candidate url

urlmap = {}

for url in download_urls:
	file_name = url.rsplit('/', 1)[-1]
	if (urlmap.get(file_name)) == None:
		urlmap[file_name] = []
	urlmap[file_name].append(url)


# Download each of the files...
#print(urlmap)
print("Query found:", len(urlmap), "files")

progress_counter = 1
for key in urlmap.keys():
	urllist = urlmap[key]
	for url in urllist:
		time.sleep(1) # Don't get rate limited'
		print("GET", "(",progress_counter,"/",len(urlmap),")", key)
		# print(url)
		try:
			urllib.request.urlretrieve(url, path + key)

			print("COMPLETE")
			progress_counter += 1
			break
		except Exception as err:
			print("FAILED", err)









