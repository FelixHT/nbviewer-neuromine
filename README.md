# nbviewer-neuromine

nbviewer-neuromine is a fork of the [The Jupyter Notebook Viewer](http://nbviewer.ipython.org) and is tailored around navigating local notebook projects.

![ScreenShot](nbviewer/static/img/neuromine_screenshot.png?raw=true "Frontpage screenshot")

## Motivation

I am a data scientist working in collaboration with several experiment-focused, biology labs.
A big part of my research is to develop new techniques and ultimately model data to undertsand the underlying processes.
The Jupyter notebooks allow for obvious flexibility but also transparency because every figure and every analysis comes with its own code.
This turns out to be very useful not only for dissemination and collaboration but also for educating people on coding and data analysis.
Hence, I have been working with Jupyter notebooks running on local servers for a while and that served the above purposes very well.
However, I also needed to scale the approach to a larger pool of users who are not always consumers.
Also, some of the analysis techniques are well established now and a polished viewer provides a bigger picture view on the datasets, which is ultimately useful to answer the scientific questions at hand.
For this purpose I decided to run Jupyter notebook viewer locally.
This allows me to share notebooks to multiple users in read-only mode.
I then explored nbviewer's functionalities and learned a lot about its engines, so I started playing with them to meet some specific needs.
I figured I had to modify some code so although I'm not sure a fork was strictly necessary, well here I am.
I hope you enjoy the results of this experiment.

### Why 'neuromine'??

I work in neuroscience.
I search brain mines for golden data.
The original idea for this project was mine.

## Features

- Importantly, I removed the input cells and the input and output prompts of the notebook rendering. (Another possibility was to use cell toggles or a global toggle, but aesthetically both these solutions suck so whatever.)
- I added a simple but effective password protection (default is 'guest', but see below).
- I edited the rendered HTMLs to reflect my own style and needs, removing a whole lot of clumsy information. See below on how to edit the frontpage.

### Some todos and desiderata

- [ ] use the config file for storing password
- [ ] improve security and auth overall
- [ ] logout
- [ ] notebook description in the tree view
- [ ] interactive plots using widgets (it should already work but haven't tested)
- [x] button to enter edit mode on separate server
- [ ] better/customizable folders filtering
- [ ] fancy folder navigation
- [ ] a way to quickly navigate from one subject to another (e.g., navbar?)
- [ ] remove all the unnecessary nbviewer features
- [ ] dataset upload


## A typical structure of my datasets

Although in principle the viewer can be used in many different situations, I modified it with a specific model in mind.
This model is reflected by the folder structure of my datasets.
At the moment there is not much in the rendered HTMLs that reflects this structure and this allows for greater flexibility on a dataaset-by-dataset basis.
However, I may change my mind in the future so let's just put it here:

```
/dataset
|-- subj1
|   |-- session1
|   |   `-- nbs
|   |       (analysis of single session data)
|   |-- ...
|   |-- sessionM
|   `-- nbs
|       (analysis comparing sessions, within subject)
|-- ...
|-- subjN
|   |-- session1
|   |-- ...
|   `-- sessionO
`-- nbs
    (analysis comparing subjects)
```

## Frontpage example

I use a frontpage that looks like this:

```
{"title": "neuromine",
 "subtitle": "<some subtitle>",
 "text": "<my email>",
 "show_input": false,
 "sections":[
   {   
     "header":"<name of first group of datasets>",
     "links":[
       {
         "text": "<name of first dataset>",
         "target": "localfile/<folder name where notebooks are stored>",
         "img": "/static/img/logo.png"
       },
       {
         "text": "<name of second dataset>",
         "target": "localfile/<folder name where notebooks are stored>",
         "img": "/static/img/logo.png"
       },
     ]   
   },  
   {   
     "header":"<name of second group of datasets>",
     "links":[
       {
         "text": "<name of first dataset>",
         "target": "localfile/<folder name where notebooks are stored>",
         "img": "/static/img/logo.png"
       },
       {
         "text": "<name of second dataset>",
         "target": "localfile/<folder name where notebooks are stored>",
         "img": "/static/img/logo.png"
       },
     ]   
   },
 ]
}

```

## Security
**Warning: running the server on a public network is unsafe.**

Please refer to [Jupyter Notebook](https://jupyter-notebook.readthedocs.io/en/stable/public_server.html) doc on how to generate a password.
Copy the password into a file then pass the file via the `--passwordfile` inline option.
Example:
`u'sha1:18f0d2b1de95:90653605332a1b3c7d680010e509d2e15d7cd3c5'`
(yes, the `u'` and `'` are important).
You can also create your own certificates and pass them with the `--sslkey` and `--sslcert` inline options.

I took some code from the Jupyter Notebook security module.

## Disclaimer

Being close to a newbie in the web apps world, the features I added on top of the nbviewer may be considered quite poorly implemented.
For instance, I couldn't really follow the indications for customization in the Jupyter Notebook Viewer page, so I decided to go my own, more straight-forward and perhaps sacrilegious path.
Any feedback or pull requests are more than welcome!

## Installation

Tested on python 3.6.8.
See the Local Installation in [The Jupyter Notebook Viewer](http://nbviewer.ipython.org) page.
I generated a json file that I pass as `--frontpage`.

## Run

```shell
$ cd <path to repo>
$ python -m nbviewer --debug --no-cache --locafiles=<myfolder>
```
where `<myfolder>` points to a folder with your datasets full of notebooks.

Now navigate to `http://127.0.0.1:5000`.
Type password `guest` and enjoy.
**Warning: running the server on a public network is unsafe.**

This will automatically relaunch the server if a change is detected on a python file, and not cache any results. You can then just do the modifications you like to the source code and/or the templates then refresh the pages.

## What I ended up learning

- [Jinja](https://jinja.palletsprojects.com/en/2.10.x/)
- [Tornado](https://www.tornadoweb.org/en/stable/)
- some common best practices, e.g., the use of [traitlets](https://pypi.org/project/traitlets/)
- how to encode and decode hash passwords using [hashlib](https://docs.python.org/2/library/hashlib.html)
