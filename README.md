# COMP90024 Team 72 Project
## Video resources
Youtube Link:
https://www.youtube.com/playlist?list=PLBGy6cO3iY4JJfzsyCUD9kTY9J9CzDUBh
## Project Overview
In this project, we designed and implemented a cloud native distributed pipeline for collecting, processing, and visualizing public opinions related to tariffs. By utilizing the OpenStack infrastructure and Kubernetes cluster, we integrate Fission’s serverless functionality with Redis as a message queue to automate data ingestion, cleaning, and storage in Elasticsearch. On this basis, we used Python-based NLP to perform sentiment analysis and topic extraction, and used Folium to build geospatial maps and dashboards.

## Team Members and Responsibilities
| Team Members    | Responsibility |
|-----------------|----------------|
| **Jiangyi Yang** | - Deployment of the whole cluster, including all components such as Fission, Redis and ES<br>- Design and implement of all backend jobs such as fission components and message queue and unittests<br>- Design and implements of the data pipeline and the system architecture<br>- All codes are placed in the `backend` folder |
| **DongPing Lou** | - Design and implementation of the data collection jobs<br>- Design and deployment of the tariff scenario<br>- All codes are placed in the `dataCollection` folder |
| **Gefei Zhao**   | - Analysis about the sentiment and opinion scenario<br>- Cleaning data and send back to ES<br>- Implement of the sentiment score and sentiment opinion<br>- All codes are placed in the data_analysis folder |
| **ShanShan Li**  | - Visualization of posts opinion and sentiment<br>- Visualization of engagements and posts trend<br>- Visualization of Keyword distribution<br>- All codes are placed in the `data visualization` folder |
| **Yadi Chen**    | - Visualization of geological posts and engagement distribution<br>- Visualization of regional posts and engagements count<br>- Visualization of posts and engagements in different domains |


## Project Structure
```
comp90024_TEAM_72/
├── backend/                 # Backend services
│   └── fission/            # Fission serverless functions
│       ├── harvester/      # Data collection services and unittest
│       ├── mqueue/         # Enqueuing data to Redis
│       ├── addmoutputdata/ # Formating data and sending data to ES
│       ├── mprocessor.js   # Processing data
│       ├── specs/          # Storing ymal file about fission components
│       └── cmd.sh          # All deployment command about fission env, functions, packages and triggers
├── data_collecting/        # Data collection scripts
├── data_analysis/         # Data analysis modules
├── data_visualization1/   # Visualization scripts written by Yadi Chen
├── data_visualization2/   # Visualization scripts written by Shanshan Li
├── installation/          # Kubernetes and infrastructure setup files
├── docs/                  # Final report
```

## Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- Kubernetes cluster
- Kubectl
- Helm
- OpenStack clients
- MRC project with enough resources to create a Kubernetes cluster.



## Installation

### 1. Backend Setup
1. Preperation
   Procedures included in the given comp90024 installation readme.md should be impelemented. Such as the MRC config, K8s cluster creating, Fission installation, Redis installation and Elastic Search installation.

2. Installation of fission components.
   Scpec folder is already given in this project, which is located in the fission folder. So by typing
   ```bash
   fission spec apply --specdir ./specs --wait
   ```
   You can Install all needed fission components quickly.

3. Another way to install fission components.
   If you can't installation fission components by spec yaml. you can install components step by step through cmd.sh which is located in the fission folder.
   First you need install basic python and node.js environement by running.
   ```bash
   fission env create --name python --image fission/python-env --builder fission/python-builder
   fission env create --name nodejs --image fission/node-env --builder fission/node-builder
    ```
   Then you should install package mharvesters, addmoutputdata, mqueue. Their commands are given in cmd.sh. 
   After that you should install function bash, refresh, mqueue, mprocessor and addmoutputdata.yaml. Their commands are also given in cmd.sh.
   Finally you need to install two mqtriggers and one timertrigger. They can named as add-moutputdata, mprocessing and mtimer. Their commands are given.
   Then all fisson compoments are installed.
4. ES index creation
   ES index should also be created. And the creation command is given in cmd.sh. The index is called moutputdata.
   But before the command is run, you should start a port-forward.
   ```bash
   kubectl port-forward service/elasticsearch-master -n elastic 9200:9200
    ```
   Now, if every processed, you can find data in Elastic search and the index is called moutputdata.
   Or you can run the command
   ```bash
   fission function log -f --name refresh
    ```
   To check the logs.

### 2. Backend test
   Two unit test functions,test_base and test_refresh, are provided.They have tested many functions that the base and refresh harvesters have used. 
   To run the unit test functions,you should input the code:
   ```bash
   cd backend/fission/harvester
   python -m unittest test_base.py
   python -m unittest test_refresh.py
   ```
   

### 3. Data Analysis 
   1. Install needed package
      To run the data analysis script, many package should be installed.
      - emoji
      - transformers
      - tqdm

   2. Run Jupyter Notebook
      Then you need to start the port-worward.   
      ```bash
      kubectl port-forward service/elasticsearch-master -n elastic 9200:9200
      ```
      And now you can run notebook sentiment_analysis.ipynb to get sentiment score and sentiment label.
      Also you need to run update_daya.ipynb to send analysed data to elastic search.


### 4. Frontend
   1.Installed needed package
      
      To run the data visualization script, the following packages should be installed.
      - folium
      - geopandas
      - pandas
      - ipywidgets
      - matplotlib
      - IPython

   1. Run data visualization module 1

      Navigate to the data_visualization1 folder, you can run the data_visualization1.ipynb to get the visualized data about analysis of posts and engagement in different domains and countries.
   2. Run data visualization module 2
   
       Navigate to the data_visualization2 folder, you can run the data_visualization2.ipynb to get the visualized data about posts and engagement in weekly scale. You can also get to know about the topic word through the word cloud and the bar chart about key words.




## License
This project is licensed under the MIT License - see the LICENSE file for details.
