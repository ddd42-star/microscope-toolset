# Microscope Toolset
This repository is a toolset for microscope that use pymmcore-plus with LLM


### How to get  started

In order to use this toolset, you need to have python installed. There are differents option, you could use *Anaconda*, *miniconda* or *mamba*. After you installed your favorite package and environment management system create a specific environment for this toolset.

```
conda create -n microscope-toolset python=3.12.11
```
Afterwards activate your newly environment
```
conda activate microscope-toolset
```
Create a new folder and clone the _microscope-toolset_ repository
```
git clone https://github.com/ddd42-star/microscope-toolset.git
```
Then go into the folder of this repository and install all the packages using the *requirements* file
```
pip install -r requirements.txt
```

### Create the vector database with pdf files
To help the different agents to avoid hallucination, it's advised to create a vector database with the different "knowledge". We have the documentation of *pymmcore_plus* and the publications of the *Pertz Lab*. If you want to add other pdfs file you can run this command:
```
python .\src\create_database_from_publication.py --db <path to db> --doc <path to pdf(s)>
```
In the folder that you choose were to save the database, at the moment two directories will be created: *pages_png* and *pages_markdown*. The first will contain the png files of each page of the document and in the second the markdown files of the text extracted. 

### How to start the toolset

> Currently, the *Large Language Model* in use is from OpenAI. In the future it will be added the possibilities to choose the preferred Model. Be sure to have saved in the environment the api key for OpenAI with *OPENAI_API_KEY*.

Run the following command for starting the Napari GUI
```
python .\src\plugin_napari.py
```
On the right there is the panel control that will start or stop the MCP Microscope Toolset server.

In the UI at your choice (e.g. vs-code, Claude Desktop) add the configuration file of the mcp server.
```
{
	"servers": {
		"microscope toolset": {
			"url": "http://127.1.1.1:5500/mcp",
			"type": "http",
			"env": {
				"OPENAI_API_KEY":"${input:api-key}"
			}
		}
	},
	"inputs": [
		{
      "type": "promptString",
      "id": "api-key",
      "description": "Please enter your OpenAI API key.",
      "password": true
    }
  ]
}
```
After you added the *mcp.json* configuration file, you can start the MCP Client that will connect to the server.

