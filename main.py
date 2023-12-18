import urllib.request
import json
from pathlib import Path

# Support for command line arugments
import argparse
parser = argparse.ArgumentParser(description="Script to download data from CMIP")
parser.add_argument("-u", "--url", type=str, help="Query URL for data to be downloaded, more info in README.md", default="http://esgf-node.llnl.gov/esg-search/search/?offset=0&limit=10&type=Dataset&replica=false&latest=true&source_id=CESM2&experiment_id=ssp370&frequency=mon&variable_id=gpp%2Churs%2Cps%2Ctran&project=CMIP6&facets=mip_era%2Cactivity_id%2Cproduct%2Csource_id%2Cinstitution_id%2Csource_type%2Cnominal_resolution%2Cexperiment_id%2Csub_experiment_id%2Cvariant_label%2Cgrid_label%2Ctable_id%2Cfrequency%2Crealm%2Cvariable_id%2Ccf_standard_name%2Cdata_node&format=application%2Fsolr%2Bjson")
parser.add_argument("-o", "--output", type=str, help="Path of folder/directory that files will be downloaded to", default="./cmipdata/")
args = parser.parse_args()

# Any dataset from this search url will be pulled
# For more info check README.md
searchurl = args.url

download_urls = []
with urllib.request.urlopen(searchurl) as query:
	# Fetch info about datasets matching searchurl
	query_info = json.load(query)["response"]
	print("Query found:", query_info["numFound"], "datasets")

	# For each dataset in query...
	for dataset_info in query_info["docs"]:
		# Get the id of each dataset and make another request to get the download urls
		id = dataset_info["id"]
		with urllib.request.urlopen("https://esgf-node.llnl.gov/search_files/"+id+"/esgf-node.llnl.gov/") as subquery:
			dataset_metadata = json.load(subquery)
			# For each file in the dataset, we add the download url to our list of downloard_urls
			for file_metadata in dataset_metadata["response"]["docs"]:
				# Each file has several download urls for different protocols ie HTTP, OpenDAP, Globus, we will only use HTTP
				for download_url in file_metadata["url"]:
					if download_url.startswith("http"):
						download_urls.append(download_url.split('|')[0])

# Folder to download to, if it doesn't exist create it
path = args.output
Path(path).mkdir(parents=True, exist_ok=True)

# Download each of the files...
i = 1
print("Query found:", len(download_urls), "files")
for url in download_urls:
	#print(url)
	file_name = url.rsplit('/', 1)[-1]
	print("GET", "(",i,"/",len(download_urls),")", file_name)
	try:
		urllib.request.urlretrieve(url, path + file_name)
		print("COMPLETE")
	except Exception as err:
		print("FAILED", err)
	i += 1
