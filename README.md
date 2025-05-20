# microscope-toolset
This repository is a toolset for microscope that use pymmcore-plus with LLM


### How to get  started

In order to use this toolset, you need to have python installed. There are differents option, you could use *Anaconda*, *miniconda* or *mamba*. After you installed your favorite package and environment management system create a specific environment for this toolset.

```
conda create -n microscope-toolset python=3.12
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

### How to start the toolset

> Currently, the *Large Language Model* in use is from OpenAI. In the future it will be added the possibilities to choose the preferred Model. Be sure to have saved in the environment the api key for OpenAI with *OPENAI_API_KEY*.

Run the following command
```
python .\src\napari_microscope_toolset.py
```
The following GUI should now open
![My beatiful gui](/pictures/gui.png)
> You cannot choose other LLM languages model for the moment. The model used for all functionality are *gpt-4.1-mini*.
### Functionalities
The main functionality are the following:
#### LLM Assistant
This is a normal assistant. It simulates the web user experience of chatting with chat-gpt.
#### Scientific Assistant
This is a specialised assistant that use RAG to answer scientific questions. 
Currently, the database contains public publication of the *Pertz Group*. But in any case custom database can be used.
Simply create your own personal vector database and the correct name when calling the collection to use by the assistant.
#### Microscope toolset Assistant
This is the Microscope Assistant. It allows to interact with the microscope in use directly from
*chat widget*. 
> Before starting to use this functions, you need to load the configuration file of the microscope.
> If you don't do it, it will not work.

This Assistant use different specialised Agent to answer the user queries.

> To interact with the microscope hardware, it is used pymmcore-plus. If your microscope
> doesn't support pymmcore-plus it will not work.

