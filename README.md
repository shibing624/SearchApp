[**🇨🇳中文**](https://github.com/shibing624/SmartSearch/blob/main/README_zh.md) | [**🌐English**](https://github.com/shibing624/SmartSearch/blob/main/README.md) 

<div align="center">
    <a href="https://github.com/shibing624/SmartSearch">
    <img src="https://github.com/shibing624/SmartSearch/blob/main/docs/icon.svg" height="50" alt="Logo">
    </a>
    <br/>
    <a href="https://chat.mulanai.com/" target="_blank"> Online Demo </a>
    <br/>
    <img width="70%" src="https://github.com/shibing624/SmartSearch/blob/main/docs/screenshot.png">
</div>

-----------------

# SmartSearch: Build your own conversational search engine with LLMs
[![HF Models](https://img.shields.io/badge/Hugging%20Face-shibing624-green)](https://huggingface.co/shibing624)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/SmartSearch.svg)](https://github.com/shibing624/SmartSearch/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)

```markdown
## Features
- Supports models from various large model vendors, including OpenAI/ZhipuAI API, recommended to use the free `glm-4-flash`
- Built-in support for google serper/DDGS/ZhipuAI SearchPro search engines (free, recommended)
- Customizable and beautiful UI interface
- Shareable, cacheable search results
- Supports related questions and continuous Q&A

## Install Dependencies

```shell
pip install -r requirements.txt
```


## Run

```shell
python search.py
```
Now your search application is running at: http://0.0.0.0:8081


- Provides an online colab demo service: [demo.ipynb](https://github.com/shibing624/SearchGPT/blob/main/demo.ipynb), corresponding colab: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shibing624/SearchGPT/blob/main/demo.ipynb)

### Rebuild Frontend Web

Two ways to build the frontend:
1. Download the packaged frontend UI, https://github.com/shibing624/SearchGPT/releases/download/0.1.0/ui.zip and unzip it to the project root directory for direct use.
2. Build the frontend yourself using npm (requires nodejs version 18 or above)
```shell
cd web && npm install && npm run build
```
Output: The project root directory will produce a `ui` folder containing the frontend static files.

## Use Search Engine API
Using Serper's Google search:

```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
BACKEND=SERPER python search.py
```

## Use OpenAI LLM
If you are looking for better LLM generation results, you can use OpenAI's LLM model `gpt-4`.

```shell
export SERPER_SEARCH_API_KEY=YOUR_SERPER_API_KEY
export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
export OPENAI_BASE_URL=https://xxx/v1
BACKEND=SERPER LLM_TYPE=OPENAI LLM_MODEL=gpt-4 python search.py
```

## Configuration

Deployment configuration, see [search.py](https://github.com/shibing624/SearchGPT/blob/main/search.py):

Set the following environment variables:

* `BACKEND`: The search backend to use. The default is to use ZhipuAI's free search tool `SEARCHPRO`. Otherwise, set it to `SERPER` and provide the corresponding API_KEY, or use the open-source search engine `DDGS`.
* `LLM_TYPE`: The type of LLM to use. The default is set to `ZHIPUAI`. Otherwise, set it to `OPENAI` and provide the corresponding LLM API key.
* `LLM_MODEL`: The LLM model to run. We recommend using the free `glm-4-flash`, or other models that match the above `LLM_TYPE`.
* `RELATED_QUESTIONS`: Whether to generate related questions. If set to `true`, the search engine will generate related questions for you. Otherwise, it will not.
* `ENABLE_HISTORY`: Whether to enable history. If you set this to `true`, the LLM will store search history. Otherwise, it will not.

Additionally, you can set the following keys:

* `ZHIPUAI_API_KEY`: If using ZhipuAI, specify the API key
* `OPENAI_API_KEY`: If using OpenAI, specify the API key
* `SERPER_SEARCH_API_KEY`: If using Serper's Google, specify the search API key

## Contact
- Issue (suggestions): [![GitHub issues](https://img.shields.io/github/issues/shibing624/SearchGPT.svg)](https://github.com/shibing624/SearchGPT/issues)
- Email me: xuming: xuming624@qq.com
- WeChat me: Add my *WeChat ID: xuming624, note: Name-Company-NLP* to join the NLP group.

<img src="docs/wechat.jpeg" width="200" />

## License
The license is [The Apache License 2.0](LICENSE), free for commercial use. Please include a link to SearchGPT and the license in your product description.


## Contribute
The project code is still rough, if you have any improvements to the code, feel free to submit them back to this project.

## Reference
- [leptonai/search_with_lepton](https://github.com/leptonai/search_with_lepton/tree/main)
