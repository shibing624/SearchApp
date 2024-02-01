[**🇨🇳中文**](https://github.com/shibing624/SmartSearch/blob/main/README_zh.md) | [**🌐English**](https://github.com/shibing624/SmartSearch/blob/main/README.md) 

<div align="center">
    <a href="https://github.com/shibing624/SmartSearch">
    <img src="https://github.com/shibing624/SmartSearch/blob/main/docs/icon.svg" height="50" alt="Logo">
    </a>
    <br/>
    <a href="https://search.mulanai.com/" target="_blank"> Online Demo </a>
    <br/>
    <img width="70%" src="https://github.com/shibing624/SmartSearch/blob/main/docs/screenshot.png">
</div>

-----------------

# SmartSearch: Build your own conversational search engine with LLMs
[![HF Models](https://img.shields.io/badge/Hugging%20Face-shibing624-green)](https://huggingface.co/shibing624)
[![Github Stars](https://img.shields.io/github/stars/shibing624/SmartSearch?color=yellow)](https://star-history.com/#shibing624/SmartSearch&Timeline)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/SmartSearch.svg)](https://github.com/shibing624/SmartSearch/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)


## Features
- Built-in support for LLM, you can build API with local model
- Support OpenAI LLMs, such as `gpt-4`
- Built-in support for search engine
- Customizable pretty UI interface
- Shareable, cached search results
- Support for follow-up questions, continuous Q&A
- Supports query analysis, rewrites queries based on context for precise search

## Setup Search Engine API
There are two default supported search engines: Bing and Google.
 
### Bing Search
To use the Bing Web Search API, please visit [this link](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) to obtain your Bing subscription key.

### Google Search
You have three options for Google Search: you can use the [SearchApi Google Search API](https://www.searchapi.io/) from SearchApi, 
[Serper Google Search API](https://www.serper.dev) from Serper, or opt for the [Programmable Search Engine](https://developers.google.com/custom-search) provided by Google.

## Setup LLM and KV

> [!NOTE]
> We recommend using the built-in llm and kv functions with Lepton. 
> Running the following commands to set up them automatically.

```shell
pip install -U leptonai && lep login
pip install -r requirements.txt
```


## Build and Run

1. . Build web
```shell
cd web && npm install && npm run build
```
2. Run server
```shell
export BING_SEARCH_V7_SUBSCRIPTION_KEY=YOUR_BING_SUBSCRIPTION_KEY
BACKEND=BING python search.py
```

alternatively, you can run server with Google Search API.
#### Using Google Search Api
For Google Search using SearchApi:
```shell
export SEARCHAPI_API_KEY=YOUR_SEARCHAPI_API_KEY
BACKEND=SEARCHAPI python search.py
```

For Google Search using Serper:
```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
BACKEND=SERPER python search.py
```

For Google Search using Programmable Search Engine:
```shell
export GOOGLE_SEARCH_API_KEY=YOUR_GOOGLE_SEARCH_API_KEY
export GOOGLE_SEARCH_CX=YOUR_GOOGLE_SEARCH_ENGINE_ID
BACKEND=GOOGLE python search.py
```

ok, now your search app running on http://0.0.0.0:8080

## Deploy

You can deploy your own version via

```shell
lep photon run -n search-with-lepton-modified -m search.py --env BACKEND=BING --env BING_SEARCH_V7_SUBSCRIPTION_KEY=YOUR_BING_SUBSCRIPTION_KEY
```

Learn more about `lep photon` [here](https://www.lepton.ai/docs).


#### Deployment Configurations

Here are the configurations you can set for your deployment:
* Name: The name of your deployment, like "my-search"
* Resource Shape: most of heavy lifting will be done by the LLM server and the search engine API, so you can choose a small resource shape. `cpu.small` is usually good enough.

Then, set the following environmental variables.

* `BACKEND`: the search backend to use. If you don't have bing or google set up, simply use `LEPTON` to try the demo. Otherwise, do `BING`, `GOOGLE`, `SERPER` or `SEARCHAPI`.
* `LLM_MODEL`: the LLM model to run. We recommend using `mixtral-8x7b`, but if you want to experiment other models, you can try the ones hosted on LeptonAI, for example, `llama2-70b`, `llama2-13b`, `llama2-7b`. Note that small models won't work that well.
* `KV_NAME`: the Lepton KV to use to store the search results. You can use the default `search-with-lepton`.
* `RELATED_QUESTIONS`: whether to generate related questions. If you set this to `true`, the search engine will generate related questions for you. Otherwise, it will not.
* `GOOGLE_SEARCH_CX`: if you are using google, specify the search cx. Otherwise, leave it empty.
* `LEPTON_ENABLE_AUTH_BY_COOKIE`: this is to allow web UI access to the deployment. Set it to `true`.

In addition, you will need to set the following secrets:
* `LEPTON_WORKSPACE_TOKEN`: this is required to call Lepton's LLM and KV apis. You can find your workspace token at [Settings](https://dashboard.lepton.ai/workspace-redirect/settings).
* `BING_SEARCH_V7_SUBSCRIPTION_KEY`: if you are using Bing, you need to specify the subscription key. Otherwise it is not needed.
* `GOOGLE_SEARCH_API_KEY`: if you are using Google, you need to specify the search api key. Note that you should also specify the cx in the env. If you are not using Google, it is not needed.
* `SEARCHAPI_API_KEY`: if you are using SearchApi, a 3rd party Google Search API, you need to specify the api key.
* `OPENAI_API_KEY`: if you are using OpenAI, you need to specify the api key.
* `OPENAI_BASE_URL`: if you are using OpenAI, you can specify the base url. It is usually `https://api.openai.com/v1`.


## Todo

1. Support multi-round retrieval, mainly displaying multi-round retrieval results on the page.
2. Support third-party LLM's API, such as qwen, baichuan, etc.
3. Mini program support, currently only supports web end.

## Contact

- Issue(suggestion): [![GitHub issues](https://img.shields.io/github/issues/shibing624/SmartSearch.svg)](https://github.com/shibing624/SmartSearch/issues)
- Email: xuming: xuming624@qq.com
- Wechat: Add my *Wechat ID: xuming624, note: name-company-NLP* to join the NLP discussion group.

## License

The license agreement is [The Apache License 2.0](LICENSE), which can be used for commercial purposes for free. Please include SmartSearch's link and license agreement in the product description.

## Contribute

The project code is still rough, if everyone has improvements to the code, welcome to submit back to this project.


## Reference
- [leptonai/search_with_lepton](https://github.com/leptonai/search_with_lepton/tree/main)

